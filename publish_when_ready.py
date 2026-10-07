"""Finite publication step for this authorized assignment run; no paid inference."""
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from core import ROOT,write_json
from jev_client import load_key


def cmd(*args):return subprocess.run([str(x) for x in args],cwd=ROOT,check=True)

def main():
    status=ROOT/'evidence/execution_status.json';deadline=time.monotonic()+6*3600
    while True:
        r=json.loads(status.read_text()) if status.exists() else {}
        if r.get('stage')=='stopped':
            if r.get('error')=='Final mechanical audit requires review; publication stopped.':
                cmd(sys.executable,'finish_assignment.py','--finalize-only')
                continue
            raise RuntimeError('Analysis stopped: '+r.get('error','inspect saved evidence'))
        if r.get('stage')=='analysis_complete':break
        if time.monotonic()>deadline:raise RuntimeError('Publication timed out waiting for the analysis; nothing was published as final.')
        time.sleep(15)
    report=r['report'];summary=report['classification'];budget=report['project_budget']
    assert summary['input_count']==100013 and summary['completed']==100000 and summary['quarantined']==13 and summary['pending']==0
    assert report['audit_status']=='pass' or report.get('audit_accepted') is True
    assert (ROOT/'deployment/dashboard.sqlite').stat().st_size<200_000_000
    cmd('vercel','deploy','deployment','--prod','--yes','--scope','knit3')
    base='https://spotify-review-insights-three.vercel.app'
    with urllib.request.urlopen(base+'/api/health',timeout=60) as f:health=json.load(f)
    assert health['stored_reviews']==100013 and health['model_calls_on_request']==0
    with urllib.request.urlopen(base+'/api/summary',timeout=60) as f:live=json.load(f)
    assert live['summary']['completed']==100000
    source=ROOT/'runs/jev-500/resume'
    for name in ['memo.md','memo.json','verification.json','ranking.csv','claims.csv']:
        shutil.copy2(source/name,ROOT/'evidence'/('final-'+name))
    readme=ROOT/'README.md';s=readme.read_text()
    s=s.replace('The real Jev cold/warm pilot, 500-review checkpoint, human/model comparison and initial public dashboard are complete. The 10,000-review checkpoint is running; the final 100,000-review analysis is not yet complete.',
        'The approved analysis is complete: 100,000 nonempty reviews classified and 13 empty texts quarantined. Coverage, ranking and provenance checks have no flags; unavailable provider usage on failed requests is disclosed in `evidence/audit-disclosure.json`. The published backend retrieves the final processed data, rankings and memo from a deployed read-only SQLite database.')
    s=s.replace('(currently the clearly labeled 500-review checkpoint).','(final approved analysis).')
    s+=f'''\n## Final measured result\n\n- Classified: 100,000; empty quarantines: 13; pending: 0. Original full source: 660,622 rows, profiled separately.\n- Project-wide known API cost: ${budget['known_api_usd']:.6f}; unresolved/in-flight reservations: ${budget['reserved_or_unknown_usd']:.6f}. These are usage-based costs and conservative reservations, not a provider invoice.\n- Local hardware/energy costs remain unmeasured. The API authorization was $10, with a $9 dispatch stop.\n- Final machine-checkable audit: `evidence/final-self-check.json`. This validates artifacts, not semantic truth or a final grade.\n- Final decision memo: `evidence/final-memo.md`; human/model comparison: `evidence/golden_evaluation.json`.\n- Download input sample, grading artifacts, recovery evidence, costs and final outputs from the [final-analysis release](https://github.com/gracecao1997/spotify-review-insights/releases/tag/final-analysis).\n'''
    readme.write_text(s)
    files=['README.md','evidence/audit-disclosure.json','evidence/final_run.json','evidence/final-self-check.json','evidence/final-memo.md','evidence/final-memo.json',
           'evidence/final-verification.json','evidence/final-ranking.csv','evidence/final-claims.csv','evidence/golden_evaluation.json','cost/jev/checkpoint10000_projection.json']
    key=load_key().encode()
    for name in files:assert key not in (ROOT/name).read_bytes(),'Credential detected in publication candidate'
    cmd('git','add',*files);cmd('git','commit','-m','Publish completed approved 100k analysis and audited evidence');cmd('git','push')
    notes=ROOT/'release/final-notes.txt'
    notes.write_text('Completed professor-approved scope: 100,000 nonempty reviews classified plus 13 empty records quarantined. Includes original sample, grading artifacts, actual pilot usage, recovery recording, verification and final memo. The entire original corpus was profiled separately. See README for measured costs, evaluation and limitations.\n')
    cmd('gh','release','create','final-analysis','release/spotify-assignment-evidence.zip','--repo','gracecao1997/spotify-review-insights','--target','codex/spotify-pipeline','--title','Final approved 100,000-review analysis','--notes-file',notes)
    write_json(status,{'stage':'published','updated_unix':time.time(),'dashboard':base,'repository':'https://github.com/gracecao1997/spotify-review-insights','report':report})
    print('Final analysis published and anonymous database access verified.',flush=True)

if __name__=='__main__':
    try:main()
    except BaseException as e:
        write_json(ROOT/'evidence/publication_error.json',{'error':str(e),'updated_unix':time.time()});raise
