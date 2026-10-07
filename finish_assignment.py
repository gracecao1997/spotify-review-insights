"""Finish the approved analysis after the 10k checkpoint; stop visibly on any failure."""
import argparse
import json
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from core import ROOT,write_json
from budget import Ledger
from stages import load_records


def command(*parts):
    subprocess.run([str(p) for p in parts],cwd=ROOT,check=True)


def main(args):
    base=ROOT/'runs/jev-500';status=ROOT/'evidence/execution_status.json'
    def state(stage,**values):write_json(status,{'stage':stage,'updated_unix':time.time(),**values})
    py=sys.executable
    if not getattr(args,'finalize_only',False):
        # This is one finite local job waiting for its running prerequisite, not a scheduler.
        state('waiting_for_10000_checkpoint')
        deadline=time.monotonic()+3600
        while True:
            p=base/'resume/experiment.json'
            if p.exists():
                e=json.loads(p.read_text())
                if e['classification']['input_count']==10000 and e['complete_pipeline']:break
            if time.monotonic()>deadline:raise RuntimeError('10k prerequisite did not finish within one hour; inspect its saved logs.')
            time.sleep(10)
        dest=base/'checkpoint10000'
        if not dest.exists():shutil.copytree(base/'resume',dest)
        records=load_records(dest/'records.jsonl');calls=load_records(dest/'all_calls.jsonl')
        unique=len({r['source']['review_text'] for r in records if r['status']=='completed'})
        cost=sum(c.get('api_cost_usd') or 0 for c in calls if c['role']=='enrich')
        ledger=Ledger(ROOT/'runs/project_budget.sqlite').summary()
        projected=cost/unique*78099*1.2 + .15 + ledger['reserved_or_unknown_usd']
        write_json(ROOT/'cost/jev/checkpoint10000_projection.json',{'measured_unique_texts':unique,'measured_enrich_known_usd':cost,
                   'projected_final_api_usd_with_20_percent_margin':projected,'project_budget':ledger,
                   'formula':'known enrichment cost / checkpoint distinct texts * 78099 * 1.2 + 0.15 verification allowance + unresolved reservations'})
        if projected>=8.5:raise RuntimeError('10k measured projection leaves insufficient room under budget; stopped before final expansion.')
        state('classifying_100000',projection_usd=projected)
        py=sys.executable
        command(py,'jev_pipeline.py','--execute-paid','--resume','--input','data/analysis_100000.csv','--root','runs/jev-500','--workers','2')
    else:
        experiment=json.loads((base/'resume/experiment.json').read_text())
        assert experiment['complete_pipeline'] and experiment['classification']['input_count']==100013
    state('auditing_final_outputs')
    command(py,'evaluate.py','--predictions','runs/jev-500/resume/records.jsonl')
    command(py,'export_grading.py','--source','runs/jev-500/resume','--stages','runs/jev-500/stages','--input','data/analysis_100000.csv','--out','grading','--checkpoints','runs/jev-500')
    command(py,'course/check_submission.py','reference','--full','data/spotify_reviews_18months.csv','--analysis','data/analysis_100000.csv','--out','runs/reference-final.json')
    command(py,'course/check_submission.py','check','--reference','runs/reference-final.json','--submission','grading','--out','evidence/final-self-check.json')
    audit=json.loads((ROOT/'evidence/final-self-check.json').read_text())
    from audit_acceptance import assess
    acceptance=assess(ROOT/'evidence/final-self-check.json',ROOT/'grading',ROOT/'evidence/audit-disclosure.json')
    command(py,'dashboard.py','--import-run','runs/jev-500/resume','--db','deployment/dashboard.sqlite')
    summary=json.loads((base/'resume/summary.json').read_text())
    final_budget=Ledger(ROOT/'runs/project_budget.sqlite').summary()
    report={'scope':'100000 nonempty plus 13 empty; original full source profiled separately','classification':summary,
            'project_budget':final_budget,'audit_status':audit['status'],'audit_accepted':acceptance['accepted_for_publication'],'dashboard_url':'https://spotify-review-insights-three.vercel.app'}
    write_json(ROOT/'evidence/final_run.json',report)
    release=ROOT/'release';release.mkdir(exist_ok=True)
    archive=release/'spotify-assignment-evidence.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for folder in ['grading','cost/jev']:
            for f in (ROOT/folder).rglob('*'):
                if f.is_file():z.write(f,f.relative_to(ROOT))
        for f in ['data/analysis_100000.csv','runs/jev-500/recovery.cast','runs/jev-500/recovery_report.json','runs/jev-500/resume/memo.md','runs/jev-500/resume/memo.json','runs/jev-500/resume/verification.json','evidence/final_run.json','evidence/final-self-check.json']:
            z.write(ROOT/f,f)
    # The analysis can finish without granting this process publishing authority.
    state('analysis_complete',report=report,archive=str(archive),publication_pending=True)
    print('Analysis and audit complete. Final database and evidence archive are ready for publication.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-paid',action='store_true',required=False);p.add_argument('--finalize-only',action='store_true');args=p.parse_args()
    if not args.execute_paid and not args.finalize_only:p.error('--execute-paid is required for model execution')
    try:main(args)
    except BaseException as e:
        write_json(ROOT/'evidence/execution_status.json',{'stage':'stopped','error':str(e),'updated_unix':time.time()})
        raise
