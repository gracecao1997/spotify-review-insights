"""Read-only dashboard backend serving saved analysis from a SQLite database."""
import argparse
import json
import re
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from core import ROOT,canonical
from stages import load_records,rank

def import_run(db_path,run):
    records=load_records(run/'records.jsonl');ranking,membership,_=rank(records)
    db_path.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(db_path)) as db,db:
        db.executescript('''CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, issue TEXT, status TEXT, severity INTEGER, payload TEXT);
        CREATE INDEX IF NOT EXISTS by_issue ON reviews(issue,severity);
        CREATE TABLE IF NOT EXISTS artifacts(name TEXT PRIMARY KEY,payload TEXT);''')
        db.execute('DELETE FROM reviews');db.execute('DELETE FROM artifacts')
        members={r['review_id']:r['issue_id'] for r in membership}
        db.executemany('INSERT INTO reviews VALUES(?,?,?,?,?)',[(r['review_id'],members.get(r['review_id']),r['status'],r.get('severity'),canonical(r)) for r in records])
        summary={'scope':'Approved 100,000-review analysis' if len(records)==100013 else 'Development checkpoint','input_count':len(records),'full_source_count':660622,
                 'completed':sum(r['status']=='completed' for r in records),'quarantined':sum(r['status']=='quarantined' for r in records),
                 'pending':sum(r['status']=='pending' for r in records),'complaints':len(membership),'ranking':ranking,
                 'human_evaluation':'50 independent human labels complete; see repository for human/model evaluation',
                 'warning':'Historical self-selected reviews; model errors and coarse grouping limit interpretation. Analysis covers a professor-approved sample, not the whole source.' if len(records)==100013 else 'Checkpoint results are provisional; this is not the final analysis.'}
        db.execute('INSERT INTO artifacts VALUES(?,?)',('summary',canonical(summary)))
        memo=run/'memo.json'
        if memo.exists():
            m=json.loads(memo.read_text())
            if any(re.search(r'\b(churn|retention|revenue|profit)\b',m.get(k,''),re.I) for k in ['recommendation','rationale','alternatives']):
                summary['warning']+=' The saved model memo also contains an unsupported business-outcome inference and requires revision.'
                db.execute('UPDATE artifacts SET payload=? WHERE name=?',(canonical(summary),'summary'))
            db.execute('INSERT INTO artifacts VALUES(?,?)',('memo',canonical(m)))
    print(f'Imported {len(records)} records into {db_path}',flush=True)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url=urlparse(self.path)
        if url.path=='/':payload=(ROOT/'web/dashboard.html').read_bytes();kind='text/html; charset=utf-8'
        else:
            with closing(sqlite3.connect(f'file:{self.server.db_path}?mode=ro',uri=True)) as db:
                if url.path=='/api/summary':
                    rows=dict(db.execute('SELECT name,payload FROM artifacts'))
                    result={'summary':json.loads(rows['summary']),'memo':json.loads(rows['memo']) if 'memo' in rows else None}
                elif url.path=='/api/reviews':
                    issue=parse_qs(url.query).get('issue',[''])[0]
                    result=[json.loads(r[0]) for r in db.execute('SELECT payload FROM reviews WHERE issue=? ORDER BY severity DESC,id LIMIT 30',(issue,))]
                else:self.send_error(404);return
            payload=json.dumps(result,ensure_ascii=False).encode();kind='application/json; charset=utf-8'
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(payload)))
        self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(payload)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--db',type=Path,default=ROOT/'runs/dashboard.sqlite');p.add_argument('--import-run',type=Path)
    p.add_argument('--serve',action='store_true');p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8770);a=p.parse_args()
    if a.import_run:import_run(a.db,a.import_run)
    if a.serve:
        http=ThreadingHTTPServer((a.host,a.port),Handler);http.db_path=a.db.resolve()
        print(f'Dashboard: http://{a.host}:{a.port}',flush=True);http.serve_forever()
