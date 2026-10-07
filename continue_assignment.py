"""Finite recovery, audit and publication for the approved final analysis."""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from core import ROOT,write_json
from stages import load_records


def main(args):
    base=ROOT/'runs/jev-500';status=ROOT/'evidence/execution_status.json'
    def state(stage,**extra):write_json(status,{'stage':stage,'updated_unix':time.time(),**extra})
    for attempt in range(args.recovery_rounds+1):
        output=base/'resume';summary_path=output/'summary.json'
        prior=json.loads(summary_path.read_text()) if summary_path.exists() else {}
        if output.exists():
            snapshot=base/f'interrupted-final-{time.time_ns()}'
            shutil.copytree(output,snapshot)
        state('classifying_100000',recovery_round=attempt,max_recovery_rounds=args.recovery_rounds)
        result=subprocess.run([sys.executable,'-u','jev_pipeline.py','--execute-paid','--resume','--retry-transport-quarantine',
            '--input','data/analysis_100000.csv','--root','runs/jev-500','--workers','2','--model','qwen3:4b'],cwd=ROOT)
        if result.returncode==0:break
        summary=json.loads(summary_path.read_text()) if summary_path.exists() else {}
        if summary.get('run_id')==prior.get('run_id'):raise RuntimeError('No new checkpoint; inspect setup or local model failure.')
        calls=[c for c in load_records(output/'calls.jsonl') if c.get('run_id')==summary.get('run_id') and c.get('outcome')=='failed']
        network_only=bool(calls) and all(any(x in c.get('error','') for x in ['network error','HTTP 5']) for c in calls)
        circuit=any('Three consecutive failed attempts' in s for s in summary.get('stop_reasons',[]))
        if not(network_only and circuit) or attempt==args.recovery_rounds:
            raise RuntimeError('Final run stopped; no further automatic recovery is allowed for this failure.')
        state('network_backoff',recovery_round=attempt+1,saved_completed=summary.get('completed'),seconds=45)
        time.sleep(45)
    else:raise RuntimeError('Recovery limit reached')
    subprocess.run([sys.executable,'finish_assignment.py','--finalize-only'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,'publish_when_ready.py'],cwd=ROOT,check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-paid',action='store_true',required=True)
    p.add_argument('--recovery-rounds',type=int,choices=[0,1,2],default=2);a=p.parse_args()
    try:main(a)
    except BaseException as e:
        write_json(ROOT/'evidence/execution_status.json',{'stage':'stopped','error':str(e),'updated_unix':time.time()});raise
