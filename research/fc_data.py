"""Source/layout/token-matched random selection and single-orientation controls."""
import collections
import copy
import hashlib
import json
import random
import itertools
import math
from research.fc_common import *
from research import hp_data as masks


def answer_tokens(tokenizer, target):
    text=json.dumps(target,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return len(tokenizer(text,add_special_tokens=False)['input_ids'])+1


def stratified_random(candidates, stratum_counts, total_delta, hard_ids, seed=20261105, attempts=1000000, min_new=4):
    """Uniform reservoir draw among maximally separated, budget-matched subsets."""
    rng=random.Random(seed)
    groups={s:sorted(p for p,r in candidates.items() if tuple(r['stratum'])==s) for s in sorted(stratum_counts)}
    if any(len(groups[s])<n for s,n in stratum_counts.items()):
        raise ValueError('Insufficient candidates in a matched source/layout stratum')
    count=math.prod(math.comb(len(groups[s]),n) for s,n in stratum_counts.items())
    if count>attempts:raise ValueError('Exact selection space exceeds preregistered enumeration cap')
    choices=[list(itertools.combinations(groups[s],n)) for s,n in sorted(stratum_counts.items())]
    best=-1;eligible=0;optimal=0;selected=None
    for combo in itertools.product(*choices):
        chosen=[p for part in combo for p in part]
        if sum(candidates[p]['token_delta'] for p in chosen)!=total_delta:continue
        eligible+=1;outside=len(set(chosen)-set(hard_ids))
        if outside>best:best=outside;optimal=0;selected=None
        if outside==best:
            optimal+=1
            if rng.randrange(optimal)==0:selected=chosen
    if best<min_new:raise ValueError('Token-matched subset support is insufficient for the registered comparison')
    return selected,dict(enumerated_subsets=count,token_matched_subsets=eligible,
        maximum_new_ids_after_token_match=best,maximally_separated_subsets=optimal)


def repeated_directions(items, a_count):
    """Equal total A/B token exposure, balanced orientations, stable hash ties."""
    ordered=sorted(items,key=lambda p:hashlib.sha256(('fc-repeat/'+p).encode()).digest())
    states={(0,0):()}
    for i,pid in enumerate(ordered):
        d=items[pid]['a_tokens']-items[pid]['b_tokens'];next_states={}
        options=(True,False) if hashlib.sha256(pid.encode()).digest()[0]%2 else (False,True)
        for (n,delta),path in states.items():
            for use_a in options:
                m=n+int(use_a)
                if m>a_count or m+len(ordered)-i-1<a_count:
                    continue
                key=m,delta+(d if use_a else -d)
                if key not in next_states:
                    next_states[key]=path+(use_a,)
        states=next_states
    if (a_count,0) not in states:
        raise ValueError('Exact repeated-direction token match unavailable before training')
    return dict(zip(ordered,states[(a_count,0)]))


def training(tokenizer, rebuild=False):
    preserve()
    if (DATA/'train.json').exists() and not rebuild:
        return read(DATA/'train.json')
    uniform=[r for r in read(V3_DATA/'samples.json') if r['role']=='train' and r['variant']=='partial']
    hard=[r for r in read(HP_DATA/'samples.json') if r['role']=='train']
    graphs={r['base']['physical_id']:r for r in read(HP_DATA/'base_graphs.json') if r['base']['role']=='train'}
    old_slots=collections.defaultdict(dict);hard_slots=collections.defaultdict(dict)
    for row in uniform:old_slots[row['physical_id']][row['slot']]=row
    for row in hard:hard_slots[row['physical_id']][row['slot']]=row
    inventory=read(ROOT/'research/cache/current_progress/hard_case_inventory.json')
    frequencies=collections.Counter(k for r in inventory['development_errors'][inventory['model']]
        for kind in ('hidden_output_keys','neighbor_omission_keys','neighbor_wrong_keys') for k in r[kind])
    hard_ids={r['physical_id'] for r in read(HP_OUT/'training_changes.json')['rows']}
    strata=collections.Counter((graphs[p]['base']['source'],graphs[p]['base']['layout']) for p in hard_ids)
    candidates={}
    for pid,graph in sorted(graphs.items()):
        full,nodes=graph['base'],graph['nodes']
        pair=masks.pair_for(nodes,full['width'],full['height'],pid,frequencies)
        if pair is None:continue
        a=masks.refs_for(nodes,masks.regions_for(nodes,pair['a']),full['width'],full['height'])['target']
        b=masks.refs_for(nodes,masks.regions_for(nodes,pair['b']),full['width'],full['height'])['target']
        na,nb=answer_tokens(tokenizer,a),answer_tokens(tokenizer,b)
        delta=na+nb-sum(answer_tokens(tokenizer,old_slots[pid][slot]['target']) for slot in (3,4))
        candidates[pid]=dict(pair=pair,a_tokens=na,b_tokens=nb,token_delta=delta,
                             stratum=(full['source'],full['layout']))
    if not hard_ids<=set(candidates):raise ValueError('Original hard IDs lost eligibility')
    total_delta=sum(answer_tokens(tokenizer,r['target']) for r in hard)-sum(answer_tokens(tokenizer,r['target']) for r in uniform)
    if sum(candidates[p]['token_delta'] for p in hard_ids)!=total_delta:
        raise ValueError('Counterfactual construction differs from the frozen intervention')
    maximum_new=sum(min(n,sum(tuple(r['stratum'])==s and p not in hard_ids for p,r in candidates.items()))
                    for s,n in strata.items())
    if maximum_new<4:raise ValueError('Insufficient support for an informative selection control')
    random_ids,selection_proof=stratified_random(candidates,strata,total_delta,hard_ids,min_new=4)
    directions=repeated_directions({p:candidates[p] for p in hard_ids},16)
    random_rows=[];repeat_rows=[]
    masks.DATA=DATA
    for old in uniform:
        pid,slot=old['physical_id'],old['slot']
        if pid in random_ids and slot in (3,4):
            full,nodes=graphs[pid]['base'],graphs[pid]['nodes'];pair=candidates[pid]['pair']
            hidden,kept=(pair['a'],pair['b']) if slot==3 else (pair['b'],pair['a'])
            row=masks.write_capture(full,nodes,'pair_a' if slot==3 else 'pair_b',
                old['uid']+'/fc-random',hidden,kept)
            row.update(slot=slot,variant='partial',role='train')
            random_rows.append(row)
        else:random_rows.append(copy.deepcopy(old))
        if pid in hard_ids and slot in (3,4):
            selected=hard_slots[pid][3 if directions[pid] else 4]
            row=copy.deepcopy(selected);row.update(slot=slot,uid=old['uid'])
            repeat_rows.append(row)
        else:repeat_rows.append(copy.deepcopy(old))
    arms=dict(uniform=uniform,hard=hard,random=random_rows,repeat=repeat_rows)
    tokens={k:2*sum(answer_tokens(tokenizer,r['target']) for r in values) for k,values in arms.items()}
    if len(set(tokens[k] for k in ('hard','random','repeat')))!=1:
        raise ValueError('Primary ablation answer-token exposure differs')
    save(DATA/'train.json',arms)
    save(DATA/'selection.json',dict(random_ids=random_ids,repeat_uses_a=directions,candidates=candidates))
    save(OUT/'training_design.json',dict(
        document_instances=128,ordered_slots_per_arm=640,steps_per_seed=320,presentations_per_seed=1280,
        new_training_runs=4,reused_training_runs=4,seeds=list(SEEDS),
        selected_document_instances=32,replaced_slots=64,answer_loss_tokens_per_seed=tokens,
        random_selection_proof=selection_proof,random_selection_seed=20261105,
        random_overlap_hard_ids=len(set(random_ids)&hard_ids),random_new_ids=len(set(random_ids)-hard_ids),
        maximum_new_ids_under_matched_strata=maximum_new,
        maximum_new_ids_under_matched_strata_and_tokens=selection_proof['maximum_new_ids_after_token_match'],
        strata=[dict(source=s[0],layout=s[1],selected=n,eligible=sum(tuple(c['stratum'])==s for c in candidates.values()))
                for s,n in sorted(strata.items())],
        repeat_a_count=sum(directions.values()),repeat_b_count=len(directions)-sum(directions.values()),
        primary_global_answer_token_budget_matched=True,exact_FLOPs_or_per_step_token_match=False,
        uniform_is_secondary_whole_intervention_control=True,
        selection_sha256=sha(DATA/'selection.json'),selection_used_model_test_outputs=False))
    print('FC_TRAINING_DATA',tokens,'selection_proof',selection_proof,flush=True)
    return arms


def new_authored(index):
    """New strings/IDs; keep the previous generator, layouts and fonts fixed."""
    # The generator derives all strings from its physical_id, which includes the index.
    # An offset beyond the previous24 makes genuinely new authored identities.
    masks.DATA=DATA
    row=masks.new_authored(1000+index)
    row['physical_id']=f'fair_controls_v1/test/{index:03}'
    row['uid']=row['physical_id']+'/base'
    return row


def build():
    from transformers import AutoTokenizer
    from research.vlm_setup import CACHE as BASE_CACHE
    from research.v2_common import HELD_LAYOUTS
    freeze_previous()
    if (OUT/'dataset_card.json').exists():
        card=read(OUT/'dataset_card.json')
        if card['train_sha256']!=sha(DATA/'train.json') or card['evaluation_sha256']!=sha(DATA/'evaluation.json'):
            raise ValueError('Prepared dataset changed')
        print('FC_DATA_ALREADY_PREPARED',flush=True);return
    tokenizer=AutoTokenizer.from_pretrained(str(BASE_CACHE/'model'),local_files_only=True,trust_remote_code=False)
    arms=training(tokenizer)
    masks.DATA=DATA
    rows=copy.deepcopy([r for r in read(HP_DATA/'samples.json') if r['role']=='development'])
    bases=[];graphs=[]
    from research.v2_data import mapped_fields
    for source in read(DATA/'sources.json'):
        base=dict(physical_id=source['physical_id'],uid=source['physical_id']+'/base',role='test',
            source='midv2020',device=source['device'],layout=source['code'],held_layout=source['code'] in HELD_LAYOUTS,
            path=source['path'],input_sha256=source['source_sha256'],fields=mapped_fields(source),
            width=source['width'],height=source['height'],capture='full')
        bases.append(base);graphs.append(dict(base=base,nodes=masks.nodes_for(base,source)))
    for i in range(24):
        base=new_authored(i);bases.append(base);graphs.append(dict(base=base,nodes=masks.nodes_for(base)))
    for graph in graphs:
        base,nodes=graph['base'],graph['nodes'];pid=base['physical_id']
        pair=masks.pair_for(nodes,base['width'],base['height'],pid)
        for capture in ('full','field_clip','value_mask','pair_mask'):
            uid=pid+'/fc/'+capture
            if capture=='pair_mask' and pair:
                a,b=(pair['a'],pair['b']) if int(hashlib.sha256((pid+'/fc-direction').encode()).hexdigest(),16)%2==0 else (pair['b'],pair['a'])
                row=masks.write_capture(base,nodes,capture,uid,a,b)
            else:
                row=masks.write_capture(base,nodes,'value_mask' if capture=='pair_mask' else capture,uid)
                if capture=='pair_mask':row.update(capture='pair_mask',pair_fallback=True)
            rows.append(row)
    save(DATA/'evaluation.json',rows);save(DATA/'base_graphs.json',graphs)
    save(OUT/'dataset_manifest.json',[{k:r[k] for k in ('uid','physical_id','role','source','device','layout','capture','input_sha256')} for r in rows])
    save(OUT/'dataset_card.json',dict(train_sha256=sha(DATA/'train.json'),evaluation_sha256=sha(DATA/'evaluation.json'),
        graphs_sha256=sha(DATA/'base_graphs.json'),data_code_sha256=sha(ROOT/'research/fc_data.py'),
        development_instances=24,development_cases=96,test_instances=48,test_cases=192,
        test_photo_instances=24,test_authored_instances=24,
        photo_device_counts=dict(collections.Counter(r['device'] for r in bases if r['source']=='midv2020')),
        test_layout_counts=dict(collections.Counter(r['layout'] for r in bases)),
        test_pair_fallbacks=sum(bool(r.get('pair_fallback')) for r in rows if r['role']=='test'),
        independent_camera_collection=False,human_legibility_annotations=0,
        new_layout_or_font_claim=False,all_old_test_results_retained=True))
    print('FC_DATA_READY',len(rows),flush=True)


def refine_provisional():
    """Preserve an unpublished preparation and strengthen its training-only contrast."""
    import datetime
    import shutil
    from transformers import AutoTokenizer
    from research.vlm_setup import CACHE as BASE_CACHE
    if (OUT/'prepare_publication.json').exists() or any((CACHE/'training').glob('*/step_*/complete.json')):
        raise ValueError('Cannot refine data after publication/training')
    backup=CACHE/'provisional_preparation_0'
    paths=[DATA/'train.json',DATA/'selection.json',OUT/'training_design.json',OUT/'dataset_card.json']
    if backup.exists():
        if any(sha(p)!=sha(backup/p.name) for p in paths):raise ValueError('Partially updated preparation differs from the retained backup')
    else:
        backup.mkdir(parents=True)
        for p in paths:shutil.copyfile(p,backup/p.name)
    before={p.name:sha(p) for p in paths}
    tokenizer=AutoTokenizer.from_pretrained(str(BASE_CACHE/'model'),local_files_only=True,trust_remote_code=False)
    training(tokenizer,rebuild=True)
    card=read(OUT/'dataset_card.json');card.update(train_sha256=sha(DATA/'train.json'),data_code_sha256=sha(ROOT/'research/fc_data.py'))
    save(OUT/'dataset_card.json',card)
    save(OUT/'preparation_revision.json',dict(time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reason='Maximize available ID contrast under fixed source/layout/token budget before any optimizer update',
        before_hashes=before,after_hashes={p.name:sha(p) for p in paths},
        previous_random_new_ids=read(backup/'training_design.json')['random_new_ids'],
        final_random_new_ids=read(OUT/'training_design.json')['random_new_ids'],
        failed_maximum6_rejection_log_sha256=sha(CACHE/'preparation_refinement.log'),
        training_started=False,new_test_inference_started=False,raw_provisional_files_preserved_locally=True))
    print('FC_PROVISIONAL_REFINEMENT_RECORDED',flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--refine-provisional',action='store_true')
    a=p.parse_args()
    if a.refine_provisional:refine_provisional()
    else:build()
