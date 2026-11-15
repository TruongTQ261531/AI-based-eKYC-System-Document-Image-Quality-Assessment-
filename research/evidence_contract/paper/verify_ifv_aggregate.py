"""Verify aggregate consistency and file integrity, without raw human reviews."""
from pathlib import Path
import hashlib
import json
import math
import re


PRIVATE_KEYS={'observed_transcript','output_note','reviewer_id','author_reference',
              'before_output','after_output','source_path'}


def checksum(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def check_public(value):
    if isinstance(value,dict):
        if set(value)&PRIVATE_KEYS: raise ValueError('Private review content in aggregate candidate')
        for item in value.values(): check_public(item)
    elif isinstance(value,list):
        for item in value: check_public(item)
    elif isinstance(value,str) and re.search(r'(?:[A-Za-z]:[\\/]|/Users/|/home/)',value):
        raise ValueError('Machine path in aggregate candidate')


def check_rate(value,n,d):
    if value['numerator']!=n or value['denominator']!=d:
        raise ValueError('Rate denominator differs from counts')
    expected=n/d if d else None
    if expected is None:
        if value['value'] is not None: raise ValueError('Zero denominator must remain unavailable')
    elif not isinstance(value['value'],(int,float)) or not math.isclose(value['value'],expected,abs_tol=1e-12):
        raise ValueError('Rate value differs from counts')


def validate_report(report):
    if report['schema']!='ifv-postreview-analysis/1': raise ValueError('Wrong aggregate schema')
    check_public(report)
    if report['reviewed']!=report['primary_cases']+report['diagnostic_cases']:
        raise ValueError('Review sample denominator differs')
    for panel in (report['original'],report['sensitivity']['results']):
        for endpoint,result in panel.items():
            if result['primary_cases']!=report['primary_cases']:
                raise ValueError('Sensitivity dropped part of the frame')
            for method,item in result['overall'].items():
                c=item['confusion'];tp,fp,fn,tn=[c[k] for k in ('TP','FP','FN','TN')]
                if any(type(n) is not int or n<0 for n in c.values()):
                    raise ValueError('Counts must be nonnegative integers')
                if sum(c.values())!=item['labeled_cases'] or (
                    item['status'].get('CONFIRMED_FAULT',0)!=tp+fn or
                    item['status'].get('NO_FAULT',0)!=fp+tn or
                    sum(item['status'].values())!=result['primary_cases']):
                    raise ValueError('Confusion counts differ from endpoint statuses')
                check_rate(item['precision'],tp,tp+fp)
                check_rate(item['sensitivity_on_reviewed'],tp,tp+fn)
                check_rate(item['false_alarm_rate_on_reviewed'],fp,fp+tn)
                if panel is report['original']:
                    alarms=report['all_alarm_accounting'][endpoint][method]
                    if (alarms['labeled_fault_alarms']!=tp or alarms['labeled_no_fault_alarms']!=fp or
                        alarms['total_alarms']!=sum(alarms['status_counts'].values()) or
                        alarms['unresolved_alarms']!=alarms['total_alarms']-tp-fp):
                        raise ValueError('All-alarm accounting differs from counts')
                    check_rate(alarms['verified_fault_fraction_of_all_alarms'],tp,alarms['total_alarms'])
                    check_rate(alarms['conditional_precision'],tp,tp+fp)
    return dict(status='PASS_AGGREGATE_CONSISTENCY',reviewed=report['reviewed'],
                primary=report['primary_cases'],human_review_reproduced=False,model_calls=0)


def verify(root):
    root=Path(root).resolve()
    manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if actual!=set(manifest['files'])|{'MANIFEST.json'}:
        raise ValueError('Missing or unexpected aggregate package files')
    for name,expected in manifest['files'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root) or checksum(path)!=expected:
            raise ValueError('Aggregate package hash mismatch')
    return validate_report(json.loads((root/'analysis.json').read_text(encoding='utf-8')))


if __name__=='__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent),sort_keys=True))
