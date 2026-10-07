"""Explicit paid Jev classification within the shared user-authorized $10 budget."""
import argparse
import concurrent.futures as futures
import fcntl
import json
import random
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path
from budget import BudgetExceeded
from core import ROOT,canonical,connect,digest,ingest,read_csv,row_sha,validate,write_json
from jev_client import JevClient,MODEL,decode,load_key,settings_for

def execute(args):
    load_key()  # Fail before ingestion/dispatch when setup is missing. Never print it.
    started=time.perf_counter();run_id=str(uuid.uuid4());out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    settings=settings_for();config=digest(canonical(settings));write_json(out/'settings.json',{'config':config,**settings})
    records=list(read_csv(args.input));records=records[:args.limit] if args.limit else records
    ids={r['review_id'] for r in records}
    if len(ids)!=len(records):raise ValueError('Duplicate review IDs')
    with closing(connect(args.db)) as db:ingest(db,args.input)
    client=JevClient(ROOT/'runs/project_budget.sqlite')
    stop=threading.Event();lock=threading.Lock();next_dispatch=[0.0];failure_streak=[0];stop_reasons=[]
    def halt(reason):
        with lock:stop_reasons.append(reason)
        stop.set()
    with closing(connect(args.db)) as db:
        before={r['id'] for r in db.execute("SELECT id FROM results WHERE config=? AND status='completed'",(config,)) if r['id'] in ids}
    write_json(out/'checkpoint_before.json',{'completed_ids':sorted(before)})
    groups={};hits=0
    with closing(connect(args.db)) as db,db:
        for r in records:
            old=db.execute('SELECT status FROM results WHERE id=? AND config=?',(r['review_id'],config)).fetchone()
            if old:hits+=1;continue
            if not r['review_text'].strip():
                db.execute('INSERT INTO results VALUES(?,?,?,?)',(r['review_id'],config,'quarantined',canonical({'reason':'empty_review_text'})))
                continue
            h=digest(r['review_text']);cached=db.execute('SELECT * FROM cache WHERE text_hash=? AND config=?',(h,config)).fetchone()
            if cached and cached['source_id'] in ids:
                p=json.loads(cached['payload']);validate(p,r['review_text']);p['cache_source_id']=cached['source_id']
                db.execute('INSERT INTO results VALUES(?,?,?,?)',(r['review_id'],config,'completed',canonical(p)));hits+=1;continue
            groups.setdefault(h,[]).append(r)
    queue=iter(groups.items());new_calls=[0];done_count=[0]
    def work(item):
        h,rows=item;r=rows[0]
        if stop.is_set():return
        for attempt in range(2):
            if stop.is_set():return
            with lock:
                now=time.monotonic();delay=max(0,next_dispatch[0]-now)
                # Conservative UTF-8 byte allowance plus overhead; shared across workers.
                allowance=len(canonical({'state':{'review_text':r['review_text']},'questions':settings['questions']}).encode())+1024
                next_dispatch[0]=max(now,next_dispatch[0])+max(.05,allowance/60000)
            if stop.wait(delay):return
            cid=str(uuid.uuid4());t=time.perf_counter();call={'request_id':cid,'run_id':run_id,'role':'enrich','review_ids':[r['review_id']],
                'model':MODEL,'phase':args.phase,'label_config':config,'attempt':attempt+1,'outcome':'unknown',
                'api_cost_usd':None,'input_tokens':None,'output_tokens':None,'request_sent':None}
            with closing(connect(args.db)) as db,db:db.execute('INSERT INTO calls VALUES(?,?,?,?)',(cid,'enrich',config,canonical(call)))
            result=None;fatal=False
            try:
                response,meta=client.call(r['review_text'],cid);call.update(meta);call['raw_response']=response;call['request_sent']=True
                result,confidences=decode(response,r['review_text']);call['confidences']=confidences;call['outcome']='succeeded'
                if meta['input_tokens'] is None:halt('Provider usage missing; inspect retained reservation before more spending')
            except BudgetExceeded as e:
                call.update({'outcome':'failed','error':str(e),'request_sent':False,'api_cost_usd':0});halt(str(e));fatal=True
            except Exception as e:
                error=str(e);call.update({'outcome':'failed','error':error})
                if any(x in error for x in ['HTTP 401','HTTP 403','HTTP 402','HTTP 422']):
                    halt('Account/configuration error: '+error);fatal=True
            call['wall_seconds']=time.perf_counter()-t
            with closing(connect(args.db)) as db,db:
                db.execute('UPDATE calls SET payload=? WHERE request_id=?',(canonical(call),cid))
                if result is not None:
                    for i,source in enumerate(rows):
                        payload={**result,**({'cache_source_id':r['review_id']} if i else {})}
                        db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(source['review_id'],config,'completed',canonical(payload)))
                    db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)',(h,config,r['review_id'],canonical(result)))
                elif attempt==1 and not fatal:
                    for source in rows:
                        db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(source['review_id'],config,'quarantined',canonical({'reason':call.get('error','invalid_output'),'attempts':2})))
            with lock:
                new_calls[0]+=int(call.get('request_sent') is not False)
                if result is not None:failure_streak[0]=0;done_count[0]+=len(rows)
                else:failure_streak[0]+=1
                failures=failure_streak[0]
            if result is not None:
                if done_count[0]%25==0 or args.limit:print(canonical({'new_completed':done_count[0],'budget':client.ledger.summary()}),flush=True)
                return
            if failures>=3:halt('Three consecutive failed attempts; saved work retained for diagnosis')
            if attempt==0 and not stop.is_set():stop.wait(1+random.random())
    pool=futures.ThreadPoolExecutor(max_workers=args.workers);active=set();exhausted=False;interrupted=False
    try:
        while active or not exhausted:
            if args.max_seconds and time.perf_counter()-started>=args.max_seconds:halt('Time limit reached')
            while not stop.is_set() and not exhausted and len(active)<args.workers:
                try:item=next(queue)
                except StopIteration:exhausted=True;break
                active.add(pool.submit(work,item))
            if not active:break
            completed,active=futures.wait(active,timeout=.5,return_when=futures.FIRST_COMPLETED)
            for task in completed:task.result()
    except Exception as e:
        halt('Internal runner error: '+str(e))
    except KeyboardInterrupt:
        interrupted=True;halt('User interrupt; in-flight work will finish and save before exit')
    finally:
        stop.set();pool.shutdown(wait=True,cancel_futures=True)
    final=[]
    with closing(connect(args.db)) as db:
        for r in records:
            saved=db.execute('SELECT status,payload FROM results WHERE id=? AND config=?',(r['review_id'],config)).fetchone()
            final.append({'review_id':r['review_id'],'source_sha256':row_sha(r),'source':r,'label_config':config,
                          'status':saved['status'] if saved else 'pending',**(json.loads(saved['payload']) if saved else {})})
        calls=[json.loads(x['payload']) for x in db.execute('SELECT payload FROM calls WHERE config=?',(config,))]
        calls=[c for c in calls if set(c['review_ids']) <= ids]
    (out/'records.jsonl').write_text(''.join(canonical(r)+'\n' for r in final))
    (out/'calls.jsonl').write_text(''.join(canonical(c)+'\n' for c in calls))
    after=[r['review_id'] for r in final if r['status']=='completed']
    write_json(out/'checkpoint_after.json',{'completed_ids':after})
    summary={'run_id':run_id,'label_config':config,'input_count':len(final),'completed':len(after),
             'quarantined':sum(r['status']=='quarantined' for r in final),'pending':sum(r['status']=='pending' for r in final),
             'new_enrichment_calls':new_calls[0],'cache_or_saved_hits':hits,'workers':args.workers,
             'wall_seconds':time.perf_counter()-started,'interrupted':interrupted,'stop_reasons':stop_reasons,'project_budget':client.ledger.summary()}
    write_json(out/'summary.json',summary);print(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-paid',action='store_true',required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--db',default='runs/jev/state.sqlite');p.add_argument('--out',default='runs/jev/output')
    p.add_argument('--workers',type=int,default=1);p.add_argument('--limit',type=int);p.add_argument('--max-seconds',type=float,default=0)
    p.add_argument('--phase',choices=['initial','resume'],default='initial');args=p.parse_args()
    if not 1<=args.workers<=2:p.error('Start with one worker; at most two until a measured capacity check supports more')
    lock_path=ROOT/'runs/jev-run.lock';lock_path.parent.mkdir(parents=True,exist_ok=True)
    with lock_path.open('a') as run_lock:
        try:fcntl.flock(run_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Another Jev run is active; wait or resume it instead of duplicating work')
        execute(args)
