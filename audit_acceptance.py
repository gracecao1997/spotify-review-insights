"""Accept only documented missing provider usage; never alter the course audit."""
import json
from pathlib import Path
from core import write_json
from stages import load_records


def assess(audit_path,grading,out):
    audit=json.loads(Path(audit_path).read_text());issues=audit.get('issue_counts',{})
    calls=load_records(Path(grading)/'calls.jsonl')
    unknown=[];missing=0
    for c in calls:
        absent=[k for k in ('input_tokens','output_tokens') if type(c.get(k)) is not int or c[k]<0]
        if absent:
            if c.get('outcome')!='failed' or c.get('api_cost_usd') is not None or not any(s in c.get('error','') for s in ['network error','HTTP 5']):
                raise ValueError('Unexplained missing usage; finalization stopped')
            unknown.append({'request_id':c['request_id'],'missing_fields':absent,'error':c.get('error')});missing+=len(absent)
    accepted=audit['status']=='pass' or (set(issues)=={'invalid_usage'} and issues['invalid_usage']==missing and bool(unknown))
    if not accepted:raise ValueError('Unresolved audit issues: '+str(issues))
    report={'accepted_for_publication':True,'course_audit_status':audit['status'],
        'disclosure':'Course audit unchanged. Coverage, ranking and provenance checks have no flags. Provider usage is unavailable for the listed failed calls; unknown charges remain reserved, not treated as zero.',
        'failed_calls_with_unavailable_usage':unknown}
    write_json(out,report);return report
