"""No optimizer/test inference until budgets, provenance and overlap checks pass."""
import collections
import hashlib
import json
from PIL import Image, ImageOps
from research.fc_common import *
from research.hp_metrics import scoring
from research.hp_data import refs_for


def pixel_digest(row):
    encoded=row['input_sha256'];path=ROOT/row['path']
    if sha(path)!=encoded:raise ValueError('Image bytes changed')
    cached=CACHE/'pixel_hashes'/(encoded+'.json')
    if cached.exists():return read(cached)['pixel_sha256']
    with Image.open(path) as image:
        image=ImageOps.exif_transpose(image).convert('RGB')
        value=hashlib.sha256(f'RGB/{image.width}/{image.height}/'.encode()+image.tobytes()).hexdigest()
    save(cached,dict(input_sha256=encoded,pixel_sha256=value))
    return value


def check():
    frozen=preserve();card=read(OUT/'dataset_card.json')
    if sha(ROOT/'research/fc_data.py')!=card['data_code_sha256']:raise ValueError('Preparation code changed')
    if sha(DATA/'base_graphs.json')!=card['graphs_sha256']:raise ValueError('Test reference graph changed')
    for folder,result in ((HP_DATA,HP_OUT),(V3_DATA,V3_OUT)):
        if sha(folder/'samples.json')!=read(result/'dataset_card.json')['samples_sha256']:
            raise ValueError('Frozen private source data changed')
    arms={a:train_rows(a) for a in ARMS};rows=eval_rows('development')+eval_rows('test')
    old_uniform=[r for r in read(V3_DATA/'samples.json') if r['role']=='train' and r['variant']=='partial']
    old_hard=[r for r in read(HP_DATA/'samples.json') if r['role']=='train']
    if arms['uniform']!=old_uniform or arms['hard']!=old_hard:raise ValueError('Frozen training controls changed')
    if [r for r in read(HP_DATA/'samples.json') if r['role']=='development']!=eval_rows('development'):
        raise ValueError('Development inputs changed')
    train_ids={r['physical_id'] for r in old_uniform};dev=eval_rows('development');test=eval_rows('test')
    dev_ids={r['physical_id'] for r in dev};test_ids={r['physical_id'] for r in test}
    if len(train_ids)!=128 or len(dev_ids)!=24 or len(test_ids)!=48 or len(dev)!=96 or len(test)!=192:
        raise ValueError('Unexpected registered data sizes')
    if train_ids&dev_ids or train_ids&test_ids or dev_ids&test_ids:raise ValueError('Role identity overlap')
    order=[(r['physical_id'],r['slot']) for r in old_uniform]
    for arm,values in arms.items():
        if len(values)!=640 or [(r['physical_id'],r['slot']) for r in values]!=order:
            raise ValueError('Unmatched ordered ID slots')
    graphs={r['base']['physical_id']:r for r in read(HP_DATA/'base_graphs.json')}
    graphs.update({r['base']['physical_id']:r for r in read(DATA/'base_graphs.json')})
    pixels={};scored=0;rebuilt=0
    for row in rows+[r for values in arms.values() for r in values]:
        if row['input_sha256'] not in pixels:pixels[row['input_sha256']]=pixel_digest(row)
        metrics,_=scoring(row,json.dumps(row['target'],ensure_ascii=False))
        if metrics['correct']!=len(row['target']) or metrics['predicted']!=len(row['target']):
            raise ValueError('Reference self-score differs')
        scored+=1
        if row.get('pair_hidden_key'):
            graph=graphs[row['physical_id']]
            refs=refs_for(graph['nodes'],row['mask_regions'],row['width'],row['height'])
            if any(refs[k]!=row[k] for k in ('target','source_refs','source_evidence','masked_keys')):
                raise ValueError('Counterfactual reference graph differs')
            if row['pair_hidden_key'] in row['target'] or row['pair_kept_key'] not in row['target']:
                raise ValueError('Hidden/retained target contract failed')
            rebuilt+=1
    design=read(OUT/'training_design.json');support={}
    hard_ids={r['physical_id'] for r in read(HP_OUT/'training_changes.json')['rows']}
    for arm in ('hard','random','repeat'):
        altered=[]
        for old,new in zip(old_uniform,arms[arm]):
            different=pixels[old['input_sha256']]!=pixels[new['input_sha256']]
            if different:
                if old['slot'] not in (3,4):raise ValueError('Unregistered slot changed')
                altered.append(old)
        support[arm]=dict(pixel_changed_slots=len(altered),pixel_changed_ids=len({r['physical_id'] for r in altered}),
                         distinct_training_pixels=len({pixels[r['input_sha256']] for r in arms[arm]}))
    selection=read(DATA/'selection.json');random_ids=set(selection['random_ids'])
    if len(random_ids)!=32 or len(random_ids-hard_ids)!=design['maximum_new_ids_under_matched_strata_and_tokens']:
        raise ValueError('Random comparison did not attain the registered support bound')
    if sum(selection['repeat_uses_a'].values())!=16:raise ValueError('Repeated orientations are not balanced')
    repeat_index=collections.defaultdict(dict)
    for r in arms['repeat']:repeat_index[r['physical_id']][r['slot']]=r
    for pid in hard_ids:
        if repeat_index[pid][3]['input_sha256']!=repeat_index[pid][4]['input_sha256'] or repeat_index[pid][3]['target']!=repeat_index[pid][4]['target']:
            raise ValueError('Single-orientation control is not actually repeated')
    tokens=design['answer_loss_tokens_per_seed']
    if tokens['hard']!=tokens['random'] or tokens['hard']!=tokens['repeat']:raise ValueError('Primary global token budgets differ')
    from transformers import AutoTokenizer
    from research.vlm_setup import CACHE as BASE_CACHE
    from research.fc_data import answer_tokens
    import numpy as np
    tokenizer=AutoTokenizer.from_pretrained(str(BASE_CACHE/'model'),local_files_only=True,trust_remote_code=False)
    exposure={}
    for arm,values in arms.items():
        lengths=[answer_tokens(tokenizer,r['target']) for r in values]
        if 2*sum(lengths)!=tokens[arm]:raise ValueError('Independent answer-token recount differs')
        exposure[arm]=dict(answer_loss_tokens=2*sum(lengths),per_slot_min=min(lengths),per_slot_max=max(lengths),
            per_slot_median=float(np.median(lengths)),per_slot_p95=float(np.percentile(lengths,95)),
            target_key_counts=dict(collections.Counter(k for r in values for k in r['target'])),
            hidden_key_counts=dict(collections.Counter(r['pair_hidden_key'] for r in values if r.get('pair_hidden_key'))))
    save(OUT/'exposure_audit.json',exposure)
    previous=[]
    for path in (ROOT/'research/data').glob('*/samples.json'):
        previous.extend(r for r in read(path) if isinstance(r,dict) and 'physical_id' in r)
    previous_ids={r['physical_id'] for r in previous}
    if previous_ids&test_ids:raise ValueError('A fresh test identity was previously used')
    fingerprints={stable_hash(r['target']) for r in previous if isinstance(r.get('target'),dict) and r['target']}
    if any(stable_hash(r['target']) in fingerprints for r in test if r['capture']=='full' and r['target']):
        raise ValueError('A fresh full-answer fingerprint was previously used')
    old_pixels=set()
    for i,row in enumerate({r['input_sha256']:r for r in previous if 'input_sha256' in r and 'path' in r}.values(),1):
        old_pixels.add(pixel_digest(row))
        if i%128==0:print('FC_PRIOR_PIXEL_CHECK',i,flush=True)
    new_pixels={pixels[r['input_sha256']] for r in test}
    if old_pixels&new_pixels:raise ValueError('Fresh test decoded pixels overlap a previous role')
    targets={}
    for row in test:
        key=pixels[row['input_sha256']];value=stable_hash(row['target'])
        if key in targets and targets[key]!=value:raise ValueError('Identical test pixels have conflicting targets')
        targets[key]=value
    coverage=[]
    from research.v3_sources import source_graph
    for source in read(DATA/'sources.json'):
        _,meta=source_graph(source)
        coverage.append(dict(physical_id=source['physical_id'],code=source['code'],mrz_present=meta['mrz_present'],
            mrz_parsed=meta['mrz_parsed'],author_mrz_line_lengths=[len(r['value']) for r in source['fields'] if r['author_key'].startswith('mrz_line')]))
    excluded=sorted(r['physical_id'] for r in coverage if r['mrz_present'] and not r['mrz_parsed'])
    save(OUT/'analysis_plan.json',dict(primary_test_cases=192,primary_test_instances=48,
        supplementary_excluded_document_instances=excluded,coverage_inventory=coverage,
        exclusion_basis='Author MRZ metadata present but no recognized TD3 source; no model outputs used',
        bootstrap_resamples=10000,bootstrap_seed=20261106,permutations=10000,permutation_seed=20261107,
        primary_comparisons=[[f'hard_{s}',f'{a}_{s}'] for s in SEEDS for a in ('random','repeat')],
        primary_family_size=4,multiplicity='Holm p-values and Bonferroni98.75% primary intervals',
        primary_cases_retained=True,test_inference_started=False))
    save(OUT/'pixel_manifest.json',[dict(input_sha256=k,pixel_sha256=v) for k,v in sorted(pixels.items())])
    hash_ids=collections.defaultdict(set)
    for row in test:hash_ids[pixels[row['input_sha256']]].add(row['physical_id'])
    save(OUT/'preflight.json',dict(status='passed',signature=signature(),reference_self_scored_rows=scored,
        pair_reference_rows_rebuilt=rebuilt,distinct_input_encodings=len(pixels),distinct_test_pixels=len(new_pixels),
        cross_id_test_pixel_groups=sum(len(v)>1 for v in hash_ids.values()),prior_decoded_pixel_overlap=0,
        prior_document_overlap=0,prior_full_answer_fingerprint_overlap=0,duplicate_target_conflicts=0,
        actual_training_pixel_support=support,matched_ID_slot_order=True,primary_answer_tokens_matched=True,
        source_coverage_exclusions=len(excluded),frozen_V1_files=frozen[0],frozen_V4_files=frozen[1],
        frozen_HP_files=len(read(OUT/'previous_artifacts.json')['files']),training_started=False,new_test_inference_started=False))
    print('FC_PREFLIGHT_PASSED',scored,len(new_pixels),'test_pixels',flush=True)


if __name__=='__main__':check()
