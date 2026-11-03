"""Separate, resumable paired-mask intervention; all earlier studies stay frozen."""
from pathlib import Path
from research.v2_common import ROOT, CONFIG as OLD_CONFIG, read, save, sha, stable_hash, preserve_v1
from research.v3_common import DATA as OLD_DATA, OUT as OLD_OUT, CACHE as OLD_CACHE
from research.v3_common import signature as old_signature

DATA=ROOT/'research/data/hard_pairs_v1'
CACHE=ROOT/'research/cache/hard_pairs_v1'
OUT=ROOT/'research/results/hard_pairs_v1'
CONFIG=dict(OLD_CONFIG)
KEYS=('uniform_42','hard_42','uniform_31415','hard_31415')


def preserve():
    one=preserve_v1()
    four=read(ROOT/'research/results/recovery_v4/artifact_index.json')['files']
    if any(sha(ROOT/r['path'])!=r['sha256'] for r in four):raise ValueError('Frozen V4 changed')
    if old_signature()!=read(OLD_OUT/'test_lock.json')['signature']:raise ValueError('Frozen V3 contract changed')
    return one,len(four)


def signature():
    names=['hp_common.py','hp_acquire.py','hp_data.py','hp_metrics.py','hp_study.py','HARD_PAIR_PROTOCOL.md']
    hashes={p:sha(ROOT/'research'/p) for p in names}
    hashes['old_V3_contract']=old_signature()
    hashes['diagnostic_geometry']=sha(ROOT/'research/priority_progress.py')
    hashes['dataset_card']=sha(OUT/'dataset_card.json')
    hashes['hard_case_inventory']=sha(ROOT/'research/cache/current_progress/hard_case_inventory.json')
    return stable_hash(hashes)


def load(role):
    if role not in ('train','development','test'):raise ValueError('Unknown split')
    if sha(DATA/'samples.json')!=read(OUT/'dataset_card.json')['samples_sha256']:raise ValueError('Paired-mask data changed')
    return [r for r in read(DATA/'samples.json') if r['role']==role]


def baseline(key):
    if key not in KEYS or not key.startswith('uniform_'):raise ValueError('Not a uniform baseline')
    seed=int(key.split('_')[1]);record=read(OLD_OUT/f'train_source_{seed}.json')
    path=ROOT/record['selected_checkpoint']
    if sha(path/'adapter_model.safetensors')!=record['selected_adapter_sha256']:raise ValueError('Uniform adapter changed')
    return path,record['selected_adapter_sha256']
