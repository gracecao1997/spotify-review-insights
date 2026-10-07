"""Offline by default: saved usage × editable rates; no model or network calls."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from core import ROOT,write_json

def load(path):return json.loads(Path(path).read_text())
def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()] if Path(path).exists() else []

def calculate(base,rates,project_rows=660622,unique_texts=484189,rate_multiplier=1):
    with open(rates,newline='') as f:rate_map={r['model']:r for r in csv.DictReader(f)}
    cold=load(base/'cold/experiment.json');warm=load(base/'warm/experiment.json') if (base/'warm/experiment.json').exists() else None
    cold_summary=load(base/'cold/summary.json');warm_summary=load(base/'warm/summary.json') if warm else None
    calls=lines(base/'cold/calls.jsonl')+lines(base/'stages/stage_calls.jsonl')
    seen=set();stage=defaultdict(lambda:{'attempts':0,'input_tokens':0,'output_tokens':0,'api_usd':0.0,'call_seconds':0.0,'unknown_usage_calls':0})
    usage=[]
    for c in calls:
        if c['request_id'] in seen:continue
        seen.add(c['request_id']);r=rate_map[c['model']];x=stage[c['role']];x['attempts']+=1
        inp=c.get('input_tokens');out=c.get('output_tokens');cached=c.get('cached_input_tokens',0)
        if inp is None or out is None:
            x['unknown_usage_calls']+=1;charge=None
        else:
            if not 0<=cached<=inp:raise ValueError('Invalid cached-input accounting')
            charge=((inp-cached)*float(r['input_per_million_usd'])+cached*float(r['cached_input_per_million_usd'])+out*float(r['output_per_million_usd']))/1e6*rate_multiplier
            x['api_usd']+=charge;x['input_tokens']+=inp;x['output_tokens']+=out
        x['call_seconds']+=c['wall_seconds']
        usage.append({'request_id':c['request_id'],'role':c['role'],'model':c['model'],'input_tokens':inp,'cached_input_tokens':cached,'output_tokens':out,'api_usd':charge,'wall_seconds':c['wall_seconds']})
    enrich=stage['enrich'];verify=stage['verify'];fixed=sum(x['api_usd'] for role,x in stage.items() if role not in ('enrich','verify'))
    n=cold_summary['input_count'];nonempty=project_rows-(13 if project_rows==660622 else 0)
    verify_rate=cold['verification_fraction'];pilot_verify=cold['stages']['timings'].get('verify',[])
    verify_n=load(base/'cold/verification.json')['sample_count']
    fixed_seconds=max(0,cold['wall_seconds']-enrich['call_seconds']-verify['call_seconds'])
    estimates={}
    for name,work,mult in [('base_exact_reuse',unique_texts,1),('conservative_exact_reuse',unique_texts,1.5),('no_reuse',nonempty,1)]:
        variable=enrich['api_usd']/n*work+verify['api_usd']/max(verify_n,1)*(nonempty*verify_rate)
        seconds=enrich['call_seconds']/n*work+verify['call_seconds']/max(verify_n,1)*(nonempty*verify_rate)
        estimates[name]={'first_pass_distinct_texts':work,'verification_reviews':round(nonempty*verify_rate),
           'api_usd':variable*mult+fixed,'hours':(seconds*mult+fixed_seconds)/3600,
           'assumption':'One worker; observed retries included; conservative variable work/time ×1.5; fallback disabled; fixed overhead once.'}
    return {'measured':{'cold_seconds':cold['wall_seconds'],'warm_seconds':warm['wall_seconds'] if warm else None,
             'input_count':n,'completed':cold_summary['completed'],'failed':cold_summary['quarantined'],
             'warm_new_enrichment_calls':warm_summary['new_enrichment_calls'] if warm_summary else None,
             'api_usd':sum(x['api_usd'] for x in stage.values()),'local_compute_usd':None,
             'cost_per_1000_inputs_usd':sum(x['api_usd'] for x in stage.values())/n*1000,
             'cost_per_completed_record_usd':sum(x['api_usd'] for x in stage.values())/cold_summary['completed'] if cold_summary['completed'] else None,
             'records_per_second':n/cold['wall_seconds'],'stage_breakdown':dict(stage)},
             'projected':{'rows':project_rows,'nonempty':nonempty,'unique_texts':unique_texts,'scenarios':estimates},
             'budget_api_usd':0,'would_exceed_api_budget':any(x['api_usd']>0 for x in estimates.values()),
             'usage':usage,'limitations':['Initial estimates from only 100 reviews; refresh at 500 and 10000.',
             'Local hardware/electricity cost unmeasured, not zero.','Summed call durations are used only for this single-worker setup.',
             'Unknown token usage stays unknown; actual local API charge is zero.','Model agreement is not human-label accuracy.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',type=Path,default=Path('runs/pilot-v2'))
    p.add_argument('--rates',type=Path,default=Path('cost/rates.csv'));p.add_argument('--rows',type=int,default=660622)
    p.add_argument('--unique-texts',type=int,default=484189);p.add_argument('--rate-multiplier',type=float,default=1)
    p.add_argument('--out',type=Path,default=Path('cost/report.json'));a=p.parse_args()
    if a.rows<=0 or not 0<a.unique_texts<=a.rows or a.rate_multiplier<0:p.error('Invalid projection inputs')
    report=calculate(a.pilot,a.rates,a.rows,a.unique_texts,a.rate_multiplier);write_json(a.out,report)
    usage=report.pop('usage');print(json.dumps(report,indent=2))
    with a.out.with_name('usage.csv').open('w',newline='') as f:
        if usage:
            w=csv.DictWriter(f,fieldnames=list(usage[0]));w.writeheader();w.writerows(usage)
    m=report['measured'];md=['# Measured local pilot and projected full run','',
        f"Cold wall time: {m['cold_seconds']:.2f} seconds. Warm wall time: {m['warm_seconds']} seconds.",
        f"Classified {m['completed']} of {m['input_count']}; {m['failed']} failed. API subtotal: ${m['api_usd']:.6f}.",
        f"Warm replay new enrichment calls: {m['warm_new_enrichment_calls']}.",'',
        '| Scenario | Estimated API cost | Estimated hours |','|---|---:|---:|']
    for k,v in report['projected']['scenarios'].items():md.append(f"| {k} | ${v['api_usd']:.4f} | {v['hours']:.1f} |")
    md+=['']+report['limitations'];a.out.with_suffix('.md').write_text('\n'.join(md)+'\n')
