"""Explicit free local pilot. Offline replay lives in calculator.py and never invokes this."""
import argparse
import json
import shutil
import time
from pathlib import Path
from types import SimpleNamespace
from core import ROOT,write_json
from run import classify
from stages import run_stages

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute-local',action='store_true',required=True)
    p.add_argument('--warm',action='store_true');p.add_argument('--root',default='runs/pilot-v2')
    p.add_argument('--model',default='gemma3n:e4b-it-q4_K_M')
    a=p.parse_args();base=Path(a.root);db=base/'state.sqlite';phase='warm' if a.warm else 'cold'
    if db.exists() and not a.warm:raise SystemExit('Cold experiment requires an empty result cache. Choose a new --root; never erase evidence.')
    if a.warm and not db.exists():raise SystemExit('Warm replay needs a completed cold pilot first.')
    start=time.perf_counter();out=base/phase
    classify(SimpleNamespace(db=db,input=ROOT/'data/cost_100.csv',limit=None,model=a.model,
        batch_size=10,out=out,max_seconds=0,phase='resume' if a.warm else 'initial',retry_quarantine=False))
    classified=json.loads((out/'summary.json').read_text())
    if classified['pending'] or classified['quarantined'] or classified['interrupted']:
        raise SystemExit('Pilot incomplete; saved evidence retained. Resolve failures before completing the experiment.')
    settings=json.loads((out/'settings.json').read_text())
    stages=run_stages(out/'records.jsonl',base/'stages',settings)
    # Snapshot each experiment separately; the shared cache remains immutable by input/config hash.
    for name in ['stage_summary.json','verification.json','ranking.csv','membership.csv','claims.csv','memo.md','memo.json','memo_evidence.json','issue_names.json']:
        source=base/'stages'/name
        if source.exists():shutil.copy2(source,out/name)
    write_json(out/'experiment.json',{'phase':phase,'wall_seconds':time.perf_counter()-start,'stages':stages,
                 'api_cost_usd':0,'local_compute_cost_usd':None,'workers':1,'verification_fraction':.1,
                 'api_budget_usd':0,'fallback_fraction':0,'complete_pipeline':True})
    print('Saved '+str(out/'experiment.json'),flush=True)
