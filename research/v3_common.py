"""Prospective source-aware reference-policy study on the exact R2 pixels."""
import hashlib
import json
from pathlib import Path
from research.v2_common import ROOT,CONFIG,KEYS,PROMPT,read,save,sha,stable_hash,preserve_v1
from research.v2_common import DATA as R2DATA,CACHE as R2CACHE,OUT as R2OUT

DATA=ROOT/'research/data/source_visibility_v3'
CACHE=ROOT/'research/cache/source_visibility_v3'
OUT=ROOT/'research/results/source_visibility_v3'

def load(role=None):
    if sha(DATA/'samples.json')!=read(OUT/'dataset_card.json')['samples_sha256']:raise ValueError('Source-reference dataset changed')
    rows=read(DATA/'samples.json')
    return [r for r in rows if (role is None or r['role']==role) and (r['role']!='train' or r['variant']=='partial')]

def signature():
    files=['v3_common.py','v3_sources.py','v3_data.py','v3_metrics.py','v3_study.py','V3_PROTOCOL.md']
    hashes={p:sha(ROOT/'research'/p) for p in files}
    hashes['R2_contract']=__import__('research.v2_common',fromlist=['signature']).signature()
    hashes['dataset_card']=sha(OUT/'dataset_card.json')
    return stable_hash(hashes)
