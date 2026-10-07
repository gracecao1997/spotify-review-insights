import csv
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from calculator import calculate
from core import ROOT

class CalculatorTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'runs/pilot-v2/cold/experiment.json').exists(),'Needs saved pilot evidence, never executes a model')
    def test_editable_rates_scale_only_cost(self):
        with tempfile.TemporaryDirectory() as d:
            rates=Path(d)/'rates.csv'
            rates.write_text('model,input_per_million_usd,cached_input_per_million_usd,output_per_million_usd\ngemma3n:e4b-it-q4_K_M,1,0.5,2\n')
            a=calculate(ROOT/'runs/pilot-v2',rates,rate_multiplier=1)
            b=calculate(ROOT/'runs/pilot-v2',rates,rate_multiplier=2)
            self.assertGreater(a['measured']['api_usd'],0)
            self.assertAlmostEqual(b['measured']['api_usd'],2*a['measured']['api_usd'])
            self.assertEqual(b['measured']['cold_seconds'],a['measured']['cold_seconds'])
            c=calculate(ROOT/'runs/pilot-v2',rates,project_rows=10000,unique_texts=10000)
            self.assertEqual(a['measured'],c['measured'])

if __name__=='__main__':unittest.main()
