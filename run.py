"""Explicit local execution only. Saves each call and validated batch transactionally."""
import argparse
import json
import time
import uuid
from pathlib import Path
from core import *

def classify(args):
    started=time.perf_counter(); run_id=str(uuid.uuid4())
    db=connect(args.db); ingest(db,args.input)
    rows=list(read_csv(args.input))
    if len({r['review_id'] for r in rows})!=len(rows):raise ValueError('Input contains duplicate review IDs')
    if args.limit: rows=rows[:args.limit]
    identity=model_identity(args.model); config,settings=configuration(args.model,identity,args.batch_size)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    write_json(out/'settings.json',{'config':config,**settings,'model_metadata':identity})
    before=[x['id'] for x in db.execute("SELECT id FROM results WHERE config=? AND status='completed'",(config,))]
    write_json(out/'checkpoint_before.json',{'completed_ids':before})
    queue=[]; hits=0; new_calls=0; max_elapsed=args.max_seconds
    for r in rows:
        rid=r['review_id']; old=db.execute('SELECT status FROM results WHERE id=? AND config=?',(rid,config)).fetchone()
        if old and (old['status']=='completed' or not args.retry_quarantine): hits+=1; continue
        if not r['review_text'].strip():
            with db: db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(rid,config,'quarantined',canonical({'reason':'empty_review_text'})))
        else: queue.append(r)
    interrupted=False
    try:
        pos=0
        while pos<len(queue):
            if max_elapsed and time.perf_counter()-started>=max_elapsed: break
            batch=[]; chars=0; seen_text=set()
            while pos<len(queue) and len(batch)<args.batch_size:
                r=queue[pos]; text_hash=digest(r['review_text'])
                cached=db.execute('SELECT * FROM cache WHERE text_hash=? AND config=?',(text_hash,config)).fetchone()
                if cached:
                    result=json.loads(cached['payload']); validate(result,r['review_text'])
                    result['cache_source_id']=cached['source_id']
                    with db: db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(r['review_id'],config,'completed',canonical(result)))
                    hits+=1; pos+=1; continue
                if text_hash in seen_text: break
                if batch and chars+len(r['review_text'])>10000: break
                if len(r['review_text'])>20000:
                    with db: db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(r['review_id'],config,'quarantined',canonical({'reason':'text_exceeds_context_budget'})))
                    pos+=1; continue
                batch.append(r); seen_text.add(text_hash); chars+=len(r['review_text']); pos+=1
            if not batch: continue
            pending=batch
            for attempt in range(2):
                if not pending: break
                call_id=str(uuid.uuid4()); call_start=time.perf_counter()
                user=canonical([{'index':i,'text':r['review_text']} for i,r in enumerate(pending)])
                call={'request_id':call_id,'run_id':run_id,'role':'enrich','review_ids':[r['review_id'] for r in pending],
                      'model':args.model,'phase':args.phase,'label_config':config,'attempt':attempt+1,
                      'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'outcome':'unknown',
                      'api_cost_usd':0,'local_compute_cost_usd':None,'input':user}
                with db: db.execute('INSERT INTO calls VALUES(?,?,?,?)',(call_id,'enrich',config,canonical(call)))
                errors={}; valid={}
                try:
                    response,seconds,request=model_call(args.model,PROMPT,user,SCHEMA,{k:settings[k] for k in ('temperature','num_ctx','num_predict')})
                    call.update({'raw_response':response,'wall_seconds':seconds,'input_tokens':response.get('prompt_eval_count'),
                                 'output_tokens':response.get('eval_count'),'request':request})
                    if response.get('done_reason')=='length': raise ValueError('output_token_limit')
                    parsed=json.loads(response['message']['content']); items=parsed['items']
                    if not isinstance(items,list): raise ValueError('items must be a list')
                    indices=[x.get('index') for x in items if isinstance(x,dict)]
                    if len(indices)!=len(items) or any(type(i) is not int for i in indices) or len(set(indices))!=len(indices) or any(i<0 or i>=len(pending) for i in indices):
                        raise ValueError('duplicate or unexpected indices')
                    by_index={x['index']:x for x in items}
                    for i,r in enumerate(pending):
                        try: valid[i]=validate(enrich_deterministically(by_index.get(i,{}),r['review_text']),r['review_text'])
                        except ValueError as e: errors[i]=str(e)
                    call['outcome']='succeeded'
                except KeyboardInterrupt:
                    call.update({'outcome':'failed','error':'interrupted; local inference usage unknown',
                                 'wall_seconds':time.perf_counter()-call_start,'input_tokens':None,'output_tokens':None})
                    with db:db.execute('UPDATE calls SET payload=? WHERE request_id=?',(canonical(call),call_id))
                    raise
                except Exception as e:
                    errors={i:str(e) for i in range(len(pending))}; call['outcome']='failed'; call['error']=str(e)
                call['wall_seconds']=time.perf_counter()-call_start; call['validation_errors']=errors
                with db:
                    db.execute('UPDATE calls SET payload=? WHERE request_id=?',(canonical(call),call_id))
                    for i,result in valid.items():
                        r=pending[i]
                        db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(r['review_id'],config,'completed',canonical(result)))
                        db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?,?)',(digest(r['review_text']),config,r['review_id'],canonical(result)))
                    if attempt==1:
                        for i,reason in errors.items():
                            db.execute('INSERT OR REPLACE INTO results VALUES(?,?,?,?)',(pending[i]['review_id'],config,'quarantined',canonical({'reason':reason,'attempts':2})))
                new_calls+=1
                print(json.dumps({'run_id':run_id,'batch':len(pending),'valid':len(valid),'invalid':len(errors),'seconds':round(call['wall_seconds'],2)}),flush=True)
                pending=[r for i,r in enumerate(pending) if i in errors]
    except KeyboardInterrupt:
        interrupted=True; print('Interrupted; committed results are safe.',flush=True)
    records=[]
    for r in rows:
        saved=db.execute('SELECT * FROM results WHERE id=? AND config=?',(r['review_id'],config)).fetchone()
        records.append({'review_id':r['review_id'],'source_sha256':row_sha(r),'source':r,
                        'status':saved['status'] if saved else 'pending','label_config':config,
                        **(json.loads(saved['payload']) if saved else {})})
    (out/'records.jsonl').write_text(''.join(canonical(r)+'\n' for r in records))
    calls=[json.loads(c['payload']) for c in db.execute('SELECT payload FROM calls WHERE config=?',(config,))]
    (out/'calls.jsonl').write_text(''.join(canonical(c)+'\n' for c in calls))
    completed=sum(r['status']=='completed' for r in records)
    elapsed=time.perf_counter()-started
    report={'run_id':run_id,'label_config':config,'input':str(args.input),'input_count':len(rows),
            'completed':completed,'quarantined':sum(r['status']=='quarantined' for r in records),
            'pending':sum(r['status']=='pending' for r in records),'cache_or_saved_hits':hits,
            'new_enrichment_calls':new_calls,'wall_seconds':elapsed,'api_cost_usd':0,
            'local_compute_cost_usd':None,'interrupted':interrupted,
            'note':'Classification benchmark only; this is NOT yet the required all-stage cost pilot.'}
    write_json(out/'summary.json',report)
    write_json(out/'checkpoint_after.json',{'completed_ids':[r['review_id'] for r in records if r['status']=='completed']})
    print(json.dumps(report,indent=2),flush=True)
    db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True); p.add_argument('--db',default='runs/state.sqlite')
    p.add_argument('--model',default='gemma3n:e4b-it-q4_K_M'); p.add_argument('--batch-size',type=int,default=5)
    p.add_argument('--limit',type=int); p.add_argument('--out',default='runs/benchmark')
    p.add_argument('--max-seconds',type=float,default=0); p.add_argument('--phase',choices=['initial','resume'],default='initial')
    p.add_argument('--retry-quarantine',action='store_true'); a=p.parse_args()
    if not 1<=a.batch_size<=25: p.error('Use 1–25 reviews per request (course maximum is 50)')
    classify(a)
