"""Local human-labeling UI. No model predictions or suggestions are shown."""
import argparse
import csv
import datetime
import json
from contextlib import closing
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse
from core import ROOT,connect,read_csv,validate,LABEL_FIELDS,write_json

GOLDEN=list(read_csv(ROOT/'data/golden_50_to_label.csv'))
GOLDEN_BY_ID={r['review_id']:r for r in GOLDEN}
LABEL_DB=ROOT/'runs/human-labels.sqlite'

def export_labels(db):
    labels={r['id']:json.loads(r['payload']) for r in db.execute('SELECT id,payload FROM human_labels')}
    path=ROOT/'evidence/golden_50_human.csv'; tmp=path.with_suffix('.tmp')
    with tmp.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(GOLDEN[0])+LABEL_FIELDS)
        writer.writeheader()
        for source in GOLDEN:
            row={**source,**labels.get(source['review_id'],{})}
            if isinstance(row.get('entities'),list): row['entities']=json.dumps(row['entities'],ensure_ascii=False)
            writer.writerow(row)
    tmp.replace(path)

class Handler(BaseHTTPRequestHandler):
    def send(self,status,value,kind='application/json; charset=utf-8'):
        content=json.dumps(value,ensure_ascii=False).encode() if kind.startswith('application/json') else value
        self.send_response(status); self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(content))); self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(content)

    def do_GET(self):
        path=urlparse(self.path).path
        if path=='/': return self.send(200,(ROOT/'web/label.html').read_bytes(),'text/html; charset=utf-8')
        if path=='/api/labels':
            with closing(connect(LABEL_DB)) as db, db:
                saved={r['id']:json.loads(r['payload']) for r in db.execute('SELECT id,payload FROM human_labels')}
            # Ratings intentionally hidden to avoid substituting stars for severity.
            return self.send(200,{'reviews':[{'review_id':r['review_id'],'review_text':r['review_text']} for r in GOLDEN],'labels':saved})
        if path=='/api/health': return self.send(200,{'ok':True,'golden_count':len(GOLDEN)})
        if path=='/download':
            with closing(connect(LABEL_DB)) as db, db: export_labels(db)
            return self.send(200,(ROOT/'evidence/golden_50_human.csv').read_bytes(),'text/csv; charset=utf-8')
        return self.send(404,{'error':'Not found'})

    def do_POST(self):
        if self.path!='/api/labels': return self.send(404,{'error':'Not found'})
        if self.headers.get('Origin') not in (None,'http://127.0.0.1:8765','http://localhost:8765'):
            return self.send(403,{'error':'Local labeling only'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<30000: raise ValueError('Invalid body length')
            value=json.loads(self.rfile.read(n)); rid=value['review_id']
            if rid not in GOLDEN_BY_ID: raise ValueError('Unknown review ID')
            label=validate(value,GOLDEN_BY_ID[rid]['review_text'])
            with closing(connect(LABEL_DB)) as db, db:
                db.execute('INSERT OR REPLACE INTO human_labels VALUES(?,?,?)',
                           (rid,json.dumps(label,ensure_ascii=False),datetime.datetime.now(datetime.timezone.utc).isoformat()))
                export_labels(db)
            return self.send(200,{'saved':rid})
        except (ValueError,KeyError,TypeError) as e: return self.send(400,{'error':str(e)})

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--port',type=int,default=8765); a=p.parse_args()
    connect(LABEL_DB).close()
    print(f'Human labeling: http://127.0.0.1:{a.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
