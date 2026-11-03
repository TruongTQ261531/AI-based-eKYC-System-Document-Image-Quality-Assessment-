"""Checkpoint, raw-output, pixel/feature and registered-statistics verification."""
import argparse
import hashlib
import json
import subprocess
import numpy as np
from PIL import Image
from research.fc_common import *
from research.hp_metrics import scoring, summary
from research.fc_io import save_retry as save


def data_audit():
    from research import hp_data as masks
    preserve();arms={a:train_rows(a) for a in ARMS};evaluation=eval_rows('development')+eval_rows('test')
    pixel_map={r['input_sha256']:r['pixel_sha256'] for r in read(OUT/'pixel_manifest.json')}
    labels={};unique={}
    for row in [r for values in arms.values() for r in values]+evaluation:
        if sha(ROOT/row['path'])!=row['input_sha256']:raise ValueError('Data raster changed')
        value=stable_hash(row['target']);pixel=pixel_map[row['input_sha256']]
        if pixel in labels and labels[pixel]!=value:raise ValueError('Identical decoded pixels have contradictory training/evaluation targets')
        labels[pixel]=value;unique.setdefault(row['input_sha256'],row)
    graphs={r['base']['physical_id']:r for r in read(HP_DATA/'base_graphs.json')}
    graphs.update({r['base']['physical_id']:r for r in read(DATA/'base_graphs.json')})
    new_rows=[r for r in arms['random'] if r['uid'].endswith('/fc-random')]
    new_rows+=eval_rows('test');checked=0
    for row in new_rows:
        graph=graphs[row['physical_id']];base,nodes=graph['base'],graph['nodes']
        image=masks.image_for(base)
        if row.get('pair_hidden_key'):
            expected,_,refs,_=masks.masked_capture(image,base,nodes,row['pair_hidden_key'],row['pair_kept_key'])
        else:
            actual='value_mask' if row['capture']=='pair_mask' else row['capture']
            expected,_=masks.augment(image,base['fields'],base['physical_id'],actual)
            H=np.eye(3)
            if row['capture']=='field_clip':H[1,2]=row['fields'][0]['quad'][0][1]-base['fields'][0]['quad'][0][1]
            refs=masks.refs_for(nodes,row['mask_regions'],row['width'],row['height'],H)
        with Image.open(ROOT/row['path']) as image:
            if not np.array_equal(np.asarray(image.convert('RGB')),expected):raise ValueError('Generated raster differs from deterministic reconstruction')
        if any(refs[k]!=row[k] for k in ('target','source_refs','source_evidence','masked_keys')):
            raise ValueError('Source-reference replay differs')
        checked+=1
        if checked%32==0:print('FC_RASTER_RECONSTRUCTION',checked,len(new_rows),flush=True)
    save(OUT/'data_audit.json',dict(status='passed',signature=signature(),unique_input_encodings=len(unique),
        identical_pixel_target_conflicts=0,reconstructed_new_rasters=checked,
        independent_human_annotation=False,scope='Generator and source-label consistency, not human legibility'))
    print('FC_DATA_AUDIT_PASSED',checked,flush=True)


def inventory():
    import torch
    from safetensors.torch import load_file
    from research.fc_study import adapter_for
    from research import vlm_train as trainer
    preserve();models={};exposure=read(OUT/'exposure_audit.json')
    for key in KEYS:
        arm,seed_text=key.rsplit('_',1);seed=int(seed_text);path,digest=adapter_for(key)
        folder=V3_OUT if arm=='uniform' else HP_OUT if arm=='hard' else OUT
        record=read(folder/(f'train_source_{seed}.json' if arm=='uniform' else f'train_{key}.json'))
        complete=read(path/'complete.json')
        if complete['step']!=320 or complete['cursor']!=1280 or complete['seed']!=seed:
            raise ValueError('Wrong checkpoint exposure')
        for name,value in complete['sha256'].items():
            if sha(path/name)!=value:raise ValueError('Checkpoint file bytes changed')
        state=torch.load(path/'training_state.pt',map_location='cpu',weights_only=True)
        if state['step']!=320 or state['cursor']!=1280 or state['seed']!=seed:
            raise ValueError('Optimizer state cursor differs')
        optimizer=state['optimizer']['state']
        if len(optimizer)!=192 or any(int(v['step'])!=320 for v in optimizer.values()):
            raise ValueError('LoRA optimizer steps differ')
        if any(not bool(torch.isfinite(t).all()) for v in optimizer.values() for t in v.values() if torch.is_tensor(t)):
            raise ValueError('Nonfinite optimizer state')
        tensors=load_file(str(path/'adapter_model.safetensors'));b=[t for k,t in tensors.items() if 'lora_B' in k]
        if len(tensors)!=192 or len(b)!=96 or not all(bool(t.ne(0).any()) for t in b):raise ValueError('Untrained LoRA adapter')
        if any(not bool(torch.isfinite(t).all()) for t in tensors.values()):raise ValueError('Nonfinite LoRA')
        config=read(path/'adapter_config.json')
        if config['r']!=8 or config['lora_alpha']!=16 or config['lora_dropout']!=0 or set(config['target_modules'])!={'q_proj','k_proj','v_proj','o_proj'}:
            raise ValueError('Unmatched trainable architecture')
        rows=train_rows(arm);sequence=[trainer.sampler(rows,seed,i) for i in range(1280)]
        order=stable_hash([r['physical_id']+'/'+str(r['slot']) for r in sequence])
        pixels=stable_hash([r['input_sha256'] for r in sequence])
        if order!=record['identity_slot_sequence_sha256'] or pixels!=record['pixel_sequence_sha256']:
            raise ValueError('Training sequence differs from the frozen record')
        if record['token_exposure']['answer_loss_tokens']!=exposure[arm]['answer_loss_tokens']:
            raise ValueError('Actual training token exposure differs')
        events=record['events']
        if [e['step'] for e in events]!=list(range(1,321)) or any(not np.isfinite(e[f]) for e in events for f in ('loss','gradient_norm')):
            raise ValueError('Incomplete or nonfinite training event log')
        models[key]=dict(arm=arm,seed=seed,steps=320,presentations=1280,adapter_sha256=digest,
            checkpoint_hashes={name:sha(path/name) for name in ('complete.json','training_state.pt','adapter_model.safetensors','adapter_config.json')},
            identity_slot_sequence_sha256=order,pixel_sequence_sha256=pixels,
            token_exposure=record['token_exposure'],nonzero_B_tensors=96,optimizer_states=192,
            historical_training=arm in ('uniform','hard'))
        del tensors,b,state,optimizer
    for seed in SEEDS:
        group=[models[f'{a}_{seed}'] for a in ('hard','random','repeat')]
        if len({r['token_exposure']['input_and_answer_tokens'] for r in group})!=1:
            raise ValueError('Primary total input/answer token exposure differs')
        if len({r['identity_slot_sequence_sha256'] for r in group})!=1:raise ValueError('Primary ID/slot orders differ')
    save(OUT/'training_state_inventory.json',dict(status='passed',signature=signature(),models=models,new_runs=4,historical_runs=4,
        frozen_final320=True,global_primary_tokens_matched=True,per_step_tokens_or_FLOPs_matched=False))
    print('FC_EIGHT_CHECKPOINTS_VERIFIED',flush=True)


def features():
    import torch
    from research.fc_study import configure
    from research.v2_inputs import pixels
    model,trainer=configure()
    rows=eval_rows('development')+eval_rows('test')+[r for a in ARMS for r in train_rows(a)]
    unique={r['input_sha256']:r for r in rows};proof=[]
    for i,row in enumerate(unique.values(),1):
        if sha(ROOT/row['path'])!=row['input_sha256']:raise ValueError('Feature input bytes changed')
        cached=model.features(row)
        with Image.open(ROOT/row['path']) as image:view,_=model.views.prepare(image,'rect2')
        tensor=pixels(view,'rect2').to(device='cuda',dtype=model.dtype)
        with torch.no_grad():fresh=model.model.extract_feature(tensor).detach().cpu().contiguous()
        if not torch.equal(cached,fresh):raise ValueError('Fresh visual features differ from cache')
        token=hashlib.sha256((model.input_version+row['input_sha256']).encode()).hexdigest()
        path=CACHE/'features/rect2'/(token+'.safetensors')
        proof.append(dict(input_sha256=row['input_sha256'],feature_sha256=sha(path)))
        if i%32==0 or i==len(unique):trainer.progress(stage='fair_control_feature_audit',complete=i,total=len(unique))
    save(OUT/'feature_audit.json',dict(status='passed',signature=signature(),freshly_reextracted_features=len(proof),mismatches=0,rows=proof))


def audit():
    from research.fc_study import adapter_for,verify_test
    from research.fc_statistics import analyze
    frozen=preserve();sig=signature();lock=verify_test();prepare=read(OUT/'prepare_publication.json');pub=read(OUT/'test_publication.json')
    subprocess.run(['git','merge-base','--is-ancestor',prepare['commit'],pub['commit']],cwd=ROOT,check=True)
    io_recoveries=[]
    if (OUT/'io_recovery.json').exists():
        recovery=read(OUT/'io_recovery.json');publication=read(OUT/'io_publication.json')
        if recovery['signature']!=sig or publication['signature']!=sig or publication['recovery_sha256']!=sha(OUT/'io_recovery.json'):
            raise ValueError('I/O recovery publication differs')
        subprocess.run(['git','merge-base','--is-ancestor',publication['commit'],pub['commit']],cwd=ROOT,check=True)
        retained=[]
        for row in eval_rows('development')[:recovery['retained_generation_outputs']]:
            path=CACHE/'predictions/development_repeat_42'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
            retained.append(path)
        digest=stable_hash([{p.name:sha(p)} for p in sorted(retained)])
        if digest!=recovery['retained_outputs_digest']:raise ValueError('Retained pre-interruption outputs changed')
        for name in ('fc_io.py','fc_runner.py'):
            raw=subprocess.check_output(['git','show',pub['commit']+':research/'+name],cwd=ROOT)
            if hashlib.sha256(raw).hexdigest()!=sha(ROOT/'research'/name):raise ValueError('Pretest I/O runner differs')
        io_recoveries.append(dict(publication=publication['commit'],retained_outputs=recovery['retained_generation_outputs'],
            weights_or_data_changed=False,retrained_runs=0,scope='Metadata file locking, not failed OCR/model inference'))
    names=('fc_common.py','fc_data.py','fc_acquire.py','fc_study.py','fc_statistics.py','fc_preflight.py','FAIR_CONTROLS_PROTOCOL.md')
    for name in names:
        raw=subprocess.check_output(['git','show',prepare['commit']+':research/'+name],cwd=ROOT)
        if hashlib.sha256(raw).hexdigest()!=sha(ROOT/'research'/name):raise ValueError('Pretraining source bytes differ')
    for name in ('analysis_plan.json','training_state_inventory.json'):
        raw=subprocess.check_output(['git','show',pub['commit']+':research/results/fair_controls_v1/'+name],cwd=ROOT)
        if hashlib.sha256(raw).hexdigest()!=sha(OUT/name):raise ValueError('Pretest analysis/checkpoint inventory changed')
    for name in ('data_audit.json','feature_audit.json','training_state_inventory.json'):
        value=read(OUT/name)
        if value['status']!='passed' or value['signature']!=sig:raise ValueError('Matching component audit missing')
    for key,info in read(OUT/'training_state_inventory.json')['models'].items():
        path,digest=adapter_for(key)
        if digest!=info['adapter_sha256'] or digest!=lock['models'][key]['sha256']:raise ValueError('Model differs from seal')
        if any(sha(path/name)!=h for name,h in info['checkpoint_hashes'].items()):raise ValueError('Checkpoint changed after pretest inventory')
    samples={r['uid']:r for r in eval_rows('development')+eval_rows('test')}
    pixel_map={r['input_sha256']:r['pixel_sha256'] for r in read(OUT/'pixel_manifest.json')}
    replayed=0;new=0;reused=0;records={}
    for role in ('development','test'):
        expected={r['uid'] for r in eval_rows(role)}
        for key in KEYS:
            record=read(OUT/f'{role}_{key}.json')
            if record['signature']!=sig or len(record['rows'])!=len(expected) or {r['uid'] for r in record['rows']}!=expected:
                raise ValueError('Missing/duplicate evaluation cases')
            for row in record['rows']:
                dest=CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
                raw=read(dest);sample=samples[row['uid']];metrics,_=scoring(sample,raw['_private_text'])
                if raw['signature']!=sig or row['model_sha256']!=lock['models'][key]['sha256'] or raw['model_sha256']!=row['model_sha256']:
                    raise ValueError('Raw model contract differs')
                if raw['input_sha256']!=sample['input_sha256'] or row['input_sha256']!=sample['input_sha256'] or row['pixel_sha256']!=pixel_map[sample['input_sha256']]:
                    raise ValueError('Raw input contract differs')
                if any(row[k]!=v for k,v in metrics.items()) or row['prediction_sha256']!=hashlib.sha256(raw['_private_text'].encode()).hexdigest():
                    raise ValueError('Raw score replay differs')
                if row['reused_historical_development']:
                    if role!='development' or key.split('_')[0] not in ('uniform','hard'):raise ValueError('Illegitimate reuse')
                    previous=read(HP_CACHE/'predictions'/f'development_{key}'/dest.name)
                    if previous['_private_text']!=raw['_private_text']:raise ValueError('Reused raw output changed')
                    reused+=1
                else:new+=1
                replayed+=1
            if summary(record['rows'])!=record['summary']:raise ValueError('Public summary changed')
            if role=='test':records[key]=record
    fresh_calls=0;fresh_mismatches=0
    for key in KEYS:
        record=read(OUT/f'fresh_{key}.json');test={r['uid']:r for r in records[key]['rows']};pairs=set()
        if record['signature']!=sig:raise ValueError('Fresh signature differs')
        for row in record['rows']:
            dest=CACHE/'fresh'/key/(hashlib.sha256((row['uid']+'/'+str(row['repeat'])).encode()).hexdigest()+'.json')
            raw=read(dest);metrics,_=scoring(samples[row['uid']],raw['_private_text'])
            if raw['signature']!=sig or raw['model_sha256']!=lock['models'][key]['sha256'] or raw['input_sha256']!=samples[row['uid']]['input_sha256']:
                raise ValueError('Fresh model/input contract differs')
            if any(row[k]!=v for k,v in metrics.items()) or row['prediction_sha256']!=hashlib.sha256(raw['_private_text'].encode()).hexdigest():
                raise ValueError('Fresh raw-score replay differs')
            if row['identical_to_test']!=(row['prediction_sha256']==test[row['uid']]['prediction_sha256']):raise ValueError('Fresh consistency flag differs')
            pairs.add((row['uid'],row['repeat']));fresh_mismatches+=not row['identical_to_test'];fresh_calls+=1
        if len(pairs)!=8 or len({u for u,r in pairs})!=4 or {r for u,r in pairs}!={1,2}:raise ValueError('Incomplete fresh panel')
        if record['mismatches']!=sum(not r['identical_to_test'] for r in record['rows']):raise ValueError('Fresh mismatch count differs')
    if replayed!=2304 or fresh_calls!=64:raise ValueError('Registered evaluation coverage not complete')
    main=analyze(records);joined=analyze(records,joined=True,permutations=False)
    save(OUT/'paired_statistics.json',main);save(OUT/'pixel_cluster_sensitivity.json',joined)
    slices=[]
    for key,record in records.items():
        for axis in ('source','capture','device','layout'):
            for value in sorted({r[axis] for r in record['rows']}):
                chosen=[r for r in record['rows'] if r[axis]==value]
                slices.append(dict(model=key,axis=axis,value=value,summary=summary(chosen)))
    save(OUT/'slices.json',slices)
    excluded=set(read(OUT/'analysis_plan.json')['supplementary_excluded_document_instances']);subset={}
    for key,record in records.items():
        chosen=[r for r in record['rows'] if r['physical_id'] not in excluded]
        if len(chosen)!=192-4*len(excluded):raise ValueError('Coverage sensitivity cases differ')
        subset[key]=dict(rows=chosen,summary=summary(chosen))
    save(OUT/'source_coverage_sensitivity.json',dict(excluded_ids=sorted(excluded),primary_cases_retained=True,
        new_model_calls=0,summaries={k:r['summary'] for k,r in subset.items()},intervals=analyze(subset,permutations=False)))
    replays=[]
    for key in KEYS:
        if key.split('_')[0] not in NEW_ARMS:continue
        for path in (CACHE/'training'/key).glob('discarded_after_*.json'):
            data=read(path);step=int(path.name.split('_')[2]);replays.append(dict(model=key,backup_sha256=sha(path),discarded_logged_updates=sum(r['step']>step for r in data)))
    save(OUT/'audit.json',dict(status='passed',signature=sig,replayed_score_rows=replayed,
        new_cached_generation_calls=new,reused_development_outputs=reused,additional_pixel_level_calls=fresh_calls,
        fresh_output_hash_mismatches=fresh_mismatches,exact_repeat_consistency=fresh_mismatches==0,
        probe_calls=read(OUT/'runtime_choice.json')['new_model_calls'],new_training_runs=4,reused_training_runs=4,
        pretraining_publication=prepare['commit'],pretest_publication=pub['commit'],
        primary_family_size=4,bootstrap_resamples=10000,permutation_resamples=10000,
        statistical_code_sha256=sha(ROOT/'research/fc_statistics.py'),audit_code_sha256=sha(ROOT/'research/fc_audit.py'),
        frozen_V1_files=frozen[0],frozen_V4_files=frozen[1],frozen_HP_files=len(read(OUT/'previous_artifacts.json')['files']),
        discarded_update_records=replays,io_recoveries=io_recoveries,
        recorded_worker_failures=[dict(file=p.name,sha256=sha(p),action=read(p)['action'],error_type=read(p)['error_type']) for p in sorted(CACHE.glob('failure_*.json'))],
        human_legibility_annotations=0,physical_camera_validation=False,model_promoted=False))
    print('FC_AUDIT_PASSED',replayed,'new_cached',new,'reused',reused,'fresh',fresh_calls,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['data','inventory','features','audit']);a=p.parse_args()
    if a.action=='data':data_audit()
    else:
        from research import vlm_train as trainer
        from research.fc_io import save_retry
        trainer.save=save_retry
        with trainer.process_lock():
            if a.action=='inventory':inventory()
            elif a.action=='features':features()
            else:audit()
