"""Append-only human proposals; released answers and model outputs are not edited."""
import datetime
import sqlite3
import uuid
from research.labels_common import *
from research.labels_schema import validate_review

def store(sample,payload,path=REVIEW_DB):
    validate_review(payload)
    expected={f['field_id'] for f in sample['fields']}
    if {r['field_id'] for r in payload['items']}!=expected:raise ValueError('Assess every native field, without adding fields')
    for item in payload['items']:
        if 'polygon' in item:
            if any(not 0<=x<=sample['width'] or not 0<=y<=sample['height'] for x,y in item['polygon']):
                raise ValueError('Proposed region must stay inside the displayed image')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    record=dict(event_id=uuid.uuid4().hex,sample_uid=sample['uid'],input_sha256=sample['input_sha256'],
        submitted_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reviewer_kind='self_declared_human',independence_verified_by_system=False,payload=payload)
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS reviews(event_id TEXT PRIMARY KEY,sample_uid TEXT NOT NULL,reviewer TEXT NOT NULL,record TEXT NOT NULL)')
        conn.execute('INSERT INTO reviews VALUES (?,?,?,?)',(record['event_id'],sample['uid'],payload['reviewer'].strip(),canonical(record)))
    return record

def events(path=REVIEW_DB):
    path=Path(path)
    if not path.exists():return []
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as conn:
        if not conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reviews'").fetchone():return []
        return [json.loads(r[0]) for r in conn.execute('SELECT record FROM reviews ORDER BY rowid')]

def export_verified(path=REVIEW_DB,registry=None):
    registry=registry or {}
    if registry.get('independence_evidence_confirmed') is not True:return []
    allowed=set(registry.get('verified_reviewer_codes',[]));people=registry.get('reviewer_people',{});latest={}
    for event in events(path):
        p=event['payload']
        code=p['reviewer'].strip()
        if code in allowed and code in people and p['independent']:
            latest[event['sample_uid'],people[code]]=event
    groups={}
    for (sample,reviewer),event in latest.items():groups.setdefault(sample,[]).append(event)
    result=[]
    for sample,rows in groups.items():
        if len(rows)<2 or len({r['input_sha256'] for r in rows})!=1:continue
        for field_id in {f['field_id'] for r in rows for f in r['payload']['items']}:
            items=[f for r in rows for f in r['payload']['items'] if f['field_id']==field_id]
            normalized={(f['status'],' '.join(f.get('text','').split()),canonical(f.get('polygon'))) for f in items}
            if len(items)==len(rows) and len(normalized)==1:
                result.append(dict(sample_uid=sample,input_sha256=rows[0]['input_sha256'],field=items[0],
                    review_events=[r['event_id'] for r in rows],basis='Operator-confirmed independent reviewers; agreement, not OCR pseudo-labels'))
    return result

def export_single(path=REVIEW_DB,registry=None):
    registry=registry or {};people=registry.get('reviewer_people',{});latest={}
    for record in events(path):
        code=record['payload']['reviewer'].strip();person=people.get(code,'unverified-code:'+code)
        latest[record['sample_uid'],person]=record
    result=[]
    for (sample,person),record in latest.items():
        for item in record['payload']['items']:
            result.append(dict(sample_uid=sample,input_sha256=record['input_sha256'],field=item,
                review_event=record['event_id'],reviewer_person=person,
                independent_from_answers_self_declared=record['payload']['independent'],
                basis='Single self-declared human assessment; no inter-rater agreement',
                consensus_verified=False))
    return result

def status(path=REVIEW_DB):
    from research.labels_issues import status as issue_status
    rows=events(path)
    registry=read(DATA/'reviewer_registry.json') if (DATA/'reviewer_registry.json').exists() else {}
    single=export_single(path,registry)
    plan=read(OUT/'human_review_plan.json') if (OUT/'human_review_plan.json').exists() else {}
    pilot=set(plan.get('task_ids',[]))
    return dict(events=len(rows),self_declared_reviewer_codes=len({r['payload']['reviewer'].strip() for r in rows}),
        single_review_field_assessments=len(single),single_review_images=len({r['sample_uid'] for r in single}),
        pilot_review_images=len({r['sample_uid'] for r in single if uid(r['sample_uid']) in pilot}),
        single_review_blinded_field_assessments=sum(r['independent_from_answers_self_declared'] for r in single),
        independently_verified_field_labels=len(export_verified(path,registry)),
        sample_issues=issue_status(path),
        automatic_ocr_predictions_count_as_humans=False)
