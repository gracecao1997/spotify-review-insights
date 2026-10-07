"""Cached blind verification with real per-attempt evidence and a shared spend ledger."""
import json
import os
import time
import uuid
from pathlib import Path
from budget import BudgetExceeded
from core import ROOT,canonical,digest,write_json
from jev_client import JevClient,decode,settings_for


def verify_one(out,review,phase='initial'):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    settings=settings_for('verify');text=review['source']['review_text']
    key=digest(canonical({'settings':settings,'review_id':review['review_id'],'text':text}))
    cache=out/'task-cache'/f'jev-{key}.json'
    if cache.exists():
        saved=json.loads(cache.read_text());label,_=decode(saved,text)
        return label,{'cache_hit':True,'attempts':0,'wall_seconds':0}
    client=JevClient(ROOT/'runs/project_budget.sqlite');start=time.perf_counter();last=None
    for attempt in range(2):
        cid=str(uuid.uuid4());t=time.perf_counter()
        call={'request_id':cid,'role':'verify','model':settings['model'],'phase':phase,'label_config':key,
              'review_ids':[review['review_id']],'attempt':attempt+1,'outcome':'unknown','api_cost_usd':None}
        # Preserve unknown in-flight requests even if the process is killed.
        pending=out/'in-flight'/f'{cid}.json';write_json(pending,call)
        fatal=False
        try:
            response,meta=client.call(text,cid,'verify');call.update(meta);call['raw_response']=response
            label,_=decode(response,text)
            if meta['input_tokens'] is None:raise RuntimeError('Provider usage missing; stop for reconciliation')
            call['outcome']='succeeded';last=None
        except Exception as e:
            last=str(e);call.update(outcome='failed',error=last)
            fatal=isinstance(e,BudgetExceeded) or any(x in last for x in ['HTTP 401','HTTP 402','HTTP 403','HTTP 422','usage missing'])
            if isinstance(e,BudgetExceeded):call.update(request_sent=False,api_cost_usd=0)
        call['wall_seconds']=time.perf_counter()-t
        with (out/'stage_calls.jsonl').open('a') as f:
            f.write(canonical(call)+'\n');f.flush();os.fsync(f.fileno())
        pending.unlink()
        if last is None:
            write_json(cache,response)
            return label,{'cache_hit':False,'attempts':attempt+1,'wall_seconds':time.perf_counter()-start}
        if fatal:break
        if attempt==0:time.sleep(1)
    raise RuntimeError('Independent verification failed: '+str(last))
