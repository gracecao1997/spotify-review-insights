"""Rubric acceptance tests using committed real usage, without credentials or calls."""
import csv
import tempfile
import unittest
from pathlib import Path
from jev_calculator import calculate
from core import ROOT

class JevCalculatorAcceptance(unittest.TestCase):
    def test_rates_volume_and_budget_are_independent_of_measurements(self):
        base=ROOT/'cost/jev';rates=ROOT/'cost/jev_rates.csv'
        a,_=calculate(base,rates)
        with tempfile.TemporaryDirectory() as d:
            doubled=Path(d)/'rates.csv'
            with rates.open(newline='') as f:
                reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
            for r in rows:
                if r['provider']!='local':
                    for k in ['input_usd_per_million','output_usd_per_million']:r[k]=str(float(r[k])*2)
            with doubled.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
            b,_=calculate(base,doubled)
        self.assertAlmostEqual(b['measured']['cold']['known_api_usd'],a['measured']['cold']['known_api_usd']*2)
        self.assertEqual(b['measured']['cold']['wall_seconds'],a['measured']['cold']['wall_seconds'])
        self.assertEqual(b['local_compute_usd'],a['local_compute_usd'])
        full,_=calculate(base,rates,660609,484189)
        self.assertEqual(full['measured'],a['measured'])
        self.assertTrue(full['projections']['base_exact_cache']['exceeds_dispatch_budget'])
        low,_=calculate(base,rates,budget=2,reserve_margin=1)
        self.assertFalse(low['scale_ready_on_cost_only'])
        self.assertEqual(a['measured']['warm']['new_enrichment_calls'],0)
        self.assertEqual(a['measured']['warm']['known_api_usd'],0)

    def test_fallback_requires_explicit_assumptions(self):
        with self.assertRaises(ValueError):calculate(ROOT/'cost/jev',ROOT/'cost/jev_rates.csv',fallback_fraction=.1)

if __name__=='__main__':unittest.main()
