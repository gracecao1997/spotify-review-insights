"""Create the course's standard export from saved outputs; never calls a model."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from core import ROOT,canonical,write_json
from stages import load_records

def export(source,stages,input_csv,out,checkpoints=None):
    out.mkdir(parents=True,exist_ok=True);records=load_records(source/'records.jsonl')
    if any(r['status']=='pending' for r in records):raise ValueError('Unfinished records: complete or explicitly account for failures before exporting')
    if len({r['review_id'] for r in records})!=len(records):raise ValueError('Repeated source IDs')
    write_json(out/'run.json',{'version':'a5-audit-v1','analysis_count':len(records),
        'analysis_sha256':hashlib.sha256(input_csv.read_bytes()).hexdigest(),'classification_input_fields':['review_text'],'allow_multi_issue':False})
    shutil.copy2(ROOT/'evidence/ingestion.json',out/'ingestion.json')
    (out/'records.jsonl').write_text(''.join(canonical(r)+'\n' for r in records))
    for name in ['membership.csv','ranking.csv','claims.csv']:shutil.copy2(stages/name,out/name)
    calls=load_records(source/'calls.jsonl')
    if (stages/'stage_calls.jsonl').exists():calls+=load_records(stages/'stage_calls.jsonl')
    ids={r['review_id'] for r in records};seen=set();filtered=[]
    for call in calls:
        if call['request_id'] in seen:continue
        if call['role']=='enrich' and not set(call['review_ids'])<=ids:raise ValueError('Unrelated enrichment evidence')
        seen.add(call['request_id']);filtered.append(call)
    (out/'calls.jsonl').write_text(''.join(canonical(c)+'\n' for c in filtered))
    cp=checkpoints or source
    for name in ['checkpoint_before.json','checkpoint_after.json']:shutil.copy2(cp/name,out/name)
    print(f'Exported {len(records)} rows. This is a checkpoint export, not full-corpus completion.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--stages',type=Path,required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,default=Path('grading'));p.add_argument('--checkpoints',type=Path)
    a=p.parse_args();export(a.source,a.stages,a.input,a.out,a.checkpoints)
