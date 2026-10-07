"""Run all six stages from one CSV path; execution must be explicitly requested."""
import argparse
import json
import time
from pathlib import Path
from types import SimpleNamespace
from core import write_json
from run import classify
from stages import run_stages,load_records

def main(a):
    start=time.perf_counter();out=Path(a.out)
    classify(SimpleNamespace(db=a.db,input=a.input,limit=None,model=a.model,batch_size=a.batch_size,
        out=out,max_seconds=a.max_seconds,phase=a.phase,retry_quarantine=False))
    summary=json.loads((out/'summary.json').read_text())
    if summary['pending'] or summary['interrupted']:
        raise SystemExit('Run paused/incomplete. Saved progress is resumable; no final business conclusion generated.')
    settings=json.loads((out/'settings.json').read_text())
    stages=run_stages(out/'records.jsonl',out/'stages',settings,a.verify_fraction)
    records=load_records(out/'records.jsonl')
    nonempty_complete=all(r['status']=='completed' or (r['status']=='quarantined' and r.get('reason')=='empty_review_text') for r in records)
    write_json(out/'pipeline_summary.json',{'wall_seconds':time.perf_counter()-start,'classification':summary,'stages':stages,
                                          'scope_complete':nonempty_complete,'api_cost_usd':0,'local_compute_cost_usd':None})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-local',action='store_true',required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--db',default='runs/pipeline.sqlite');p.add_argument('--out',default='runs/pipeline')
    p.add_argument('--model',default='gemma3n:e4b-it-q4_K_M');p.add_argument('--batch-size',type=int,default=10)
    p.add_argument('--phase',choices=['initial','resume'],default='initial');p.add_argument('--max-seconds',type=float,default=0)
    p.add_argument('--verify-fraction',type=float,default=.1);a=p.parse_args()
    if not 1<=a.batch_size<=25 or not 0<a.verify_fraction<=1 or a.max_seconds<0:p.error('Invalid batch, verification fraction or time limit')
    main(a)
