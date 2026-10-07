"""Offline replay of saved membership, ranking and claims; never imports a model client."""
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def verify(folder, out):
    folder=Path(folder);out=Path(out)
    records={}
    with (folder/'records.jsonl').open() as f:
        for line in f:
            r=json.loads(line)
            if r['review_id'] in records:raise ValueError('Duplicate review ID')
            records[r['review_id']]=r
    groups=defaultdict(list);seen=set()
    with (folder/'membership.csv').open(newline='') as f:
        for m in csv.DictReader(f):
            rid=m['review_id'];key=(m['issue_id'],rid)
            if key in seen:raise ValueError('Duplicate membership')
            seen.add(key);r=records[rid]
            if r['status']!='completed' or r['intent'] not in ('complaint','cancellation'):raise ValueError('Ineligible issue member')
            groups[m['issue_id']].append(r)
    eligible={rid for rid,r in records.items() if r['status']=='completed' and r['intent'] in ('complaint','cancellation')}
    if {rid for _,rid in seen}!=eligible or len(seen)!=len(eligible):raise ValueError('Missing or multiply assigned primary-topic membership')
    rows=[]
    for issue,members in groups.items():
        total=sum(r['severity'] for r in members);n=len(members)
        rows.append({'rank':0,'issue_id':issue,'complaint_count':n,'severity_sum':total,'mean_severity':str((Decimal(total)/n).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP)),'priority_score':total})
    rows.sort(key=lambda r:(-r['priority_score'],r['issue_id']))
    for i,r in enumerate(rows,1):r['rank']=i
    with (folder/'ranking.csv').open(newline='') as f:saved=list(csv.DictReader(f))
    if saved!=[{k:str(v) for k,v in r.items()} for r in rows]:raise ValueError('Ranking differs from saved membership calculation')
    by_issue={r['issue_id']:r for r in rows}
    with (folder/'claims.csv').open(newline='') as f:
        claims=list(csv.DictReader(f))
        for c in claims:
            if Decimal(str(by_issue[c['issue_id']][c['metric']]))!=Decimal(c['value']):raise ValueError('Unsupported numeric claim')
    out.mkdir(parents=True,exist_ok=True)
    with (out/'ranking.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['rank','issue_id','complaint_count','severity_sum','mean_severity','priority_score']);writer.writeheader();writer.writerows(rows)
    result={'records':len(records),'members':len(seen),'issues':len(rows),'claims_checked':len(claims),'ranking_matches':True,'model_calls':0}
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--grading',default='grading');p.add_argument('--out',default='runs/offline-ranking');a=p.parse_args()
    print(json.dumps(verify(a.grading,a.out),indent=2))
