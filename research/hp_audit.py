"""Independent raw-score replay, cache/pixel parity, matched budget and intervals."""
import argparse
import hashlib
import json
import subprocess
import numpy as np
from PIL import Image
from research.hp_common import *
from research.hp_metrics import scoring,summary


def features():
    import torch
    from research.hp_study import configure
    from research.v2_inputs import pixels
    model,trainer=configure();unique={r['input_sha256']:r for r in read(DATA/'samples.json')};proof=[]
    for i,row in enumerate(unique.values(),1):
        if sha(ROOT/row['path'])!=row['input_sha256']:raise ValueError('Feature source image changed')
        cached=model.features(row)
        with Image.open(ROOT/row['path']) as image:view,_=model.views.prepare(image,'rect2')
        tensor=pixels(view,'rect2').to(device='cuda',dtype=model.dtype)
        with torch.no_grad():fresh=model.model.extract_feature(tensor).detach().cpu().contiguous()
        if not torch.equal(cached,fresh):raise ValueError('Cached vision differs from pixel re-extraction')
        token=hashlib.sha256((model.input_version+row['input_sha256']).encode()).hexdigest()
        path=CACHE/'features'/'rect2'/(token+'.safetensors')
        proof.append(dict(input_sha256=row['input_sha256'],feature_sha256=sha(path)))
        if i%32==0 or i==len(unique):trainer.progress(stage='hard_pair_feature_audit',complete=i,total=len(unique))
    save(OUT/'feature_audit.json',dict(status='passed',signature=signature(),freshly_reextracted_features=len(proof),
        mismatches=0,rows=proof))


def intervals(records,joined=False):
    rows=records['uniform_42']['rows'];ids=sorted({r['physical_id'] for r in rows});parent={p:p for p in ids}
    def root(p):
        while parent[p]!=p:p=parent[p]
        return p
    if joined:
        hashes={}
        for row in rows:
            p=row['physical_id'];h=row['input_sha256']
            if h in hashes:parent[root(p)]=root(hashes[h])
            else:hashes[h]=p
    groups={p:root(p) for p in ids};clusters=sorted(set(groups.values()))
    sources={g:{r['source'] for r in rows if groups[r['physical_id']]==g} for g in clusters}
    if any(len(s)!=1 for s in sources.values()):raise ValueError('Cross-source duplicate cluster')
    rng=np.random.default_rng(20261104)
    draw=np.concatenate([rng.choice([i for i,g in enumerate(clusters) if sources[g]=={source}],
        (10000,sum(s=={source} for s in sources.values())),replace=True) for source in ('authored','midv2020')],axis=1)
    values={}
    for key,record in records.items():
        a=np.array([[sum(r[f] for r in record['rows'] if groups[r['physical_id']]==g)
                     for f in ('correct','reference','predicted','neighbor_correct','neighbor_reference_keys','declared_hidden_outputs')]
                    for g in clusters],dtype=float)
        totals=a[draw].sum(axis=1)
        values[key]=dict(f1=2*totals[:,0]/np.maximum(1,totals[:,1]+totals[:,2]),
            neighbor_recall=totals[:,3]/np.maximum(1,totals[:,4]),hidden_outputs=totals[:,5])
    comparisons=[]
    for seed in (42,31415):
        a,b='hard_'+str(seed),'uniform_'+str(seed);result=dict(a=a,b=b)
        for metric in ('f1','neighbor_recall','hidden_outputs'):
            diff=values[a][metric]-values[b][metric]
            field='declared_hidden_outputs' if metric=='hidden_outputs' else metric
            result[metric]=dict(delta=records[a]['summary'][field]-records[b]['summary'][field],
                ci95_low=float(np.percentile(diff,2.5)),ci95_high=float(np.percentile(diff,97.5)))
        comparisons.append(result)
    return dict(seed=20261104,resamples=10000,document_instances=len(ids),resampling_clusters=len(clusters),
        method='Paired source-stratified connected-raster document bootstrap' if joined else 'Paired source-stratified document bootstrap',comparisons=comparisons)


def audit():
    import torch
    from safetensors.torch import load_file
    from research.hp_study import verify_test,adapter_for
    from research.hp_data import refs_for
    from research import vlm_train as trainer
    frozen=preserve();sig=signature();lock=verify_test();prepare=read(OUT/'prepare_publication.json');pub=read(OUT/'test_publication.json')
    if prepare['signature']!=sig:raise ValueError('Pretraining signature changed')
    runtime=read(OUT/'runtime_amendment.json');runtime_pub=read(OUT/'runtime_publication.json')
    if runtime['signature']!=sig or runtime['status']!='passed' or runtime_pub['runtime_amendment_sha256']!=sha(OUT/'runtime_amendment.json'):
        raise ValueError('Runtime parity/publication proof differs')
    subprocess.run(['git','merge-base','--is-ancestor',runtime_pub['commit'],pub['commit']],cwd=ROOT,check=True)
    runtime_blob=subprocess.check_output(['git','show',runtime_pub['commit']+':research/hp_workflow.py'],cwd=ROOT)
    if hashlib.sha256(runtime_blob).hexdigest()!=runtime['runtime_policy_source_sha256']:raise ValueError('Published runtime script differs')
    analysis=read(OUT/'analysis_plan.json');analysis_pub=read(OUT/'analysis_publication.json')
    if analysis['signature']!=sig or analysis_pub['analysis_plan_sha256']!=sha(OUT/'analysis_plan.json'):raise ValueError('Coverage analysis registration differs')
    subprocess.run(['git','merge-base','--is-ancestor',analysis_pub['commit'],pub['commit']],cwd=ROOT,check=True)
    subprocess.run(['git','merge-base','--is-ancestor',prepare['commit'],pub['commit']],cwd=ROOT,check=True)
    for name in ('hp_common.py','hp_acquire.py','hp_data.py','hp_metrics.py','hp_study.py','HARD_PAIR_PROTOCOL.md'):
        blob=subprocess.check_output(['git','show',prepare['commit']+':research/'+name],cwd=ROOT)
        if hashlib.sha256(blob).hexdigest()!=sha(ROOT/'research'/name):raise ValueError('Pretraining source bytes differ')
    if read(OUT/'feature_audit.json')['status']!='passed' or read(OUT/'feature_audit.json')['signature']!=sig:
        raise ValueError('Fresh feature audit required')
    data=read(DATA/'samples.json');samples={r['uid']:r for r in data}
    if sha(DATA/'samples.json')!=read(OUT/'dataset_card.json')['samples_sha256']:raise ValueError('Data changed')
    seen_targets={}
    for row in data:
        if row['role']!='test':continue
        target_hash=stable_hash(row['target'])
        if row['input_sha256'] in seen_targets and seen_targets[row['input_sha256']]!=target_hash:raise ValueError('Duplicate pixels have incompatible answers')
        seen_targets[row['input_sha256']]=target_hash
    graphs={r['base']['physical_id']:r for r in read(DATA/'base_graphs.json')}
    old={r['uid']:r for r in read(OLD_DATA/'samples.json')}
    rebuilt=0
    for row in data:
        if 'mask_regions' in row:
            H=np.eye(3);base=graphs[row['physical_id']]['base']
            if row['capture']=='field_clip':H[1,2]=row['fields'][0]['quad'][0][1]-base['fields'][0]['quad'][0][1]
            refs=refs_for(graphs[row['physical_id']]['nodes'],row['mask_regions'],row['width'],row['height'],H)
            if any(row[k]!=refs[k] for k in ('target','source_refs','source_evidence','masked_keys')):raise ValueError('New reference replay differs')
            rebuilt+=1
        elif row!=old[row['uid']]:raise ValueError('Unchanged old row changed')
    train=[r for r in data if r['role']=='train'];training_proof=[]
    for seed in (42,31415):
        record=read(OUT/f'train_hard_{seed}.json');paired=read(OLD_OUT/f'train_source_{seed}.json')
        original_lock=read(OLD_OUT/'test_lock.json')
        if paired['steps']!=320 or paired['presentations']!=1280 or paired['selected_adapter_sha256']!=original_lock['models'][f'source_{seed}']['sha256']:
            raise ValueError('Uniform baseline differs from frozen matched-budget control')
        path,digest=adapter_for('hard_'+str(seed));complete=read(path/'complete.json')
        if record['signature']!=sig or complete['signature']!=sig or complete['step']!=320 or complete['cursor']!=1280:raise ValueError('Training signature/budget differs')
        sequence=[trainer.sampler(train,seed,i) for i in range(1280)]
        if record['identity_slot_sequence_sha256']!=paired['identity_slot_sequence_sha256'] or record['identity_slot_sequence_sha256']!=stable_hash([r['physical_id']+'/'+str(r['slot']) for r in sequence]):raise ValueError('ID/slot exposure differs')
        if record['pixel_sequence_sha256']!=stable_hash([r['input_sha256'] for r in sequence]):raise ValueError('Training pixel sequence differs')
        if [e['step'] for e in record['events']]!=list(range(1,321)):raise ValueError('Training events missing')
        if any(not __import__('math').isfinite(e[k]) for e in record['events'] for k in ('loss','gradient_norm')):raise ValueError('Nonfinite training')
        if any(sha(path/f)!=h for f,h in complete['sha256'].items()):raise ValueError('Checkpoint bytes changed')
        state=torch.load(path/'training_state.pt',map_location='cpu',weights_only=True)
        if state['step']!=320 or state['cursor']!=1280 or len(state['optimizer']['state'])!=192 or any(int(s['step'])!=320 for s in state['optimizer']['state'].values()):raise ValueError('Optimizer updates differ')
        tensors=load_file(str(path/'adapter_model.safetensors'));b=[t for k,t in tensors.items() if 'lora_B' in k]
        if len(tensors)!=192 or len(b)!=96 or not all(bool(t.ne(0).any()) for t in b) or any(not bool(torch.isfinite(t).all()) for t in tensors.values()):raise ValueError('LoRA update proof failed')
        training_proof.append(dict(seed=seed,optimizer_updates=320,presentations=1280,adapter_sha256=digest,nonzero_B_tensors=96,identity_slot_order_matched=True))
        del state,tensors,b
    replay=read(OUT/'resume_replay_diagnostic.json')
    if replay['signature']!=sig or replay['status']!='passed':raise ValueError('Resume scalar replay diagnostic differs')
    primary={e['step']:e for e in read(OUT/'train_hard_42.json')['events']}
    backup=next((CACHE/'training/hard_42').glob('interrupted_events_after_0080_*.json'))
    if sha(backup)!=replay['original_events_backup_sha256']:raise ValueError('Interrupted events backup changed')
    for old_event in read(backup):
        if old_event['step']<=80:continue
        if any(primary[old_event['step']][k]!=old_event[k] for k in ('loss','gradient_norm','learning_rate','max_tokens','cursor')):
            raise ValueError('Recorded replayed update differs')
    replayed=0;new_calls=0;reused=0;records={}
    for role in ('development','test'):
        expected={r['uid'] for r in data if r['role']==role}
        for key in KEYS:
            record=read(OUT/f'{role}_{key}.json')
            if record['signature']!=sig or {r['uid'] for r in record['rows']}!=expected or len(record['rows'])!=len(expected):raise ValueError('Evaluation cases missing or duplicated')
            for row in record['rows']:
                path=CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json');raw=read(path)
                metrics,_=scoring(samples[row['uid']],raw['_private_text'])
                if raw['signature']!=sig or raw['input_sha256']!=row['input_sha256'] or raw['model_sha256']!=row['model_sha256']:
                    raise ValueError('Private prediction headers differ')
                if any(row[k]!=v for k,v in metrics.items()) or row['prediction_sha256']!=hashlib.sha256(raw['_private_text'].encode()).hexdigest():raise ValueError('Raw score replay differs')
                if row['model_sha256']!=lock['models'][key]['sha256'] or row['input_sha256']!=samples[row['uid']]['input_sha256']:raise ValueError('Input/model changed')
                if row['reused_old_development_inference']:
                    if role!='development' or not key.startswith('uniform_'):raise ValueError('Illegitimate output reuse')
                    reused+=1
                else:new_calls+=1
                replayed+=1
            if summary(record['rows'])!=record['summary']:raise ValueError('Summary changed')
            if role=='test':records[key]=record
    fresh=read(OUT/'fresh_repeats.json');pairs=set()
    reference={r['uid']:r for r in records[fresh['model']]['rows']}
    for row in fresh['rows']:
        path=CACHE/'fresh'/(hashlib.sha256((row['uid']+'/'+str(row['repeat'])).encode()).hexdigest()+'.json');raw=read(path)
        metrics,_=scoring(samples[row['uid']],raw['_private_text'])
        if any(row[k]!=v for k,v in metrics.items()) or row['prediction_sha256']!=hashlib.sha256(raw['_private_text'].encode()).hexdigest():raise ValueError('Fresh output replay differs')
        if row['model_sha256']!=lock['models'][fresh['model']]['sha256'] or row['input_sha256']!=samples[row['uid']]['input_sha256']:
            raise ValueError('Fresh model/input differs')
        if row['identical_to_test']!=(row['prediction_sha256']==reference[row['uid']]['prediction_sha256']):raise ValueError('Fresh comparison flag differs')
        pairs.add((row['uid'],row['repeat']))
    if len(pairs)!=16 or len({p for p,r in pairs})!=8 or {r for p,r in pairs}!={1,2}:raise ValueError('Fresh repeat coverage differs')
    if fresh['mismatches']!=sum(not r['identical_to_test'] for r in fresh['rows']):raise ValueError('Fresh mismatch count differs')
    save(OUT/'paired_intervals.json',intervals(records))
    save(OUT/'duplicate_cluster_sensitivity.json',intervals(records,True))
    excluded=set(analysis['supplementary_excluded_document_instances'])
    subset={}
    for key,record in records.items():
        selected=[r for r in record['rows'] if r['physical_id'] not in excluded]
        if len(selected)!=188:raise ValueError('Unparsed-source sensitivity subset differs')
        subset[key]=dict(rows=selected,summary=summary(selected))
    save(OUT/'source_coverage_sensitivity.json',dict(signature=sig,pretest_analysis_publication=analysis_pub['commit'],
        primary_results_unchanged=True,excluded_document_instances=sorted(excluded),new_model_calls=0,
        summaries={k:r['summary'] for k,r in subset.items()},intervals=intervals(subset)))
    save(OUT/'audit.json',dict(status='passed',signature=sig,replayed_prediction_rows=replayed,
        recorded_new_cached_generation_calls=new_calls,reused_old_development_outputs=reused,
        additional_pixel_level_calls=16,fresh_output_hash_mismatches=fresh['mismatches'],
        repeat_consistency_verified=fresh['mismatches']==0,reference_rows_regenerated=rebuilt,
        frozen_V1_files=frozen[0],frozen_V4_files=frozen[1],training_proof=training_proof,
        pretraining_publication=prepare['commit'],test_seal_publication=pub['commit'],
        feature_audit_sha256=sha(OUT/'feature_audit.json'),audit_code_sha256=sha(Path(__file__)),
        runtime_amendment_sha256=sha(OUT/'runtime_amendment.json'),runtime_publication=runtime_pub['commit'],
        recorded_discarded_updates_replayed=runtime['recorded_updates_to_replay'],runtime_diagnostic_updates=2,
        scalar_replayed_updates_exact=replay['recorded_replayed_updates'],duplicate_raster_target_conflicts=0,
        coverage_sensitivity_publication=analysis_pub['commit'],coverage_sensitivity_cases=188,
        human_legibility_labels=False,physical_camera_validation=False))
    print('HP_AUDIT_PASSED',replayed,'new cached calls',new_calls,'reused',reused,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['features','audit']);a=p.parse_args()
    from research import vlm_train as trainer
    with trainer.process_lock():
        if a.action=='features':features()
        else:audit()
