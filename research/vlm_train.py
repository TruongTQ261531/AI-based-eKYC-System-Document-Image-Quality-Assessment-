"""Resumable local LoRA experiment with a pre-test lock and public numeric audit."""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import random
import time

import torch
from safetensors.torch import load_file

from research.vlm_setup import ROOT,CACHE,OUT,save,sha
from research.vlm_data import load
from research.vlm_runtime import VLM,signature,parsed,score,aggregate,PREPROCESS

CONFIG=json.loads((ROOT/'research/vlm_config.json').read_text(encoding='utf-8'))


@contextlib.contextmanager
def process_lock():
    import msvcrt
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'gpu.lock').open('a+b') as stream:
        if stream.tell()==0: stream.write(b'0');stream.flush()
        stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        try: yield
        finally: stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)


def progress(**items):
    save(CACHE/'progress.json',dict(pid=os.getpid(),time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**items))
    print(json.dumps(items,ensure_ascii=True),flush=True)


def feature_all(model, rows):
    start=time.perf_counter()
    for i,row in enumerate(rows,1):
        model.features(row)
        if i%16==0 or i==len(rows): progress(stage='features',complete=i,total=len(rows))
    return time.perf_counter()-start


def checkpoint(model,optimizer,step,cursor,seed,total,path,sig):
    path.mkdir(parents=True,exist_ok=True)
    model.model.language_model.save_pretrained(str(path),safe_serialization=True,save_embedding_layers=False)
    state=dict(optimizer=optimizer.state_dict(),torch_rng=torch.get_rng_state(),
               cuda_rng=torch.cuda.get_rng_state_all(),python_rng=random.getstate(),step=step,cursor=cursor,seed=seed,total=total)
    tmp=path/'training_state.pt.tmp';torch.save(state,tmp);tmp.replace(path/'training_state.pt')
    files=['adapter_model.safetensors','adapter_config.json','training_state.pt']
    save(path/'complete.json',dict(signature=sig,step=step,cursor=cursor,seed=seed,total=total,
                                 sha256={f:sha(path/f) for f in files}))


def restore(model,optimizer,path,sig):
    from peft import set_peft_model_state_dict
    metadata=json.loads((path/'complete.json').read_text(encoding='utf-8'))
    if metadata['signature']!=sig: raise ValueError('Checkpoint source/data/config changed')
    if any(sha(path/f)!=h for f,h in metadata['sha256'].items()): raise ValueError('Checkpoint hash mismatch')
    set_peft_model_state_dict(model.model.language_model,load_file(str(path/'adapter_model.safetensors')))
    state=torch.load(path/'training_state.pt',map_location='cpu',weights_only=True)
    optimizer.load_state_dict(state['optimizer'])
    torch.set_rng_state(state['torch_rng']);torch.cuda.set_rng_state_all(state['cuda_rng']);random.setstate(state['python_rng'])
    return state


def sampler(rows,seed,cursor):
    epoch,index=divmod(cursor,len(rows)); order=list(range(len(rows)));random.Random(seed+epoch).shuffle(order)
    return rows[order[index]]


def development_loss(model,rows):
    total=0.;count=0;model.model.language_model.eval()
    with torch.no_grad():
        for row in rows:
            loss,n,_=model.loss(row);total+=float(loss)*n;count+=n
    return total/max(count,1)


def train_steps(model,rows,dev,seed,total,accum,folder,start_state=None,stop=None,save_every=48):
    sig=signature();params=[p for p in model.model.language_model.parameters() if p.requires_grad]
    names=[n for n,p in model.model.language_model.named_parameters() if p.requires_grad]
    if not names or any('lora_' not in n for n in names): raise ValueError('Unintended base-model training')
    optimizer=torch.optim.AdamW(params,lr=CONFIG['learning_rate'],weight_decay=.01,foreach=False)
    state=restore(model,optimizer,start_state,sig) if start_state else dict(step=0,cursor=0,seed=seed,total=total)
    if state['seed']!=seed or state['total']!=total: raise ValueError('Resume configuration differs')
    cursor=state['cursor'];start=time.perf_counter();events=[];last=state['step']
    log=folder/'events.jsonl';folder.mkdir(parents=True,exist_ok=True)
    torch.cuda.reset_peak_memory_stats()
    for step in range(state['step']+1,(stop or total)+1):
        model.model.language_model.train();optimizer.zero_grad(set_to_none=True);loss_sum=0.;max_tokens=0
        lr=CONFIG['learning_rate']*min(1.,step/12)*(.5+.5*math.cos(math.pi*step/total))
        for group in optimizer.param_groups: group['lr']=lr
        for _ in range(accum):
            row=sampler(rows,seed,cursor);cursor+=1
            loss,_,length=model.loss(row)
            if not torch.isfinite(loss): raise FloatingPointError('Non-finite training loss')
            loss_sum+=float(loss.detach());max_tokens=max(max_tokens,length)
            (loss/accum).backward()
        norm=torch.nn.utils.clip_grad_norm_(params,1.)
        if not torch.isfinite(norm): raise FloatingPointError('Non-finite gradient norm')
        optimizer.step();last=step
        event=dict(step=step,time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),loss=loss_sum/accum,gradient_norm=float(norm),learning_rate=lr,
                   max_tokens=max_tokens,cursor=cursor,wall_seconds=time.perf_counter()-start,
                   peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
        if step%save_every==0 or step==(stop or total):
            if dev: event['development_loss']=development_loss(model,dev)
            checkpoint(model,optimizer,step,cursor,seed,total,folder/f'step_{step:04}',sig)
        events.append(event)
        with log.open('a',encoding='utf-8') as f: f.write(json.dumps(event)+'\n')
        if step%4==0 or 'development_loss' in event: progress(stage='training',seed=seed,**event)
    return events,optimizer


def original_parity(model,row):
    feature=model.features(row);ids,eos=model.prompt_ids();ids=ids.to('cuda')
    with torch.no_grad():
        from PIL import Image
        from research.vlm_runtime import pixels
        with Image.open(ROOT/row['path']) as im: tensor=pixels(im).to(device='cuda',dtype=model.dtype)
        fresh=model.model.extract_feature(tensor)
        if not torch.equal(feature.to('cuda'),fresh): raise ValueError('Cached visual feature differs from fresh extraction')
        a=model.model.generate(pixel_values=torch.empty((2,3,448,448),device='cuda',dtype=model.dtype),
                visual_features=feature.to('cuda'),input_ids=ids,attention_mask=torch.ones_like(ids),
                do_sample=False,max_new_tokens=24,eos_token_id=eos,pad_token_id=model.tokenizer.pad_token_id)
        b=model.model.language_model.generate(inputs_embeds=model.embeddings(ids,feature),
                attention_mask=torch.ones_like(ids),do_sample=False,max_new_tokens=24,eos_token_id=eos,
                pad_token_id=model.tokenizer.pad_token_id,use_cache=True)
    if not torch.equal(a,b): raise ValueError('Cached inference differs from pinned native generation')
    return dict(tokens=int(a.numel()),identical_tokens=True,cached_features_equal_fresh=True,
                scope='one smoke image, same frozen features and prompt; not all possible inputs')


def smoke():
    from peft import get_peft_model_state_dict
    rows=load('train')[:12];model=VLM(42);feature_all(model,rows)
    parity=original_parity(model,rows[0]);base=model.infer(rows[0])
    model.offload_vision();model.lora(CONFIG)
    initial={k:v.detach().cpu().clone() for k,v in get_peft_model_state_dict(model.model.language_model).items()}
    events,_=train_steps(model,rows,[],42,20,1,CACHE/'smoke',save_every=10)
    continuous={k:v.detach().cpu().clone() for k,v in get_peft_model_state_dict(model.model.language_model).items()}
    changed=sum(not torch.equal(initial[k],v) for k,v in continuous.items())
    if not changed: raise ValueError('No adapter update occurred')
    events2,_=train_steps(model,rows,[],42,20,1,CACHE/'smoke_resume',start_state=CACHE/'smoke/step_0010',save_every=10)
    resumed={k:v.detach().cpu() for k,v in get_peft_model_state_dict(model.model.language_model).items()}
    maximum=max(float((continuous[k]-resumed[k]).abs().max()) for k in continuous)
    if maximum!=0: raise ValueError(f'Resume differs from continuous run: {maximum}')
    result=dict(status='passed',signature=signature(),optimizer_steps_continuous=20,resumed_steps=10,
        adapter_tensors_changed=changed,resume_max_abs_difference=maximum,native_generation_parity=parity,
        training_peak_allocated_bytes=max(x['peak_allocated_bytes'] for x in events),
        training_peak_reserved_bytes=max(x['peak_reserved_bytes'] for x in events),
        start_loss=events[0]['loss'],end_loss=events[-1]['loss'],original_generation_tokens=base['generated_tokens'],
        gpu=torch.cuda.get_device_name(),dtype=str(model.dtype),new_venv=False,existing_runtime_changed=False)
    save(OUT/'smoke.json',result);print(json.dumps(result),flush=True)


def train(seed):
    folder=CACHE/f'seed_{seed}';sig=signature()
    model=VLM(seed);rows=load('train');dev=load('development')
    feature_seconds=feature_all(model,rows+dev);model.offload_vision();model.lora(CONFIG)
    completed=sorted(p for p in folder.glob('step_*') if (p/'complete.json').exists())
    resume=completed[-1] if completed else None
    start=time.perf_counter()
    events,_=train_steps(model,rows,dev,seed,CONFIG['steps'],CONFIG['gradient_accumulation'],folder,start_state=resume,
                         save_every=CONFIG['checkpoint_every'])
    all_events=[json.loads(x) for x in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    candidates=[x for x in all_events if 'development_loss' in x]
    best=min(candidates,key=lambda x:(x['development_loss'],x['step']))
    selected=folder/f"step_{best['step']:04}"
    result=dict(seed=seed,signature=sig,steps=CONFIG['steps'],selected_checkpoint=selected.relative_to(ROOT).as_posix(),
        selected_adapter_sha256=sha(selected/'adapter_model.safetensors'),development_loss=best['development_loss'],
        events=all_events,feature_cache_setup_seconds=feature_seconds,invocation_train_seconds=time.perf_counter()-start,
        resumed_from=resume.name if resume else None,test_used_for_selection=False)
    save(OUT/f'train_seed_{seed}.json',result)
    progress(stage='trained',seed=seed,selected_step=best['step'],development_loss=best['development_loss'])


def evaluate(role,model_key,repeat=1):
    sig=signature();adapter=None
    if role=='test':
        seal=json.loads((OUT/'test_lock.json').read_text(encoding='utf-8'))
        if seal['signature']!=sig: raise ValueError('Test source lock changed')
    if model_key!='original':
        seed=int(model_key.split('_')[1]);choice=json.loads((OUT/f'train_seed_{seed}.json').read_text(encoding='utf-8'))
        if choice['signature']!=sig: raise ValueError('Training source changed')
        adapter=ROOT/choice['selected_checkpoint']
        if sha(adapter/'adapter_model.safetensors')!=choice['selected_adapter_sha256']: raise ValueError('Adapter changed')
    model=VLM();rows=load(role)
    if repeat>1:
        identities=sorted({r['physical_id'] for r in rows},key=lambda x:hashlib.sha256(('vlm-repeat-v1/'+x).encode()).digest())[:6]
        rows=[r for r in rows if r['physical_id'] in identities and r['capture'] in ('full','value_mask')]
    setup=feature_all(model,rows);model.offload_vision()
    if adapter:
        from peft import PeftModel
        model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(adapter),is_trainable=False)
    outputs=[]
    for i,row in enumerate(rows,1):
        path=CACHE/'predictions'/f'{role}_{model_key}_{repeat}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
        if path.exists():
            record=json.loads(path.read_text(encoding='utf-8'))
            if record['signature']!=sig or record['input_sha256']!=row['input_sha256']: raise ValueError('Prediction cache changed')
        else:
            prediction=model.infer(row);fields,valid=parsed(prediction['text'])
            record=dict(signature=sig,uid=row['uid'],physical_id=row['physical_id'],role=role,capture=row['capture'],
                input_sha256=row['input_sha256'],model=model_key,repeat=repeat,
                **{k:v for k,v in prediction.items() if k!='text'},**score(row['target'],fields,valid),
                _private_text=prediction['text'],_private_fields=fields,
                prediction_sha256=hashlib.sha256(prediction['text'].encode()).hexdigest())
            record['masked_field_outputs']=sum(f.get('occluded',False) and f['key'] in fields for f in row['fields'])
            record['hit_token_limit']=prediction['generated_tokens']>=CONFIG['generation_max_new_tokens']
            save(path,record)
        outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0 or i==len(rows): progress(stage='evaluation',role=role,model=model_key,complete=i,total=len(rows))
    save(OUT/f'{role}_{model_key}_{repeat}.json',dict(signature=sig,rows=outputs,summary=aggregate(outputs),
        feature_cache_setup_seconds=setup,latency_is_cached_visual_feature_inference=True,
        mean_wall_seconds=sum(x['wall_seconds'] for x in outputs)/len(outputs)))


def seal():
    records={k:json.loads((OUT/f'development_{k}_1.json').read_text(encoding='utf-8')) for k in ['original','seed_42','seed_31415']}
    sig=signature()
    if any(x['signature']!=sig for x in records.values()): raise ValueError('Development source changed')
    baseline=json.loads((OUT/'development_ocr.json').read_text(encoding='utf-8'))
    if baseline['signature']!=sig: raise ValueError('CPU development baseline needs final-source replay')
    expected={r['uid'] for r in load('development')}
    if any({r['uid'] for r in value['rows']}!=expected for value in records.values()): raise ValueError('Incomplete development comparison')
    best=max(['seed_42','seed_31415'],key=lambda k:records[k]['summary']['f1'])
    original=records['original']['summary'];adapted=records[best]['summary'];ocr=baseline['summaries']['ocr_existing_web']
    approved=(adapted['f1']>original['f1'] and adapted['f1']>=ocr['f1'] and
              adapted['masked_field_outputs']<=min(original['masked_field_outputs'],ocr['masked_field_outputs']) and
              adapted['json_valid_rate']>=original['json_valid_rate'])
    adapters={}
    for seed in CONFIG['seeds']:
        record=json.loads((OUT/f'train_seed_{seed}.json').read_text(encoding='utf-8'))
        adapters[str(seed)]={k:record[k] for k in ('selected_checkpoint','selected_adapter_sha256')}
    save(OUT/'test_lock.json',dict(signature=sig,selected_model=best,adapters=adapters,
        development_summaries={k:v['summary'] for k,v in records.items()},
        development_ocr_summary=ocr,deployment_approved=approved,
        test_scored=False,selection_uses_development_only=True))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['features','smoke','train','evaluate','seal'])
    parser.add_argument('--seed',type=int,choices=CONFIG['seeds'],default=42)
    parser.add_argument('--role',choices=['development','calibration','test'],default='development')
    parser.add_argument('--model',choices=['original','seed_42','seed_31415'],default='original')
    parser.add_argument('--repeat',type=int,default=1);args=parser.parse_args()
    with process_lock():
        try:
            if args.action=='features': feature_all(VLM(),load('train')+load('development'))
            elif args.action=='smoke': smoke()
            elif args.action=='train': train(args.seed)
            elif args.action=='evaluate': evaluate(args.role,args.model,args.repeat)
            elif args.action=='seal': seal()
        except Exception as exc:
            save(CACHE/f'failure_{time.time_ns()}.json',dict(action=args.action,type=type(exc).__name__,detail=str(exc),signature=signature()))
            raise


if __name__=='__main__': main()
