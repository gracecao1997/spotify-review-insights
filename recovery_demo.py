"""Record an actual SIGINT and resume, with saved-ID and call-log checks."""
import argparse
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from core import ROOT,write_json

def main(args):
    root=Path(args.out);root.mkdir(parents=True,exist_ok=True);db=root/'state.sqlite'
    if db.exists():raise SystemExit('Choose a fresh demo folder; evidence is never overwritten.')
    if args.seed_db:
        source=sqlite3.connect(args.seed_db);dest=sqlite3.connect(db);source.backup(dest);dest.close();source.close()
    cast=root/'recovery.cast';f=cast.open('w');start=time.monotonic()
    f.write(json.dumps({'version':2,'width':120,'height':30,'timestamp':int(time.time()),'title':'Actual pipeline interruption and resume'})+'\n')
    def emit(s):
        f.write(json.dumps([round(time.monotonic()-start,3),'o',s.replace('\n','\r\n')])+'\n');f.flush();print(s,end='',flush=True)
    def execute(phase,interrupt):
        cmd=[sys.executable,'-u',str(ROOT/'run.py'),'--input',args.input,'--db',str(db),'--out',str(root/phase),'--model',args.model,'--batch-size','10','--phase','initial' if phase=='before' else 'resume']
        if args.provider=='jev':
            cmd=[sys.executable,'-u',str(ROOT/'jev_run.py'),'--execute-paid','--input',args.input,'--db',str(db),'--out',str(root/phase),'--workers','1','--phase','initial' if phase=='before' else 'resume']
        emit('$ '+' '.join(cmd)+'\n');proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,cwd=ROOT)
        signalled=False
        for line in proc.stdout:
            emit(line)
            if interrupt and not signalled:
                try:event=json.loads(line)
                except ValueError:continue
                if event.get('valid',0)>0 or event.get('new_completed',0)>0:
                    proc.send_signal(signal.SIGINT);signalled=True;emit('[controller sent SIGINT after a committed batch]\n')
        code=proc.wait()
        if code:raise RuntimeError(f'Process exited {code}; inspect recorded output')
        if interrupt and not signalled:raise RuntimeError('No new work; interruption was not demonstrated')
    execute('before',True)
    before=json.loads((root/'before/checkpoint_after.json').read_text())['completed_ids']
    write_json(root/'checkpoint_before.json',{'completed_ids':before})
    execute('after',False)
    after=json.loads((root/'after/checkpoint_after.json').read_text())['completed_ids']
    write_json(root/'checkpoint_after.json',{'completed_ids':after})
    calls=[json.loads(line) for line in (root/'after/calls.jsonl').read_text().splitlines()]
    relabelled=sorted({rid for c in calls if c['phase']=='resume' for rid in c['review_ids']} & set(before))
    report={'before_count':len(before),'after_count':len(after),'saved_ids_retained':set(before)<=set(after),
            'additional_completed':len(set(after)-set(before)),'already_completed_ids_relabelled':relabelled,
            'passed':set(before)<set(after) and not relabelled,'recording':str(cast)}
    write_json(root/'recovery_report.json',report);emit(json.dumps(report,indent=2)+'\n');f.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--provider',choices=['local','jev'],default='local');p.add_argument('--execute-paid',action='store_true');p.add_argument('--input',default='data/checkpoint_500.csv');p.add_argument('--model',default='qwen3:4b');p.add_argument('--seed-db');p.add_argument('--out',default='runs/checkpoint-recovery');a=p.parse_args()
    if a.provider=='jev' and not a.execute_paid:p.error('Jev recovery requires --execute-paid')
    main(a)
