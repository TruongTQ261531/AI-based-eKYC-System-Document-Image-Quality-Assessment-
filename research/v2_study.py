"""Resumable V2 input comparison, paired training, locked evaluation and export."""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import time
import torch
from research.v2_common import *
from research.v2_runtime import VLM,scoring,summary
from research.v2_inputs import PROFILES
from research import vlm_train as trainer

def configure_training(sig=None):
    trainer.CACHE=CACHE;trainer.OUT=OUT;trainer.CONFIG=CONFIG
    trainer.signature=(lambda:sig) if sig else signature

def feature_all(model,rows):
    start=time.perf_counter()
    for i,r in enumerate(rows,1):
        model.features(r)
        if i%32==0 or i==len(rows):trainer.progress(stage='features',profile=model.profile,complete=i,total=len(rows))
    return time.perf_counter()-start

def panel(role,identities):
    rows=load(role);chosen=set()
    for source in ('authored','midv2020'):
        ids=sorted({r['physical_id'] for r in rows if r['source']==source},key=lambda x:hashlib.sha256(('v2-panel/'+x).encode()).digest())[:identities//2]
        chosen.update(ids)
    return [r for r in rows if r['physical_id'] in chosen and r['capture'] in ('full','field_clip')]

def probe(profile):
    configure_training('v2-feasibility/'+sha(ROOT/'research/v2_runtime.py')+'/'+profile)
    model=VLM(42,profile);rows=[]
    from research.v2_data import mock,target
    from PIL import Image
    for i in range(4):
        image,fields,_,_=mock('vlm_v2/probe/'+str(i),i,'train')
        path=DATA/'probe_images'/f'{i}.png';path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(image).save(path)
        rows.append(dict(path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),target=target(fields,1200,800)))
    feature_all(model,rows);model.offload_vision();model.lora(CONFIG)
    from peft import get_peft_model_state_dict
    before={k:v.detach().cpu().clone() for k,v in get_peft_model_state_dict(model.model.language_model).items()}
    events,_=trainer.train_steps(model,rows,[],42,4,1,CACHE/'probe'/profile,save_every=2)
    continuous={k:v.detach().cpu().clone() for k,v in get_peft_model_state_dict(model.model.language_model).items()}
    trainer.train_steps(model,rows,[],42,4,1,CACHE/'probe_resume'/profile,start_state=CACHE/'probe'/profile/'step_0002',save_every=2)
    resumed=get_peft_model_state_dict(model.model.language_model)
    difference=max(float((continuous[k]-v.detach().cpu()).abs().max()) for k,v in resumed.items())
    changed=sum(not torch.equal(before[k],v) for k,v in continuous.items())
    if not changed or difference:raise ValueError('V2 optimizer/resume smoke failed')
    save(OUT/f'probe_{profile}.json',dict(eligible=True,profile=profile,steps=4,changed_adapter_tensors=changed,
         resume_max_abs_difference=difference,events=events,scope='four separate authored smoke inputs, one-microbatch backward; main uses accumulation four'))

def compare_inputs(profile):
    rows=panel('development',8);model=VLM(42,profile);records=[]
    folder=CACHE/'input_panel'/profile
    for i,r in enumerate(rows,1):
        path=folder/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json')
        contract=stable_hash(dict(input_sha256=r['input_sha256'],prompt=PROMPT,input_code=model.input_version))
        prior=PILOT_CACHE/'input_panel'/profile/path.name
        if not path.exists() and prior.exists() and read(prior)['contract']==contract:
            save(path,dict(read(prior),reused_original_prediction_from_pilot=True))
        if path.exists():
            pred=read(path)
            if pred['contract']!=contract:raise ValueError('Input comparison source changed')
        else:
            from PIL import Image
            with Image.open(ROOT/r['path']) as im: pred=model.fresh(im)
            save(path,dict(pred,contract=contract))
        metrics,_=scoring(r,pred['text'])
        records.append(dict(uid=r['uid'],physical_id=r['physical_id'],source=r['source'],capture=r['capture'],
            **metrics,wall_seconds=pred['wall_seconds'],view_mode=pred['view_mode'],hit_token_limit=pred['generated_tokens']>=384,
            reused_original_prediction_from_pilot=pred.get('reused_original_prediction_from_pilot',False)))
        trainer.progress(stage='input_panel',profile=profile,complete=i,total=len(rows))
    save(OUT/f'input_panel_{profile}.json',dict(profile=profile,summary=summary(records),rows=records,
         mean_fresh_seconds=sum(r['wall_seconds'] for r in records)/len(records)))

def choose_inputs():
    records=[read(OUT/f'input_panel_{p}.json') for p in PROFILES]
    # Re-score persisted raw predictions with ONE final metric implementation,
    # even if a development-only scoring correction was made during the panel.
    samples={r['uid']:r for r in panel('development',8)}
    for record in records:
        for row in record['rows']:
            path=CACHE/'input_panel'/record['profile']/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
            metrics,_=scoring(samples[row['uid']],read(path)['text']);row.update(metrics)
        record['summary']=summary(record['rows']);record['metric_sha256']=sha(ROOT/'research/v2_metrics.py')
        save(OUT/f"input_panel_{record['profile']}.json",record)
    # The early smoke has short authored answers. Also test actual longest
    # training answers before declaring a tile budget feasible on this GPU.
    for profile in ('raw2','raw4'):
        path=OUT/f'probe_long_{profile}.json'
        if not path.exists():
            import gc
            model=None
            try:
                configure_training('v2-long-training-only/'+profile+'/'+sha(ROOT/'research/v2_study.py'))
                model=VLM(42,profile);pool=load('train','control')+load('train','partial')
                ranked=sorted(pool,key=lambda r:int(model.tokens(r['target'])[0].numel()),reverse=True)
                chosen=[];seen=set()
                for row in ranked:
                    if row['physical_id'] not in seen:chosen.append(row);seen.add(row['physical_id'])
                    if len(chosen)==4:break
                feature_all(model,chosen);model.offload_vision();model.lora(CONFIG)
                events,_=trainer.train_steps(model,chosen,[],42,1,4,CACHE/'probe_long'/profile,save_every=1)
                save(path,dict(eligible=True,profile=profile,gradient_accumulation=4,events=events,
                     training_only_source_ids=[r['physical_id'] for r in chosen],test_used=False))
            except torch.cuda.OutOfMemoryError as exc:
                save(path,dict(eligible=False,profile=profile,error_type=type(exc).__name__,detail=str(exc),
                              test_used=False,no_silent_batch_change=True))
            finally:
                del model;gc.collect();torch.cuda.empty_cache()
        probe=read(OUT/f'probe_raw{profile[-1]}.json');probe['long_answer_eligible']=read(path)['eligible']
        probe['eligible']=probe['eligible'] and read(path)['eligible'];save(OUT/f'probe_{profile}.json',probe)
    eligible=[r for r in records if read(OUT/f"probe_raw{r['profile'][-1]}.json")['eligible']]
    choice=max(eligible,key=lambda r:(r['summary']['f1'],-r['summary']['unsupported_nonempty'],-r['mean_fresh_seconds']))
    save(OUT/'input_choice.json',dict(profile=choice['profile'],development_panel_ids=8,development_inputs=16,
        chosen_by='Highest tolerant KV F1, then fewer unsupported nonempty outputs, then lower fresh time',
        comparisons=[{k:r[k] for k in ('profile','summary','mean_fresh_seconds')} for r in records],test_used=False))
    print('V2_INPUT_CHOICE',choice['profile'],flush=True)

def train(variant,seed0):
    preserve_v1()
    if (OUT/'test_lock.json').exists():raise ValueError('V2 test already sealed; do not retrain')
    configure_training();profile=read(OUT/'input_choice.json')['profile'];rows=load('train',variant)
    model=VLM(seed0,profile);dev=panel('development',4)
    token_lengths=[model.tokens(r['target']) for r in rows]
    token_exposure=dict(input_and_answer_tokens=2*sum(int(ids.numel()) for ids,_ in token_lengths),
                        answer_loss_tokens=2*sum(int(labels.ne(-100).sum()) for _,labels in token_lengths),
                        scope='Exactly two epochs of the paired 640 slots; answer lengths can differ between arms')
    del token_lengths
    setup=feature_all(model,rows+dev);model.offload_vision();model.lora(CONFIG)
    folder=CACHE/'training'/f'{variant}_{seed0}'
    existing=sorted(p for p in folder.glob('step_*') if (p/'complete.json').exists())
    resume=existing[-1] if existing else None
    events,_=trainer.train_steps(model,rows,dev,seed0,CONFIG['steps'],4,folder,start_state=resume,save_every=80)
    checkpoint=folder/'step_0320'
    if not (checkpoint/'complete.json').exists():raise ValueError('Matched final checkpoint missing')
    all_events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    ids=[trainer.sampler(rows,seed0,i)['physical_id'] for i in range(1280)]
    slots=[trainer.sampler(rows,seed0,i)['physical_id']+'/'+str(trainer.sampler(rows,seed0,i)['slot']) for i in range(1280)]
    save(OUT/f'train_{variant}_{seed0}.json',dict(signature=signature(),variant=variant,seed=seed0,
        selected_checkpoint=checkpoint.relative_to(ROOT).as_posix(),selected_adapter_sha256=sha(checkpoint/'adapter_model.safetensors'),
        selection_rule='Fixed final step320 for every arm/seed; no arm-specific early stopping',
        feature_setup_seconds=setup,events=all_events,identities=len(set(ids)),presentations=1280,
        identity_sequence_sha256=stable_hash(ids),identity_slot_sequence_sha256=stable_hash(slots),
        steps=320,train_rasters=len({r['input_sha256'] for r in rows}),resumed_from=str(resume) if resume else None))
    record=read(OUT/f'train_{variant}_{seed0}.json');record['token_exposure']=token_exposure
    save(OUT/f'train_{variant}_{seed0}.json',record)

def adapter_for(key):
    if key=='original':return None,read(ROOT/'research/results/vlm_lora_v1/training_environment.json')['model_sha256']
    if key=='v1':
        record=read(ROOT/'research/results/vlm_lora_v1/train_seed_42.json')
    else:record=read(OUT/f'train_{key}.json')
    path=ROOT/record['selected_checkpoint'];digest=sha(path/'adapter_model.safetensors')
    if digest!=record['selected_adapter_sha256']:raise ValueError('Adapter changed')
    if key!='v1' and record['signature']!=signature():raise ValueError('V2 trained source changed')
    return path,digest

def evaluate(role,key):
    profile=read(OUT/'input_choice.json')['profile'];adapter,digest=adapter_for(key);sig=signature()
    if role=='test':
        lock=read(OUT/'test_lock.json')
        if lock['signature']!=sig or lock['models'][key]['sha256']!=digest:raise ValueError('Pre-test lock mismatch')
        publication=read(OUT/'lock_publication.json')
        if publication['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('Published seal differs from local seal')
    model=VLM(42,profile);rows=load(role);feature_all(model,rows);model.offload_vision()
    if adapter:
        from peft import PeftModel
        model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(adapter),is_trainable=False)
    results=[]
    for i,r in enumerate(rows,1):
        path=CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json')
        if path.exists():
            record=read(path)
            if record['signature']!=sig or record['input_sha256']!=r['input_sha256'] or record['model_sha256']!=digest:raise ValueError('Prediction cache differs')
        else:
            pred=model.infer(r);metrics,_=scoring(r,pred['text'])
            record=dict(signature=sig,model_sha256=digest,input_sha256=r['input_sha256'],uid=r['uid'],
                physical_id=r['physical_id'],source=r['source'],device=r['device'],layout=r['layout'],
                held_layout=r.get('held_layout',False),capture=r['capture'],**metrics,
                **{k:v for k,v in pred.items() if k!='text'},_private_text=pred['text'],
                prediction_sha256=hashlib.sha256(pred['text'].encode()).hexdigest(),
                hit_token_limit=pred['generated_tokens']>=CONFIG['generation_max_new_tokens'])
            save(path,record)
        results.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0 or i==len(rows):trainer.progress(stage='evaluation',role=role,model=key,complete=i,total=len(rows))
    slices={}
    for column in ('source','capture','device','held_layout','layout'):
        for value in {r[column] for r in results}:slices[column+'/'+str(value)]=summary([r for r in results if r[column]==value])
    save(OUT/f'{role}_{key}.json',dict(signature=sig,model_sha256=digest,profile=profile,summary=summary(results),
        slices=slices,rows=results,latency_is_cached_visual_feature_generation=True))

MODELS=('original','v1','control_42','partial_42','control_31415','partial_31415')

def seal():
    preserve_v1();records={k:read(OUT/f'development_{k}.json') for k in MODELS}
    best=max(MODELS[2:],key=lambda k:(records[k]['summary']['f1'],-records[k]['summary']['unsupported_nonempty']))
    baseline=max(records[k]['summary']['f1'] for k in ('original','v1'))
    cpu=read(OUT/'development_cpu.json')
    cpu_best=max(cpu['summaries'].values(),key=lambda r:r['f1'])
    approved=(records[best]['summary']['f1']>baseline and records[best]['summary']['f1']>=cpu_best['f1'] and
              records[best]['summary']['unsupported_nonempty']<=min([records[k]['summary']['unsupported_nonempty'] for k in ('original','v1')]+[cpu_best['unsupported_nonempty']]))
    models={k:dict(path=str(adapter_for(k)[0].relative_to(ROOT)) if adapter_for(k)[0] else None,sha256=adapter_for(k)[1]) for k in MODELS}
    save(OUT/'test_lock.json',dict(signature=signature(),models=models,selected_model=best,deployment_approved=approved,
        profile=read(OUT/'input_choice.json')['profile'],test_scored=False,development_summaries={k:v['summary'] for k,v in records.items()},
        development_cpu=cpu['summaries'],cpu_source_sha256=sha(ROOT/'research/v2_cpu.py'),
        rule='Higher dev F1 than both transfer baselines and no worse than best CPU; unsupported count no greater than those baselines',
        created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['probe','inputs','choose','train','evaluate','seal'])
    p.add_argument('--profile',choices=PROFILES,default='raw2');p.add_argument('--variant',choices=['partial','control'],default='partial')
    p.add_argument('--seed',type=int,choices=CONFIG['seeds'],default=42);p.add_argument('--role',choices=['development','test'],default='development')
    p.add_argument('--model',choices=MODELS,default='original');a=p.parse_args()
    # Use the same mutex as V1/web, then redirect only this process' trainer paths.
    with trainer.process_lock():
        configure_training()
        try:
            if a.action=='probe':probe(a.profile)
            elif a.action=='inputs':compare_inputs(a.profile)
            elif a.action=='choose':choose_inputs()
            elif a.action=='train':train(a.variant,a.seed)
            elif a.action=='evaluate':evaluate(a.role,a.model)
            elif a.action=='seal':seal()
        except Exception as exc:
            save(CACHE/f'failure_{time.time_ns()}.json',dict(action=a.action,model=a.model,profile=a.profile,
                type=type(exc).__name__,detail=str(exc),time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
            if a.action=='probe' and isinstance(exc,torch.cuda.OutOfMemoryError):
                save(OUT/f'probe_{a.profile}.json',dict(eligible=False,error='CUDA OOM',no_silent_batch_change=True))
            raise

if __name__=='__main__':main()
