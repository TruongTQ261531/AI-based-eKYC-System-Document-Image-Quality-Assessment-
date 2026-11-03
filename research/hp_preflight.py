"""Checks performed before any new optimizer update or test prediction."""
import collections
from research.hp_common import *
from research.hp_metrics import scoring
from research.hp_data import refs_for


def check():
    frozen=preserve();rows=read(DATA/'samples.json');card=read(OUT/'dataset_card.json')
    if sha(DATA/'samples.json')!=card['samples_sha256'] or sha(DATA/'base_graphs.json')!=card['base_graphs_sha256']:
        raise ValueError('Prepared data hashes differ')
    graphs={r['base']['physical_id']:r['nodes'] for r in read(DATA/'base_graphs.json')}
    expected=[r for r in read(OLD_DATA/'samples.json') if r['role']=='train' and r['variant']=='partial']
    train=[r for r in rows if r['role']=='train'];dev=[r for r in rows if r['role']=='development'];test=[r for r in rows if r['role']=='test']
    if len(train)!=640 or len(dev)!=96 or len(test)!=192:raise ValueError('Unexpected split sizes')
    if [(r['physical_id'],r['slot']) for r in train]!=[(r['physical_id'],r['slot']) for r in expected]:raise ValueError('Train slot mismatch')
    changed=[(a,b) for a,b in zip(train,expected) if a['input_sha256']!=b['input_sha256']]
    if len(changed)!=64 or len({a['physical_id'] for a,b in changed})!=32:raise ValueError('Unexpected hard-mask coverage')
    for row in rows:
        if sha(ROOT/row['path'])!=row['input_sha256']:raise ValueError('Image changed')
        metrics,_=scoring(row,__import__('json').dumps(row['target'],ensure_ascii=False))
        if metrics['correct']!=len(row['target']) or metrics['predicted']!=len(row['target']):raise ValueError('Reference self-score failed')
        if 'pair_hidden_key' in row:
            replay=refs_for(graphs[row['physical_id']],row['mask_regions'],row['width'],row['height'])
            if any(replay[k]!=row[k] for k in ('target','source_refs','source_evidence','masked_keys')):raise ValueError('Pair reference replay differs')
            if row['pair_hidden_key'] in row['target'] or row['pair_kept_key'] not in row['target']:raise ValueError('Opposite target invalid')
    previous=[]
    for rel in ('vlm_lora_v1','vlm_lora_v2_r2','source_visibility_v3','recovery_v4','layout_stress'):
        path=ROOT/'research/data'/rel/'samples.json'
        if path.exists():previous.extend(read(path))
    old_ids={r['physical_id'] for r in previous};old_hashes={r['input_sha256'] for r in previous if 'input_sha256' in r}
    old_fingerprints={stable_hash(r['target']) for r in previous if isinstance(r.get('target'),dict) and r['target']}
    if old_ids & {r['physical_id'] for r in test}:raise ValueError('Test document was used before')
    if old_hashes & {r['input_sha256'] for r in test}:raise ValueError('Test raster was used before')
    if any(stable_hash(r['target']) in old_fingerprints for r in test if r['capture']=='full' and r['target']):
        raise ValueError('Complete test answer fingerprint used before')
    for key in KEYS:
        if key.startswith('uniform_'):baseline(key)
    hash_ids=collections.defaultdict(set)
    for r in test:hash_ids[r['input_sha256']].add(r['physical_id'])
    save(OUT/'preflight.json',dict(status='passed',signature=signature(),frozen_V1_files=frozen[0],frozen_V4_files=frozen[1],
        self_scored_rows=len(rows),new_test_cases=len(test),new_test_document_instances=48,
        distinct_new_test_rasters=len(hash_ids),cross_document_exact_raster_groups=sum(len(ids)>1 for ids in hash_ids.values()),
        prior_document_overlap=0,prior_raster_overlap=0,prior_complete_answer_fingerprint_overlap=0,
        changed_train_slots=len(changed),changed_train_document_instances=32,
        retained_train_slot_order=True,pair_reference_replay=True,
        pair_eligibility_by_role={role:sum('pair_hidden_key' in r for r in rows if r['role']==role) for role in ('train','development','test')},
        fallback_counts_by_role={role:sum(bool(r.get('pair_fallback')) for r in rows if r['role']==role) for role in ('train','development','test')},
        raw_labels_images_or_weights_published=False,training_started=False))
    print('HP_PREFLIGHT_PASSED',len(rows),flush=True)


if __name__=='__main__':check()
