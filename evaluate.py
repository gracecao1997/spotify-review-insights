"""Evaluate saved predictions only after all 50 independent human labels are complete."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from core import LABEL_FIELDS,validate,write_json
from stages import load_records

def evaluate(human,predictions):
    with open(human,newline='',encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
    if len(rows)!=50 or any(any(r.get(k,'')=='' for k in LABEL_FIELDS) for r in rows):
        raise ValueError('All 50 human labels must be completed before final evaluation. No labels are inferred.')
    predictions={r['review_id']:r for r in load_records(predictions)}
    comparisons=[];counts=Counter();severity_error=0;sentiment_error=0;available=0;confusion=Counter()
    for row in rows:
        expected={k:row[k] for k in LABEL_FIELDS};expected['severity']=int(expected['severity']);expected['sentiment']=float(expected['sentiment'])
        expected['entities']=json.loads(expected['entities']);expected['needs_review']=expected['needs_review'].lower()=='true'
        validate(expected,row['review_text']);pred=predictions.get(row['review_id'])
        if not pred or pred['status']!='completed':
            comparisons.append({'review_id':row['review_id'],'missing_prediction':True});continue
        available+=1;errors={};confusion[(expected['topic'],pred['topic'])]+=1
        for k in ['topic','intent','severity','needs_review']:
            counts[k]+=expected[k]==pred[k]
            if expected[k]!=pred[k]:errors[k]={'human':expected[k],'model':pred[k]}
        se=abs(expected['severity']-pred['severity']);ae=abs(expected['sentiment']-pred['sentiment'])
        severity_error+=se;sentiment_error+=ae;counts['sentiment_within_0.5']+=ae<=.5
        counts['evidence_exact_substring']+=bool(pred['evidence_quote']) and pred['evidence_quote'] in row['review_text']
        counts['entities_exact_set']+=set(expected['entities'])==set(pred['entities'])
        comparisons.append({'review_id':row['review_id'],'errors':errors,'severity_absolute_error':se,'sentiment_absolute_error':ae,
                            'human':expected,'model':{k:pred[k] for k in LABEL_FIELDS}})
    subsets={}
    for flag,name in [(False,'human_not_flagged'),(True,'human_needs_review')]:
        members=[c for c in comparisons if c.get('human',{}).get('needs_review') is flag]
        subsets[name]={'available_predictions':len(members),'agreement_on_available':{k:sum(k not in c['errors'] for c in members)/len(members) if members else None for k in ['topic','intent','severity']}}
    return {'diagnostic_subsets':subsets,'golden_count':50,'available_predictions':available,'agreement_denominator':50,
         'agreement':{k:v/50 for k,v in counts.items()},'severity_mae_on_available':severity_error/available if available else None,
         'sentiment_mae_on_available':sentiment_error/available if available else None,'sentiment_tolerance_predeclared':.5,
         'ambiguous_human_cases':sum(r['needs_review'].lower()=='true' for r in rows),
         'topic_confusion':[{'human':a,'model':b,'count':n} for (a,b),n in sorted(confusion.items())],
         'comparisons':comparisons,'limitation':'Needs-review cases remain in the overall denominator; subset diagnostics do not establish human certainty. Quote membership does not prove semantic support. Inspect disagreement examples and unsupported entities manually.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--human',default='evidence/golden_50_human.csv');p.add_argument('--predictions',required=True);p.add_argument('--out',default='evidence/golden_evaluation.json');a=p.parse_args()
    report=evaluate(a.human,a.predictions);write_json(a.out,report);print(json.dumps({k:v for k,v in report.items() if k not in ('comparisons','topic_confusion')},indent=2))
