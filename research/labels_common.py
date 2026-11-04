"""Private OCR annotations and public, versioned evidence for priority one."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'research/data/ocr_labels_v1'
CACHE=ROOT/'research/cache/ocr_labels_v1'
OUT=ROOT/'research/results/ocr_labels_v1'
DB=DATA/'annotations.sqlite3'
REVIEW_DB=CACHE/'reviews.sqlite3'
SEED=20261104

def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def uid(value):return hashlib.sha256(value.encode()).hexdigest()

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    tmp.write_text(canonical(value)+'\n',encoding='utf-8',newline='\n')
    for attempt in range(9):
        try:tmp.replace(path);return
        except PermissionError:
            if attempt==8:raise
            time.sleep(min(.05*2**attempt,.5))

def progress(stage,complete,total,**extra):
    value=dict(stage=stage,complete=complete,total=total,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**extra)
    save(CACHE/'progress.json',value)
    print('OCR_LABELS',stage,complete,total,flush=True)

def connect(write=False):
    if write:
        DATA.mkdir(parents=True,exist_ok=True);conn=sqlite3.connect(DB)
        conn.execute('PRAGMA journal_mode=WAL');conn.execute('PRAGMA foreign_keys=ON')
    else:
        conn=sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True);conn.execute('PRAGMA query_only=ON')
    conn.row_factory=sqlite3.Row
    return conn

def create_tables(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS images(
      uid TEXT PRIMARY KEY,native_uid TEXT UNIQUE NOT NULL,physical_id TEXT NOT NULL,
      source TEXT NOT NULL,quality TEXT,role TEXT NOT NULL,path TEXT NOT NULL,
      sha256 TEXT NOT NULL,bytes INTEGER NOT NULL,mtime_ns INTEGER NOT NULL,
      width INTEGER NOT NULL,height INTEGER NOT NULL,coordinate_mode TEXT NOT NULL,
      metadata TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS fields(
      image_uid TEXT NOT NULL REFERENCES images(uid),field_id TEXT NOT NULL,
      raw_key TEXT NOT NULL,transcript TEXT NOT NULL,annotation TEXT NOT NULL,
      PRIMARY KEY(image_uid,field_id));
    CREATE INDEX IF NOT EXISTS idx_images_group ON images(physical_id,source);
    CREATE INDEX IF NOT EXISTS idx_images_role ON images(role,source);
    ''')

def freeze_previous():
    from research.fc_common import preserve,signature as fc_signature
    preserve()
    if fc_signature()!='80df897cd6d3f60aab774d68e761812ac0ce7ab53bda25f47d3ad1c268e6102e':
        raise ValueError('Previous fair-control contract differs')
    path=OUT/'previous_artifacts.json'
    if path.exists():
        old=read(path)
        if any(sha(ROOT/r['path'])!=r['sha256'] for r in old['files']):raise ValueError('Previous FC evidence changed')
        return old
    files=list((ROOT/'research/results/fair_controls_v1').glob('*.json'))
    files+=list((ROOT/'research').glob('fc_*.py'))+list((ROOT/'research').glob('FAIR_CONTROLS*.md'))
    old=dict(fc_signature=fc_signature(),files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in sorted(files)])
    save(path,old);return old

def signature():
    names=('labels_common.py','labels_schema.py','labels_import.py','labels_synth.py',
           'labels_acquire.py','labels_data.py','labels_study.py','labels_metrics.py','OCR_LABELS_PROTOCOL.md')
    value={name:sha(ROOT/'research'/name) for name in names}
    for name in ('corpus_release.json','evaluation_card.json','analysis_plan.json','models.json'):
        value[name]=sha(OUT/name)
    value['previous_artifacts']=sha(OUT/'previous_artifacts.json')
    return digest(value)

def sample_rows(role=None):
    rows=read(DATA/'evaluation.json')
    if sha(DATA/'evaluation.json')!=read(OUT/'evaluation_card.json')['evaluation_sha256']:
        raise ValueError('Prepared evaluation differs')
    return [r for r in rows if role is None or r['role']==role]
