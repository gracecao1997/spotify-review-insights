"""Explicit paid six-stage pipeline; no model calls on import or offline replay."""
import argparse
import fcntl
import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace
from core import ROOT,write_json,model_identity
from jev_run import execute
from jev_tasks import verify_one
from stages import run_stages,load_records


def run(args):
    base=Path(args.root);db=base/'state.sqlite';phase='warm' if args.warm else ('resume' if args.resume else 'cold')
    if args.pilot:
        args.input=ROOT/'data/cost_100.csv'
        if db.exists() and not args.warm and not args.resume:raise ValueError('Cold pilot requires an empty result cache; choose a new root.')
        if args.warm and not (base/'cold/experiment.json').exists():raise ValueError('Warm experiment requires a complete cold pilot.')
    base.mkdir(parents=True,exist_ok=True);out=base/phase;start=time.perf_counter()
    # Verify the bounded local writer is available before dispatching paid requests.
    info=model_identity(args.model)
    text_settings={'model':args.model,'digest':info['digest'],'temperature':0,'num_ctx':8192,'num_predict':2200}
    summary=execute(SimpleNamespace(input=args.input,db=db,out=out,limit=None,workers=1 if args.pilot else args.workers,
                    max_seconds=args.max_seconds,retry_transport_quarantine=getattr(args,'retry_transport_quarantine',False),phase='resume' if args.warm or args.resume else 'initial'))
    if summary['pending'] or summary['interrupted'] or summary['stop_reasons']:
        raise RuntimeError('Classification paused/incomplete; checkpoint saved. Resolve the stop reason before resuming.')
    records=load_records(out/'records.jsonl')
    if any(r['status']!='completed' and r.get('reason')!='empty_review_text' for r in records):
        raise RuntimeError('Nonempty quarantines remain; resolve them before scaling.')
    stages_dir=base/'stages'
    fraction=.1 if args.pilot else .01
    note='Professor-approved scope reported by the student: 100,000 nonempty reviews plus 13 empty records.' if len(records)==100013 else 'Development checkpoint; not the final analysis.'
    stages=run_stages(out/'records.jsonl',stages_dir,text_settings,verify_fraction=fraction,
                      verifier=lambda folder,r:verify_one(folder,r,phase),scope_note=note)
    for name in ['stage_summary.json','verification.json','ranking.csv','membership.csv','claims.csv','memo.md','memo.json','memo_evidence.json','issue_names.json']:
        source=stages_dir/name
        if source.exists():shutil.copy2(source,out/name)
    calls=load_records(out/'calls.jsonl')
    if (stages_dir/'stage_calls.jsonl').exists():calls+=load_records(stages_dir/'stage_calls.jsonl')
    (out/'all_calls.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in calls))
    report={'phase':phase,'wall_seconds':time.perf_counter()-start,'stages':stages,'workers':1 if args.pilot else args.workers,
            'verification_fraction':fraction,'verification_minimum':10,'fallback_fraction':0,'complete_pipeline':True,
            'input':str(args.input),'classification':summary,'text_model':text_settings}
    write_json(out/'experiment.json',report);print('Saved '+str(out/'experiment.json'),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-paid',action='store_true',required=True)
    p.add_argument('--input',type=Path);p.add_argument('--root',required=True);p.add_argument('--pilot',action='store_true')
    p.add_argument('--warm',action='store_true');p.add_argument('--resume',action='store_true')
    p.add_argument('--retry-transport-quarantine',action='store_true');p.add_argument('--workers',type=int,choices=[1,2],default=1);p.add_argument('--max-seconds',type=float,default=0)
    p.add_argument('--model',default='gemma3n:e4b-it-q4_K_M');args=p.parse_args()
    if not args.pilot and not args.input:p.error('--input is required outside the fixed pilot')
    lock=ROOT/'runs/jev-run.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another paid run is active')
        run(args)
