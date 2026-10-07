"""Reproducible instructor-approved 100k scope, preserving all empty source rows."""
import csv
import hashlib
import heapq
from pathlib import Path
from core import ROOT,FIELDS,read_csv,write_json

SEED='berkeley-fall-2026-assignment-5-v1'
def prepare():
    source=ROOT/'data/spotify_reviews_18months.csv';target=ROOT/'data/analysis_100000.csv'
    source_hash=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
    if source_hash!='1fc85de68a304dd8978b537cfa58793d5f41cbaf417fa32cb53899f83a2fcef6':raise ValueError('Source checksum changed')
    heap=[];total=empty=0
    for r in read_csv(source):
        total+=1
        if not r['review_text'].strip():empty+=1;continue
        score=int.from_bytes(hashlib.sha256((SEED+':'+r['review_id']).encode()).digest(),'big')
        entry=(-score,r['review_id'])
        if len(heap)<100000:heapq.heappush(heap,entry)
        elif score < -heap[0][0]:heapq.heapreplace(heap,entry)
    selected={x[1] for x in heap}
    for name in ['cost_100.csv','checkpoint_500.csv','analysis_10000.csv','golden_50_to_label.csv']:
        assert {r['review_id'] for r in read_csv(ROOT/'data'/name)}<=selected, 'Development/golden scope mismatch'
    unique=set();count=0
    with target.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');w.writeheader()
        for r in read_csv(source):
            if r['review_id'] in selected or not r['review_text'].strip():
                w.writerow(r);count+=1
                if r['review_text'].strip():unique.add(r['review_text'])
    with target.open('rb') as f:target_hash=hashlib.file_digest(f,'sha256').hexdigest()
    report={'approval':'User reports professor permits 100k; communicated in task on 2026-10-06.',
       'source_count':total,'source_sha256':source_hash,'analysis_file':target.name,'analysis_sha256':target_hash,
       'analysis_count':count,'nonempty_to_classify':len(selected),'empty_text_quarantines':empty,
       'distinct_nonempty_texts':len(unique),'method':'Lowest 100000 SHA-256(seed + colon + review_id) among all nonempty source rows, plus every empty source row. Output retains source order.',
       'seed':SEED,'includes_all_fixed_development_and_golden_ids':True,
       'golden_answer_labels_included':False,'api_budget_usd':10,'operational_stop_usd':9}
    write_json(ROOT/'evidence/analysis_scope.json',report);print(report)
if __name__=='__main__':prepare()
