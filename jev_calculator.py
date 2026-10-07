"""Offline arithmetic from saved Jev pilot calls. No credentials/network/model execution."""
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from core import write_json
from stages import load_records,write_csv


def calculate(base,rates_path,nonempty=100000,distinct=78099,verify_fraction=.01, budget=10., reserve_margin=1., max_workers=2, output_token_cap=2200, fallback_fraction=0., fallback_usd_per_record=None, fallback_seconds_per_record=None):
    base=Path(base)
    if not 0<distinct<=nonempty:raise ValueError('Distinct count must be within the nonempty count')
    if not 0 <= verify_fraction <= 1 or not 0 <= fallback_fraction <= 1:raise ValueError('Fractions must be between zero and one')
    if budget <= reserve_margin or reserve_margin < 0 or max_workers not in (1,2) or output_token_cap < 1:raise ValueError('Invalid budget or execution controls')
    if fallback_fraction and (fallback_usd_per_record is None or fallback_seconds_per_record is None):raise ValueError('Hypothetical fallback requires explicit unit cost and time; none was executed')
    with Path(rates_path).open(newline='') as f:rates={r['model']:r for r in csv.DictReader(f)}
    exported=(base/'cold_experiment.json').exists()
    cold=json.loads((base/('cold_experiment.json' if exported else 'cold/experiment.json')).read_text())
    warm=json.loads((base/('warm_experiment.json' if exported else 'warm/experiment.json')).read_text())
    cold_calls={r['request_id']:r for r in load_records(base/('cold_calls.jsonl' if exported else 'cold/all_calls.jsonl'))}
    all_calls={r['request_id']:r for r in load_records(base/('pilot_calls.jsonl' if exported else 'warm/all_calls.jsonl'))}
    all_calls.update(cold_calls)
    totals={'cold':defaultdict(lambda:{'calls':0,'input_tokens':0,'output_tokens':0,'api_usd':0.,'unknown_usage_calls':0,'call_wall_seconds':0.}),
            'warm':defaultdict(lambda:{'calls':0,'input_tokens':0,'output_tokens':0,'api_usd':0.,'unknown_usage_calls':0,'call_wall_seconds':0.})}
    usage=[]
    for rid,c in all_calls.items():
        phase='cold' if rid in cold_calls else 'warm';rate=rates[c['model']];r=totals[phase][c['role']]
        inp,out=c.get('input_tokens'),c.get('output_tokens');charged=rate['provider']!='local'
        unknown=charged and c.get('request_sent') is not False and (inp is None or out is None)
        cost=(float(rate['input_usd_per_million'])*(inp or 0)+float(rate['output_usd_per_million'])*(out or 0))/1e6
        r['calls']+=1;r['input_tokens']+=inp or 0;r['output_tokens']+=out or 0;r['api_usd']+=cost
        r['unknown_usage_calls']+=int(unknown);r['call_wall_seconds']+=c.get('wall_seconds',0)
        usage.append({'request_id':rid,'phase':phase,'role':c['role'],'model':c['model'],'input_tokens':inp,'output_tokens':out,
                      'api_usd':cost if not unknown else '', 'usage_unknown':unknown,'outcome':c['outcome']})
    records=load_records(base/('pilot_records.jsonl' if exported else 'cold/records.jsonl'));completed=[r for r in records if r['status']=='completed']
    unique=len({r['source']['review_text'] for r in completed});sample=cold['stages']['timings'].get('verify',[])
    nverify=len(sample)
    if not unique or not nverify:raise ValueError('Pilot must include completed enrichment and independent verification')
    cold_roles=totals['cold'];enrich=cold_roles['enrich'];verify=cold_roles['verify']
    bounded=sum(v['api_usd'] for k,v in cold_roles.items() if k not in ('enrich','verify'))
    rank_wall=cold['stages']['timings']['rank']['wall_seconds']
    fixed_wall=sum(cold['stages']['timings'].get(k,{}).get('wall_seconds',0) for k in ['group','memo'])
    projections={}
    for name,count,retry_multiplier in [('base_exact_cache',distinct,1),('conservative_20_percent_extra',distinct,1.2),('no_result_reuse',nonempty,1)]:
        vn=max(10,math.ceil(nonempty*verify_fraction))
        api=(enrich['api_usd']/unique*count+verify['api_usd']/nverify*vn)*retry_multiplier+bounded
        fallback_count=math.ceil(nonempty*fallback_fraction)
        api+=fallback_count*(fallback_usd_per_record or 0)
        # Measured sequential enrichment throughput includes initial prep/cache work.
        seconds=(cold['classification']['wall_seconds']/len(completed)*count+verify['call_wall_seconds']/nverify*vn)*retry_multiplier+fixed_wall+rank_wall*nonempty/len(records)
        seconds+=fallback_count*(fallback_seconds_per_record or 0)
        projections[name]={'exceeds_dispatch_budget':api>budget-reserve_margin,'projected_fallback_records':fallback_count,'projected_api_usd':api,'projected_seconds_one_worker':seconds,'enrichment_distinct_texts':count,
                           'verification_records':vn,'additional_attempt_multiplier':retry_multiplier,'modeled_not_measured':True}
    unknown=sum(r['unknown_usage_calls'] for phase in totals.values() for r in phase.values())
    measured={phase:{'wall_seconds':exp['wall_seconds'],'by_stage':dict(totals[phase]),
                     'known_api_usd':sum(r['api_usd'] for r in totals[phase].values()),
                     'new_enrichment_calls':exp['classification']['new_enrichment_calls']} for phase,exp in [('cold',cold),('warm',warm)]}
    cold_cost=measured['cold']['known_api_usd']
    providers={c['model']:{'provider':rates[c['model']]['provider'],'effort':c.get('settings',{}).get('effort','See saved experiment/settings'),'label_config':c.get('label_config'),'batch_size':c.get('batch_size',len(c.get('review_ids',[]))),'rate':rates[c['model']]} for c in cold_calls.values()}
    report={'controls':{'budget_usd':budget,'reserve_margin_usd':reserve_margin,'dispatch_limit_usd':budget-reserve_margin,'max_workers':max_workers,'local_output_token_cap':output_token_cap,'jev_output_cap':'fixed response schema; not a generative-token setting','fallback_fraction':fallback_fraction,'fallback_unit_usd':fallback_usd_per_record,'fallback_unit_seconds':fallback_seconds_per_record,'scope':'Calculator planning controls; does not mutate execution settings. Actual paid run uses ledger and saved experiment controls.'},
            'pilot_metrics':{'cost_per_1000_inputs_usd':cold_cost/len(records)*1000,'cost_per_completed_record_usd':cold_cost/len(completed),'completed_per_second':len(completed)/cold['wall_seconds'],'failed_or_quarantined':len(records)-len(completed),'identity_evidence':'pilot_records.jsonl original IDs and source_sha256; course/manifest.json records fixed CSV checksum','models_and_rates':providers,'workers':cold.get('workers')},
            'measured':measured,'pilot_input_count':len(records),'pilot_completed':len(completed),'pilot_distinct_texts':unique,
            'projection_nonempty':nonempty,'projection_distinct':distinct,'verification_fraction':verify_fraction,
            'projections':projections,'unknown_usage_calls':unknown,'local_compute_usd':None,
            'scale_ready_on_cost_only':unknown==0 and projections['conservative_20_percent_extra']['projected_api_usd']<budget-reserve_margin,
            'limitations':['Worker/output settings describe scenario limits; no measured speedup or token-saving claim is made. Paid fallback is disabled in the executed pipeline.',
                          'Measured pilot retries are included; conservative scenario adds another 20%.',
                          'Runtime extrapolates one worker and can vary with server load; no measured parallel speedup is claimed.',
                          'Estimates describe the target run, excluding sunk development spend. Check the shared budget ledger before scaling.',
                          'Unknown usage prevents a complete cost result. Local hardware/energy costs are unmeasured.',
                          'Quality and checkpoint completion must also be checked before scaling.']}
    return report,usage

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot',default='cost/jev');p.add_argument('--rates',default='cost/jev_rates.csv')
    p.add_argument('--nonempty',type=int,default=100000);p.add_argument('--distinct',type=int,default=78099);p.add_argument('--out',default='cost/jev')
    p.add_argument('--budget',type=float,default=10);p.add_argument('--reserve-margin',type=float,default=1)
    p.add_argument('--max-workers',type=int,choices=[1,2],default=2);p.add_argument('--output-token-cap',type=int,default=2200)
    p.add_argument('--verify-fraction',type=float,default=.01);p.add_argument('--fallback-fraction',type=float,default=0)
    p.add_argument('--fallback-usd-per-record',type=float);p.add_argument('--fallback-seconds-per-record',type=float)
    a=p.parse_args();report,usage=calculate(a.pilot,a.rates,a.nonempty,a.distinct,a.verify_fraction,a.budget,a.reserve_margin,a.max_workers,a.output_token_cap,a.fallback_fraction,a.fallback_usd_per_record,a.fallback_seconds_per_record);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    write_json(out/'report.json',report);write_csv(out/'usage.csv',list(usage[0]),usage)
    text=['# Jev pilot measurements and projection','',f"Pilot: {report['pilot_completed']} / {report['pilot_input_count']} completed.",'',
          '| Experiment | Measured seconds | Known API USD | New enrichment calls |','|---|---:|---:|---:|']
    for phase,r in report['measured'].items():text.append(f"| {phase} | {r['wall_seconds']:.3f} | {r['known_api_usd']:.6f} | {r['new_enrichment_calls']} |")
    text+=['','## Estimates, not executed results','','| Scenario | Projected API USD | Projected one-worker hours |','|---|---:|---:|']
    for name,r in report['projections'].items():text.append(f"| {name} | {r['projected_api_usd']:.4f} | {r['projected_seconds_one_worker']/3600:.2f} |")
    text+=['','## Measured per-stage usage','','| Stage | Calls | Input tokens | Output tokens | Known API USD |','|---|---:|---:|---:|---:|']
    for stage,r in report['measured']['cold']['by_stage'].items():text.append(f"| {stage} | {r['calls']} | {r['input_tokens']} | {r['output_tokens']} | {r['api_usd']:.9f} |")
    text+=['',f"Cost per 1,000 inputs: ${report['pilot_metrics']['cost_per_1000_inputs_usd']:.9f}; per completed record: ${report['pilot_metrics']['cost_per_completed_record_usd']:.9f}; throughput: {report['pilot_metrics']['completed_per_second']:.4f} records/second.",'', '## Editable planning controls',json.dumps(report['controls'],indent=2),'', 'Scenario budget warnings: '+json.dumps({k:v['exceeds_dispatch_budget'] for k,v in report['projections'].items()}),'']+['- '+s for s in report['limitations']]
    (out/'report.md').write_text('\n'.join(text)+'\n');print(json.dumps(report,indent=2))
