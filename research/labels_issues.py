"""Reversible exclusion/correction requests without deleting a released sample."""
import datetime
import sqlite3
import uuid
from collections import Counter
from research.labels_common import *

CATEGORIES=('wrong_region','not_document','render_problem','other')

def store(sample,payload,path=REVIEW_DB):
    if not isinstance(payload,dict) or set(payload)-{'reviewer','category','reason','action'}:raise ValueError('Invalid sample issue')
    reviewer=payload.get('reviewer','');reason=payload.get('reason','');action=payload.get('action','flag')
    if not isinstance(reviewer,str) or not isinstance(reason,str):raise ValueError('Text reviewer/reason required')
    reviewer=reviewer.strip();reason=reason.strip()
    if not 1<=len(reviewer)<=40 or action not in ('flag','withdraw'):raise ValueError('Reviewer and issue action required')
    if payload.get('category','other') not in CATEGORIES or len(reason)>2000 or action=='flag' and len(reason)<3:
        raise ValueError('Choose an issue and describe why')
    record=dict(event_id=uuid.uuid4().hex,sample_uid=sample['uid'],input_sha256=sample['input_sha256'],
        reviewer=reviewer,category=payload.get('category','other'),reason=reason,action=action,
        submitted_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        image_deleted=False,benchmark_case_removed=False,readability_label_created=False)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS issues(event_id TEXT PRIMARY KEY,record TEXT NOT NULL)')
        conn.execute('INSERT INTO issues VALUES (?,?)',(record['event_id'],canonical(record)))
    return record

def events(path=REVIEW_DB):
    path=Path(path)
    if not path.exists():return []
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as conn:
        if not conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issues'").fetchone():return []
        return [json.loads(row[0]) for row in conn.execute('SELECT record FROM issues ORDER BY rowid')]

def active(path=REVIEW_DB):
    registry=read(DATA/'reviewer_registry.json') if (DATA/'reviewer_registry.json').exists() else {}
    people=registry.get('reviewer_people',{});latest={}
    for event in events(path):latest[event['sample_uid'],people.get(event['reviewer'],event['reviewer'])]=event
    return [row for row in latest.values() if row['action']=='flag']

def status(path=REVIEW_DB):
    rows=active(path);plan=read(OUT/'human_review_plan.json') if (OUT/'human_review_plan.json').exists() else {}
    ids=set(plan.get('task_ids',[]))
    return dict(active_flagged_images=len({r['sample_uid'] for r in rows}),
        pilot_flagged_images=len({r['sample_uid'] for r in rows if uid(r['sample_uid']) in ids}),
        categories=dict(Counter(r['category'] for r in rows)),images_deleted=0,benchmark_cases_removed=0)
