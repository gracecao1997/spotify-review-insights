"""Exercise real HTTP save/reload/export using a synthetic case and temporary DB."""
import importlib
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server
from core import FIELDS,connect

class LabelServerTests(unittest.TestCase):
    def test_saved_label_roundtrip_and_invalid_quote_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'evidence').mkdir();db=root/'test.sqlite';connect(db).close()
            source=dict(zip(FIELDS,['synthetic-only','A synthetic test review.','3','0','','2023']))
            with patch.multiple(server,ROOT=root,LABEL_DB=db,GOLDEN=[source],GOLDEN_BY_ID={'synthetic-only':source}):
                http=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
                thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
                base='http://127.0.0.1:'+str(http.server_port)
                try:
                    label={'review_id':'synthetic-only','topic':'other','intent':'unclear','severity':1,'sentiment':0,'entities':[],
                           'evidence_quote':source['review_text'],'needs_review':True}
                    req=urllib.request.Request(base+'/api/labels',data=json.dumps(label).encode(),headers={'Content-Type':'application/json'})
                    with urllib.request.urlopen(req) as r:self.assertEqual(r.status,200)
                    with urllib.request.urlopen(base+'/api/labels') as r:saved=json.load(r)
                    self.assertEqual(saved['labels']['synthetic-only']['severity'],1)
                    self.assertNotIn('review_rating',saved['reviews'][0])
                    label['evidence_quote']='invented'
                    req=urllib.request.Request(base+'/api/labels',data=json.dumps(label).encode(),headers={'Content-Type':'application/json'})
                    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(req)
                    self.assertEqual(error.exception.code,400)
                    error.exception.close()
                    with urllib.request.urlopen(base+'/download') as r:self.assertIn('synthetic-only',r.read().decode())
                    self.assertTrue((root/'evidence/golden_50_human.csv').exists())
                finally:http.shutdown();http.server_close();thread.join()

if __name__=='__main__':unittest.main()
