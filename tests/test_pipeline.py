import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import *
from stages import rank

class PipelineTests(unittest.TestCase):
    def test_source_hash_matches_supplied_checker(self):
        spec=importlib.util.spec_from_file_location('checker',ROOT/'course/check_submission.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        r=dict(zip(FIELDS,['id','a,\n"é"','1','0','','2023-01-01']))
        self.assertEqual(row_sha(r),m.row_sha(r))

    def test_multiline_and_empty_text_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';rs=[dict(zip(FIELDS,['a','line one\nline two','1','0','','2023'])),dict(zip(FIELDS,['b','','2','1','v','2023']))]
            with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rs)
            self.assertEqual(list(read_csv(p)),rs)
            db=connect(Path(d)/'db');self.assertEqual(ingest(db,p),2);self.assertEqual(ingest(db,p),2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM sources').fetchone()[0],2)
            db.close()

    def test_validation_rejects_hallucination_and_bool_severity(self):
        r={'topic':'other','intent':'praise','severity':1,'sentiment':1,'entities':[],'evidence_quote':'good','needs_review':False}
        self.assertEqual(validate(r,'good'),r)
        for patch in [{'severity':True},{'sentiment':float('nan')},{'entities':['Spotify']},{'evidence_quote':'great'}]:
            with self.assertRaises(ValueError):validate({**r,**patch},'good')

    def test_ranking_ignores_praise_and_breaks_ties(self):
        rs=[{'review_id':str(i),'status':'completed','topic':t,'intent':intent,'severity':s} for i,(t,intent,s) in enumerate([
            ('billing','complaint',2),('billing','cancellation',2),('access','complaint',4),('playback','praise',5)])]
        ranking,membership,_=rank(rs)
        self.assertEqual([r['issue_id'] for r in ranking],['issue-access','issue-billing'])
        self.assertEqual(ranking[1]['mean_severity'],'2.000000');self.assertEqual(len(membership),3)
        with self.assertRaises(ValueError):rank(rs+[rs[0]])

    def test_deterministic_evidence_preserves_exact_case(self):
        text='spotify PREMIUM\nshuffle!';r=enrich_deterministically({},text)
        self.assertEqual(r['evidence_quote'],text);self.assertEqual(r['entities'],['spotify','PREMIUM','shuffle'])

if __name__=='__main__':unittest.main()
