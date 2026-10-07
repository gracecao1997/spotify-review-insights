"""Synthetic transport/control tests only; never presented as paid model evidence."""
import contextlib
import csv
import io
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from budget import Ledger,BudgetExceeded,NANO
from core import FIELDS
from jev_client import JevClient,MODEL,decode
import jev_run
import jev_pipeline


def response():
    return {'model':MODEL,'answers':{
        'topic':{'type':'choice','choice':'access','confidence':.9},
        'intent':{'type':'choice','choice':'complaint','confidence':.9},
        'severity':{'type':'choice','choice':'4','confidence':.9},
        'sentiment':{'type':'score','score':.4,'confidence':.9},
        'needs_review':{'type':'noul','noul':.1}},'usage':{'input_tokens':1000,'output_tokens':30}}

class JevTests(unittest.TestCase):
    def test_shared_budget_atomic_and_persists_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger.db';ledger=Ledger(p)
            def reserve(i):
                try:ledger.reserve(str(i),NANO);return True
                except BudgetExceeded:return False
            with ThreadPoolExecutor(max_workers=4) as pool:accepted=list(pool.map(reserve,range(15)))
            self.assertEqual(sum(accepted),9);settled_id=str(accepted.index(True))
            ledger.settle(settled_id,None)
            self.assertEqual(Ledger(p).summary()['reserved_or_unknown_usd'],9)
            with self.assertRaises(BudgetExceeded):Ledger(p).reserve('extra',1)
            ledger.settle(settled_id,100)
            Ledger(p).reserve('replacement',NANO-100)
            self.assertAlmostEqual(Ledger(p).summary()['known_api_usd']+Ledger(p).summary()['reserved_or_unknown_usd'],9)

    def test_actual_usage_and_unknown_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            client=JevClient(Path(d)/'ledger.db',transport=lambda payload:(response(),'provider-id'))
            raw,meta=client.call('Cannot log in','success')
            self.assertAlmostEqual(meta['api_cost_usd'],.000042)
            self.assertAlmostEqual(client.ledger.summary()['known_api_usd'],.000042)
            def fail(payload):raise TimeoutError('synthetic timeout')
            client.transport=fail
            with self.assertRaises(TimeoutError):client.call('Cannot log in','unknown')
            self.assertGreater(client.ledger.summary()['reserved_or_unknown_usd'],0)

    def test_decoder_rejects_wrong_model_fractional_severity(self):
        raw=response();label,_=decode(raw,'Cannot log in')
        self.assertEqual(label['severity'],4);self.assertAlmostEqual(label['sentiment'],-.8)
        raw['answers']['severity']['choice']='3.5'
        with self.assertRaises(ValueError):decode(raw,'Cannot log in')
        raw=response();raw['model']='different'
        with self.assertRaises(ValueError):decode(raw,'Cannot log in')

    def test_retry_exact_cache_and_resume_without_new_calls(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);inp=root/'source.csv'
            rows=[dict(zip(FIELDS,[rid,text,'1','0','','2023'])) for rid,text in [('a','Cannot log in'),('b','Cannot log in'),('c','')]]
            with inp.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
            n=[0]
            def transport(payload):
                n[0]+=1;r=response()
                if n[0]==1:r['answers']['severity']['choice']='3.5'
                return r,'synthetic'
            client=JevClient(root/'budget.db',transport=transport)
            args=SimpleNamespace(input=inp,db=root/'state.db',out=root/'cold',limit=None,workers=1,max_seconds=0,phase='initial')
            with patch.object(jev_run,'load_key',return_value='test-only'),patch.object(jev_run,'JevClient',return_value=client),contextlib.redirect_stdout(io.StringIO()):
                cold=jev_run.execute(args)
                args.out=root/'warm';args.phase='resume';warm=jev_run.execute(args)
            self.assertEqual(cold['completed'],2);self.assertEqual(cold['quarantined'],1)
            self.assertEqual(cold['new_enrichment_calls'],2);self.assertEqual(warm['new_enrichment_calls'],0)
            saved=[json.loads(s) for s in (root/'warm/records.jsonl').read_text().splitlines()]
            self.assertEqual(saved[1]['cache_source_id'],'a');self.assertEqual(n[0],2)
            self.assertAlmostEqual(client.ledger.summary()['known_api_usd'],.000084)

if __name__=='__main__':unittest.main()

class CalculatorTests(unittest.TestCase):
    def test_nonzero_rates_and_projection_do_not_change_measurements(self):
        from jev_calculator import calculate
        from core import write_json
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'cold').mkdir();(p/'warm').mkdir()
            exp={'wall_seconds':20,'classification':{'wall_seconds':10,'new_enrichment_calls':1},'stages':{'timings':{'verify':[{}],'rank':{'wall_seconds':.1},'group':{'wall_seconds':2},'memo':{'wall_seconds':3}}}}
            write_json(p/'cold/experiment.json',exp)
            exp['wall_seconds']=.1;exp['classification']['new_enrichment_calls']=0;write_json(p/'warm/experiment.json',exp)
            calls=[{'request_id':r,'role':r,'model':MODEL,'input_tokens':1000,'output_tokens':30,'outcome':'succeeded','wall_seconds':1} for r in ['enrich','verify']]
            for phase in ['cold','warm']:(p/phase/'all_calls.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in calls))
            (p/'cold/records.jsonl').write_text(json.dumps({'status':'completed','source':{'review_text':'synthetic'}})+'\n')
            def rates(rate):
                (p/'rates.csv').write_text(f'model,provider,input_usd_per_million,output_usd_per_million\n{MODEL},typesafe,{rate},0\n')
            rates(.042);a,_=calculate(p,p/'rates.csv')
            rates(.084);b,_=calculate(p,p/'rates.csv')
            c,_=calculate(p,p/'rates.csv',nonempty=200000,distinct=150000)
            self.assertEqual(a['measured']['cold']['known_api_usd']*2,b['measured']['cold']['known_api_usd'])
            self.assertEqual(a['measured']['cold']['wall_seconds'],b['measured']['cold']['wall_seconds'])
            self.assertEqual(b['measured'],c['measured'])
            self.assertEqual(b['measured']['warm']['known_api_usd'],0)
            self.assertEqual(b['measured']['warm']['new_enrichment_calls'],0)
