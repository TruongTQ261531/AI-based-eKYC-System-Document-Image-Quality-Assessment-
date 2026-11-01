"""Independent raw-output replay, paired cluster intervals and fresh repeat checks."""
import argparse
import collections
import hashlib
import math
import time
from pathlib import Path
import numpy as np
from research.v2_common import *
from research.v2_runtime import scoring,summary

MODELS=('original','v1','control_42','partial_42','control_31415','partial_31415')

def fresh():
    import torch
    from peft import PeftModel
    from PIL import Image
    from research.v2_runtime import VLM
    from research.vlm_train import process_lock
    from research.v2_study import panel,adapter_for
    lock=read(OUT/'test_lock.json');key=lock['selected_model'];path,_=adapter_for(key)
    with process_lock():
        model=VLM(42,lock['profile']);model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
        results=[]
        for r in panel('test',4):
            cached=read(CACHE/'predictions'/('test_'+key)/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json'))
            for repeat in (1,2):
                private=CACHE/'fresh'/key/(hashlib.sha256((r['uid']+'/'+str(repeat)).encode()).hexdigest()+'.json')
                if private.exists():
                    record=read(private)
                    if record['signature']!=signature() or record['input_sha256']!=r['input_sha256']:raise ValueError('Fresh repeat source changed')
                else:
                    torch.cuda.reset_peak_memory_stats()
                    with Image.open(ROOT/r['path']) as im:prediction=model.fresh(im)
                    metrics,_=scoring(r,prediction['text'])
                    record=dict(signature=signature(),uid=r['uid'],physical_id=r['physical_id'],source=r['source'],
                        input_sha256=r['input_sha256'],repeat=repeat,**metrics,**{k:v for k,v in prediction.items() if k!='text'},
                        _private_text=prediction['text'],prediction_sha256=hashlib.sha256(prediction['text'].encode()).hexdigest(),
                        cached_generation_identical=hashlib.sha256(prediction['text'].encode()).hexdigest()==cached['prediction_sha256'],
                        peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
                    save(private,record)
                results.append({k:v for k,v in record.items() if not k.startswith('_private')})
                print('V2_FRESH',len(results),16,flush=True)
        save(OUT/'fresh_repeats.json',dict(signature=signature(),model=key,inputs=8,identities=4,additional_fresh_calls=16,
            same_input_generation_count_including_first_cached=3,model_cold_load_seconds=model.cold_load_seconds,
            mismatch_count=sum(not r['cached_generation_identical'] for r in results),
            fresh_seconds_p50=float(np.percentile([r['wall_seconds'] for r in results],50)),
            fresh_seconds_p95=float(np.percentile([r['wall_seconds'] for r in results],95)),rows=results))

def intervals(records):
    ids=sorted({r['physical_id'] for r in records['partial_42']['rows']});source={r['physical_id']:r['source'] for r in records['partial_42']['rows']}
    rng=np.random.default_rng(20261101);draws=[]
    for s in ('authored','midv2020'):
        indices=np.array([i for i,pid in enumerate(ids) if source[pid]==s]);draws.append(rng.choice(indices,(10000,len(indices)),replace=True))
    draws=np.concatenate(draws,axis=1);sums={}
    for name,record in records.items():
        arr=np.array([[sum(r[k] for r in record['rows'] if r['physical_id']==pid) for k in ('correct','reference','predicted')] for pid in ids])
        sampled=arr[draws].sum(axis=1);sums[name]=2*sampled[:,0]/np.maximum(sampled[:,1]+sampled[:,2],1)
    comparisons=[]
    for a,b in [('partial_42','control_42'),('partial_31415','control_31415'),('partial_42','v1'),('partial_42','original')]:
        delta=sums[a]-sums[b]
        comparisons.append(dict(a=a,b=b,delta_f1=records[a]['summary']['f1']-records[b]['summary']['f1'],
            ci95_low=float(np.percentile(delta,2.5)),ci95_high=float(np.percentile(delta,97.5))))
    return dict(method='Paired identity-cluster percentile bootstrap; source-stratified 24 authored+24 photo IDs',
                resamples=10000,seed=20261101,comparisons=comparisons,independent_units=48)

def audit():
    sig=signature();lock=read(OUT/'test_lock.json');publication=read(OUT/'lock_publication.json')
    if lock['signature']!=sig or publication['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('Published source lock mismatch')
    if lock['cpu_source_sha256']!=sha(ROOT/'research/v2_cpu.py'):raise ValueError('CPU baseline source changed after lock')
    frozen=preserve_v1();samples={r['uid']:r for r in read(DATA/'samples.json')};checked_images=set()
    old_index=read(ROOT/'research/results/recovery_v4/artifact_index.json')
    for item in old_index['files']:
        if sha(ROOT/item['path'])!=item['sha256']:raise ValueError('Frozen V4 artifact changed')
    for r in samples.values():
        if r['path'] not in checked_images:
            if sha(ROOT/r['path'])!=r['input_sha256']:raise ValueError('Benchmark raster changed')
            checked_images.add(r['path'])
    for source in read(DATA/'sources.json'):
        if sha(ROOT/source['path'])!=source['source_sha256']:raise ValueError('Author source image changed')
    train=[]
    for seed0 in CONFIG['seeds']:
        a=read(OUT/f'train_control_{seed0}.json');b=read(OUT/f'train_partial_{seed0}.json')
        if a['identity_slot_sequence_sha256']!=b['identity_slot_sequence_sha256']:raise ValueError('Unmatched exposure/order')
        for arm,r in [('control',a),('partial',b)]:
            if r['signature']!=sig or r['steps']!=320 or r['presentations']!=1280 or r['identities']!=128:raise ValueError('Training budget mismatch')
            accepted={e['step']:e for e in r['events']}
            if sorted(accepted)!=list(range(1,321)):raise ValueError('Training step continuity differs')
            if not all(math.isfinite(e[k]) for e in r['events'] for k in ('loss','gradient_norm')):raise ValueError('Nonfinite training')
            if sha(ROOT/r['selected_checkpoint']/'adapter_model.safetensors')!=r['selected_adapter_sha256']:raise ValueError('Adapter bytes changed')
            checkpoint=ROOT/r['selected_checkpoint'];complete=read(checkpoint/'complete.json')
            if complete['signature']!=sig or complete['step']!=320 or complete['cursor']!=1280:raise ValueError('Checkpoint budget/contract differs')
            for name,digest in complete['sha256'].items():
                if sha(checkpoint/name)!=digest:raise ValueError('Checkpoint state changed')
            import torch
            state=torch.load(checkpoint/'training_state.pt',map_location='cpu',weights_only=True)
            if state['step']!=320 or state['cursor']!=1280 or len(state['optimizer']['state'])!=192:raise ValueError('Optimizer state does not show complete LoRA training')
            if any(int(v['step'])!=320 for v in state['optimizer']['state'].values()):raise ValueError('Optimizer parameter steps differ')
            from safetensors.torch import load_file
            tensors=load_file(str(checkpoint/'adapter_model.safetensors'))
            if any(not bool(torch.isfinite(t).all()) for t in tensors.values()):raise ValueError('Nonfinite adapter')
            b=[t for k,t in tensors.items() if 'lora_B' in k]
            if len(tensors)!=192 or len(b)!=96 or not all(bool(t.ne(0).any()) for t in b):raise ValueError('No complete adapter update evidence')
            train.append(dict(arm=arm,seed=seed0,presentations=1280,identity_slot_sequence_sha256=r['identity_slot_sequence_sha256'],
                train_seconds=r['events'][-1]['wall_seconds'],max_allocated_bytes=max(e['peak_allocated_bytes'] for e in r['events']),
                max_reserved_bytes=max(e['peak_reserved_bytes'] for e in r['events'])))
            train[-1]['token_exposure']=r['token_exposure']
            train[-1].update(adapter_tensors=192,nonzero_lora_B_tensors=96,optimizer_steps_verified=320)
            train[-1].update(attempted_optimizer_events=len(r['events']),rollback_replayed_events=len(r['events'])-320,
                event_policy='Retain all attempts; latest event per global step belongs to the restored/final optimizer trajectory')
            del state,tensors,b
    replayed=0;tests={}
    for role in ('development','test'):
        expected={r['uid'] for r in samples.values() if r['role']==role}
        for key in MODELS:
            record=read(OUT/f'{role}_{key}.json')
            if record['signature']!=sig or {r['uid'] for r in record['rows']}!=expected:raise ValueError('Missing/changed model results')
            for r in record['rows']:
                p=read(CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json'))
                if p['signature']!=sig or p['model_sha256']!=lock['models'][key]['sha256'] or p['input_sha256']!=samples[r['uid']]['input_sha256']:
                    raise ValueError('Private prediction input/model/source hash mismatch')
                if r['prediction_sha256']!=p['prediction_sha256']:raise ValueError('Public/private prediction hash differs')
                metrics,_=scoring(samples[r['uid']],p['_private_text'])
                if any(r[k]!=v for k,v in metrics.items()) or p['prediction_sha256']!=hashlib.sha256(p['_private_text'].encode()).hexdigest():raise ValueError('Raw prediction replay differs')
                replayed+=1
            if summary(record['rows'])!=record['summary']:raise ValueError('Published summary differs')
            if role=='test':tests[key]=record
        cpu=read(OUT/f'{role}_cpu.json')
        if cpu['signature']!=sig or cpu['profile']!=lock['profile']:raise ValueError('CPU signature/profile changed')
        for reader in ('rapid_v4','rapid_latin_v5'):
            if {r['uid'] for r in cpu['rows'] if r['model']==reader}!=expected:raise ValueError('Incomplete CPU comparison')
        for r in cpu['rows']:
            p=read(CACHE/'cpu'/role/r['model']/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json'))
            if p['signature']!=sig or p['input_sha256']!=samples[r['uid']]['input_sha256'] or r['prediction_sha256']!=hashlib.sha256(p['_private_text'].encode()).hexdigest():
                raise ValueError('CPU public/private/input provenance mismatch')
            metrics,_=scoring(samples[r['uid']],p['_private_text'])
            if any(r[k]!=v for k,v in metrics.items()):raise ValueError('CPU raw replay differs')
            replayed+=1
    repeats=read(OUT/'fresh_repeats.json')
    if repeats['signature']!=sig or repeats['mismatch_count']!=0 or repeats['additional_fresh_calls']!=16:raise ValueError('Fresh repeat mismatch/incomplete')
    save(OUT/'paired_intervals.json',intervals(tests))
    result=dict(status='passed',signature=sig,frozen_v1_files_unchanged=frozen,unique_rasters_hashed=len(checked_images),
        frozen_v4_files_unchanged=len(old_index['files']),
        original_photo_sources_hashed=64,raw_output_rows_replayed=replayed,training=train,
        fresh_repeat_groups=8,fresh_repeat_mismatches=0,model_count=6,test_inputs=144,test_identities=48,
        test_lock_publication_commit=publication['commit'],human_annotation_replaced_by_audit=False,
        limitations=['Geometric visibility proxy, not human legibility GT','Only mock documents; no new real-person collection',
                     'Two seeds and 48 test identities are limited evidence','Model pretraining overlap with MIDV is unknown'])
    save(OUT/'audit.json',result);print('V2_AUDIT_PASSED',replayed,flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fresh','audit']);a=p.parse_args()
    try:fresh() if a.action=='fresh' else audit()
    except Exception as exc:
        save(OUT/'audit_failure.json',dict(action=a.action,type=type(exc).__name__,detail=str(exc)))
        raise

if __name__=='__main__':main()
