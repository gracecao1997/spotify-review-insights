"""Shared durable API spend ledger. Unknown charges retain their full reservation."""
import sqlite3
from contextlib import closing
from pathlib import Path

NANO=1_000_000_000
HARD_LIMIT=10*NANO
STOP_LIMIT=9*NANO

class BudgetExceeded(RuntimeError):pass

class Ledger:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with closing(self.connect()) as db,db:
            db.executescript('''CREATE TABLE IF NOT EXISTS budget_settings(id INTEGER PRIMARY KEY CHECK(id=1),hard_limit INTEGER,stop_limit INTEGER);
            INSERT OR IGNORE INTO budget_settings VALUES(1,10000000000,9000000000);
            CREATE TABLE IF NOT EXISTS charges(request_id TEXT PRIMARY KEY,reserved_nano INTEGER NOT NULL,actual_nano INTEGER,state TEXT NOT NULL);
            ''')
            hard,stop=db.execute('SELECT hard_limit,stop_limit FROM budget_settings WHERE id=1').fetchone()
            if hard!=HARD_LIMIT or stop!=STOP_LIMIT:raise ValueError('Budget settings differ from user-authorized $10 cap / $9 dispatch stop')
    def connect(self):
        db=sqlite3.connect(self.path,timeout=30);db.execute('PRAGMA journal_mode=WAL');return db
    def reserve(self,rid,amount):
        if type(amount) is not int or amount<=0:raise ValueError('Reservation must be positive integer nanodollars')
        with closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                used=db.execute('SELECT COALESCE(SUM(COALESCE(actual_nano,reserved_nano)),0) FROM charges').fetchone()[0]
                if used+amount>STOP_LIMIT:raise BudgetExceeded('Dispatch stopped before $9; $1 of the $10 authorization remains as a safety margin.')
                db.execute('INSERT INTO charges VALUES(?,?,NULL,?)',(rid,amount,'in_flight'));db.commit()
            except BaseException:db.rollback();raise
    def settle(self,rid,actual=None):
        if actual is not None and (type(actual) is not int or actual<0):raise ValueError('Invalid billed amount')
        with closing(self.connect()) as db,db:
            row=db.execute('SELECT reserved_nano FROM charges WHERE request_id=?',(rid,)).fetchone()
            if row is None:raise ValueError('Unknown reservation')
            db.execute('UPDATE charges SET actual_nano=?,state=? WHERE request_id=?',(actual,'settled' if actual is not None else 'unknown',rid))
            if actual is not None and actual>row[0]:
                # Freeze future dispatch if documented token bounds turn out insufficient.
                db.execute('INSERT OR IGNORE INTO charges VALUES(?,?,NULL,?)',('safety-freeze-'+rid,STOP_LIMIT,'frozen'))
    def summary(self):
        with closing(self.connect()) as db:
            actual=db.execute('SELECT COALESCE(SUM(actual_nano),0) FROM charges').fetchone()[0]
            unknown=db.execute('SELECT COALESCE(SUM(reserved_nano),0) FROM charges WHERE actual_nano IS NULL').fetchone()[0]
            states=dict(db.execute('SELECT state,count(*) FROM charges GROUP BY state'))
        return {'known_api_usd':actual/NANO,'reserved_or_unknown_usd':unknown/NANO,'authorized_cap_usd':10,'dispatch_stop_usd':9,'states':states}
