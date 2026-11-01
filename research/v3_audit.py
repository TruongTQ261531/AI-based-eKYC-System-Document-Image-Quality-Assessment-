"""Replay both source-reference and body-reference evidence without changing outputs."""
import hashlib
import json
import math
import numpy as np
from research.v3_common import *
from research.v3_metrics import scoring,summary
from research.v3_study import MODELS,BASES

def intervals(records):
    sample=records['source_42']['rows'];ids=sorted({r['physical_id'] for r in sample});source={r['physical_id']:r['source'] for r in sample}
    rng=np.random.default_rng(20261102);draw=np.concatenate([rng.choice([i for i,p in enumerate(ids) if source[p]==s],(10000,24),replace=True) for s in ('authored','midv2020')],axis=1)
    values={}
    for key,record in records.items():
        a=np.array([[sum(r[f] for r in record['rows'] if r['physical_id']==p) for f in ('correct','reference','predicted')] for p in ids])
        a=a[draw].sum(axis=1);values[key]=2*a[:,0]/np.maximum(a[:,1]+a[:,2],1)
    pairs=[('source_42','partial_42'),('source_31415','partial_31415'),('source_42','control_42'),('source_42','v1')];result=[]
    for a,b in pairs:
        d=values[a]-values[b];result.append(dict(a=a,b=b,delta=records[a]['summary']['f1']-records[b]['summary']['f1'],
            ci95_low=float(np.percentile(d,2.5)),ci95_high=float(np.percentile(d,97.5))))
    return dict(seed=20261102,resamples=10000,method='Paired ID-cluster percentile bootstrap, source-stratified24+24',comparisons=result)

def audit():
    sig=signature();lock=read(OUT/'test_lock.json');pub=read(OUT/'lock_publication.json')
    if lock['signature']!=sig or pub['lock_sha256']!=sha(OUT/'test_lock.json') or pub['R2_lock_sha256']!=sha(R2OUT/'test_lock.json'):raise ValueError('Joint publication differs')
    if lock['cpu_source_sha256']!=sha(ROOT/'research/v3_cpu.py'):raise ValueError('Source CPU implementation changed after lock')
    if read(R2OUT/'audit.json')['status']!='passed':raise ValueError('Full R2 replay/cache audit required')
    preserve_v1();allrows=read(DATA/'samples.json');original=read(R2DATA/'samples.json')
    from research.v3_data import derive
    regenerated,public,stats,changes=derive()
    card=read(OUT/'dataset_card.json')
    if regenerated!=allrows or public!=read(OUT/'dataset_manifest.json') or stats!=card['source_stats'] or changes!=card['target_changes']:raise ValueError('Source reference derivation replay differs')
    if [(r['uid'],r['input_sha256'],r['path']) for r in allrows]!=[(r['uid'],r['input_sha256'],r['path']) for r in original]:raise ValueError('Source study changed pixels/order')
    samples={r['uid']:r for r in allrows};records={};replayed=0;CPU_repeats=0
    for seed0 in CONFIG['seeds']:
        r=read(OUT/f'train_source_{seed0}.json');paired=read(R2OUT/f'train_partial_{seed0}.json')
        if r['signature']!=sig or r['identity_slot_sequence_sha256']!=paired['identity_slot_sequence_sha256'] or r['steps']!=320 or r['presentations']!=1280:raise ValueError('Unmatched source supervision experiment')
        p=ROOT/r['selected_checkpoint'];complete=read(p/'complete.json')
        if complete['signature']!=sig or complete['step']!=320 or complete['cursor']!=1280:raise ValueError('Source checkpoint budget differs')
        for f,d in complete['sha256'].items():
            if sha(p/f)!=d:raise ValueError('Source checkpoint bytes changed')
        import torch
        from safetensors.torch import load_file
        state=torch.load(p/'training_state.pt',map_location='cpu',weights_only=True)
        if state['step']!=320 or state['cursor']!=1280 or len(state['optimizer']['state'])!=192:raise ValueError('Source optimizer budget differs')
        if any(int(v['step'])!=320 for v in state['optimizer']['state'].values()):raise ValueError('Source parameter optimizer steps differ')
        tensors=load_file(str(p/'adapter_model.safetensors'));b=[t for k,t in tensors.items() if 'lora_B' in k]
        if any(not bool(torch.isfinite(t).all()) for t in tensors.values()):raise ValueError('Nonfinite source adapter')
        if len(tensors)!=192 or len(b)!=96 or not all(bool(t.ne(0).any()) for t in b):raise ValueError('Source LoRA update proof incomplete')
        del state,tensors,b
        if any(not math.isfinite(e[k]) for e in r['events'] for k in ('loss','gradient_norm')):raise ValueError('Nonfinite source training')
    for role in ('development','test'):
        expected={r['uid'] for r in allrows if r['role']==role}
        for key in MODELS:
            record=read(OUT/f'{role}_{key}.json')
            if record['signature']!=sig or {r['uid'] for r in record['rows']}!=expected:raise ValueError('Missing source comparison cases')
            cache=R2CACHE if key in BASES else CACHE
            for row in record['rows']:
                private=read(cache/'predictions'/f'{role}_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json'))
                metrics,_=scoring(samples[row['uid']],private['_private_text'])
                if any(row[k]!=v for k,v in metrics.items()) or hashlib.sha256(private['_private_text'].encode()).hexdigest()!=row['prediction_sha256']:raise ValueError('Source raw replay differs')
                if row['model_sha256']!=lock['models'][key]['sha256'] or row['input_sha256']!=samples[row['uid']]['input_sha256']:raise ValueError('Source input/model hash differs')
                replayed+=1
            if summary(record['rows'])!=record['summary']:raise ValueError('Source summary differs')
            if role=='test':records[key]=record
        cpu=read(OUT/f'{role}_cpu.json')
        if cpu['signature']!=sig:raise ValueError('Source CPU signature differs')
        for name in cpu['summaries']:
            if {r['uid'] for r in cpu['rows'] if r['model']==name}!=expected:raise ValueError('Missing source CPU rows')
        for row in cpu['rows']:
            reader,policy=row['model'].split('/');private=read(CACHE/'cpu'/role/reader/policy/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json'))
            metrics,_=scoring(samples[row['uid']],private['_private_text'])
            if any(row[k]!=v for k,v in metrics.items()) or row['prediction_sha256']!=hashlib.sha256(private['_private_text'].encode()).hexdigest():raise ValueError('Source CPU replay differs')
            if policy=='body':
                previous=read(R2CACHE/'cpu'/role/reader/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json'))
                if previous['prediction_sha256']!=row['prediction_sha256']:raise ValueError('Repeated CPU body extraction changed on identical pixels')
                CPU_repeats+=1
            replayed+=1
    fresh=read(OUT/'fresh_repeats.json')
    if fresh['signature']!=sig or fresh['mismatches'] or fresh['additional_calls']!=16:raise ValueError('Source fresh repeat differs/incomplete')
    reference={r['uid']:r for r in records[fresh['model']]['rows']};pairs=set()
    for row in fresh['rows']:
        token=hashlib.sha256((row['uid']+'/'+str(row['repeat'])).encode()).hexdigest()
        private=read(CACHE/'fresh'/(token+'.json'));metrics,_=scoring(samples[row['uid']],private['_private_text'])
        digest=hashlib.sha256(private['_private_text'].encode()).hexdigest()
        if any(row[k]!=v for k,v in metrics.items()) or row['prediction_sha256']!=digest or reference[row['uid']]['prediction_sha256']!=digest:raise ValueError('Source fresh raw replay differs')
        if private['signature']!=sig or row['input_sha256']!=samples[row['uid']]['input_sha256']:raise ValueError('Source fresh input differs')
        pairs.add((row['uid'],row['repeat']))
    if len(pairs)!=16 or len({u for u,r in pairs})!=8 or {r for u,r in pairs}!={1,2}:raise ValueError('Source fresh coverage differs')
    save(OUT/'paired_intervals.json',intervals(records))
    save(OUT/'audit.json',dict(status='passed',signature=sig,replayed_prediction_rows=replayed,
        same_R2_image_bytes_and_order=True,effective_training_steps_per_run=320,train_presentations_per_run=1280,
        source_reference_rows_regenerated=len(regenerated),source_derivation_replay_is_not_independent_human_annotation=True,
        independently_repeated_CPU_outputs_verified=CPU_repeats,fresh_raw_rows_replayed=16,
        two_additional_source_seeds=CONFIG['seeds'],fresh_repeat_groups=8,fresh_repeat_mismatches=0,
        source_GT_is_geometric_not_human_legibility=True,both_model_locks_published_before_test=True,
        R2_audit_sha256=sha(R2OUT/'audit.json'),publication_commit=pub['commit'],audit_code_sha256=sha(ROOT/'research/v3_audit.py')))
    print('SOURCE_AUDIT_PASSED',replayed,flush=True)

if __name__=='__main__':audit()
