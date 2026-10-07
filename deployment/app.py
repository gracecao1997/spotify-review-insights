"""Read-only deployed backend; every result is retrieved from the packaged SQLite DB."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from flask import Flask,jsonify,render_template,request
app=Flask(__name__)
DB=Path(__file__).resolve().parent/'dashboard.sqlite'

def connect():return sqlite3.connect(f'file:{DB}?mode=ro',uri=True)

@app.get('/')
def home():return render_template('index.html')

@app.get('/api/summary')
def summary():
    with closing(connect()) as db:rows=dict(db.execute('SELECT name,payload FROM artifacts'))
    return jsonify(summary=json.loads(rows['summary']),memo=json.loads(rows['memo']) if 'memo' in rows else None)

@app.get('/api/reviews')
def reviews():
    with closing(connect()) as db:
        rows=db.execute('SELECT payload FROM reviews WHERE issue=? ORDER BY severity DESC,id LIMIT 30',(request.args.get('issue',''),)).fetchall()
    return jsonify([json.loads(r[0]) for r in rows])

@app.get('/api/health')
def health():
    with closing(connect()) as db:count=db.execute('SELECT count(*) FROM reviews').fetchone()[0]
    return jsonify(ok=True,stored_reviews=count,model_calls_on_request=0)
