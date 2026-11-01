"""Matched-pixel source-reference LoRA and prospective eight-model comparison."""
import argparse
import hashlib
import json
import time
import torch
from research.v3_common import *
from research.v3_metrics import scoring,summary,canonical
from research.v2_runtime import VLM
from research.v2_study import feature_all,panel
from research import vlm_train as trainer

BASES=('original','v1','control_42','partial_42','control_31415','partial_31415')
MODELS=BASES+('source_42','source_31415')

def profile():return read(R2OUT/'input_choice.json')['profile']

def train(seed0):
    if (OUT/'test_lock.json').exists():raise ValueError('Source study already sealed')
    preserve_v1();trainer.CACHE=CACHE;trainer.OUT=OUT;trainer.CONFIG=CONFIG;trainer.signature=signature
    rows=load('train');dev_ids={r['uid'] for r in panel('development',4)};dev=[r for r in load('development') if r['uid'] in dev_ids]
    model=VLM(seed0,profile());setup=feature_all(model,rows+dev)
    lengths=[model.tokens(r['target']) for r in rows]
    tokens=dict(input_and_answer_tokens=2*sum(int(a.numel()) for a,b in lengths),answer_loss_tokens=2*sum(int(b.ne(-100).sum()) for a,b in lengths));del lengths
    model.offload_vision();model.lora(CONFIG);folder=CACHE/'training'/f'source_{seed0}'
    complete=sorted(p for p in folder.glob('step_*') if (p/'complete.json').exists());resume=complete[-1] if complete else None
    trainer.train_steps(model,rows,dev,seed0,320,4,folder,start_state=resume,save_every=80)
    path=folder/'step_0320';events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    sequence=[trainer.sampler(rows,seed0,i) for i in range(1280)]
    paired=read(R2OUT/f'train_partial_{seed0}.json')
    slots=stable_hash([r['physical_id']+'/'+str(r['slot']) for r in sequence])
    if slots!=paired['identity_slot_sequence_sha256']:raise ValueError('Source/body exposure differs')
    # The entire ordered pixel sequence must match, not just the document IDs.
    from research.v2_common import load as load_body
    body=load_body('train','partial')
    pixel_sequence=stable_hash([r['input_sha256'] for r in sequence])
    if pixel_sequence!=stable_hash([trainer.sampler(body,seed0,i)['input_sha256'] for i in range(1280)]):raise ValueError('Source/body input pixels differ')
    save(OUT/f'train_source_{seed0}.json',dict(signature=signature(),seed=seed0,steps=320,presentations=1280,identities=128,
        identity_slot_sequence_sha256=slots,pixel_sequence_sha256=pixel_sequence,token_exposure=tokens,
        selected_checkpoint=path.relative_to(ROOT).as_posix(),selected_adapter_sha256=sha(path/'adapter_model.safetensors'),
        feature_setup_seconds=setup,events=events,selection_rule='Fixed final320, identical to R2 partial',
        source_target_only_intervention=True))

def adapter_for(key):
    if key in BASES:
        record=read(R2OUT/'test_lock.json')['models'][key];return ROOT/record['path'] if record['path'] else None,record['sha256']
    record=read(OUT/f'train_{key}.json')
    if record['signature']!=signature():raise ValueError('Source training contract changed')
    path=ROOT/record['selected_checkpoint'];digest=sha(path/'adapter_model.safetensors')
    if digest!=record['selected_adapter_sha256']:raise ValueError('Source adapter changed')
    return path,digest

def verify_test():
    seal=read(OUT/'test_lock.json');pub=read(OUT/'lock_publication.json')
    if seal['signature']!=signature() or pub['lock_sha256']!=sha(OUT/'test_lock.json'):raise ValueError('Source seal not published')
    return seal

def evaluate(role,key):
    sig=signature();adapter,digest=adapter_for(key)
    if role=='test' and verify_test()['models'][key]['sha256']!=digest:raise ValueError('Test adapter differs')
    model=VLM(42,profile());rows=load(role);feature_all(model,rows);model.offload_vision()
    if adapter:
        from peft import PeftModel
        model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(adapter),is_trainable=False)
    outputs=[]
    for i,r in enumerate(rows,1):
        path=CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(r['uid'].encode()).hexdigest()+'.json')
        if path.exists():
            record=read(path)
            if record['signature']!=sig or record['input_sha256']!=r['input_sha256'] or record['model_sha256']!=digest:raise ValueError('Source prediction cache differs')
        else:
            pred=model.infer(r);metrics,_=scoring(r,pred['text'])
            record=dict(signature=sig,model_sha256=digest,uid=r['uid'],physical_id=r['physical_id'],input_sha256=r['input_sha256'],
                source=r['source'],device=r['device'],layout=r['layout'],held_layout=r.get('held_layout',False),capture=r['capture'],
                **metrics,**{k:v for k,v in pred.items() if k!='text'},_private_text=pred['text'],
                prediction_sha256=hashlib.sha256(pred['text'].encode()).hexdigest(),hit_token_limit=pred['generated_tokens']>=384)
            save(path,record)
        outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0 or i==len(rows):trainer.progress(stage='source_evaluation',role=role,model=key,complete=i,total=len(rows))
    save(OUT/f'{role}_{key}.json',dict(signature=sig,model_sha256=digest,rows=outputs,summary=summary(outputs),profile=profile()))

def rescore(role):
    if role=='test':verify_test()
    samples={r['uid']:r for r in load(role)};records={}
    for key in MODELS:
        if key.startswith('source_'):
            records[key]=read(OUT/f'{role}_{key}.json');continue
        body=read(R2OUT/f'{role}_{key}.json');outputs=[]
        for row in body['rows']:
            private=read(R2CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json'))
            sample=samples[row['uid']]
            if row['input_sha256']!=sample['input_sha256']:raise ValueError('Re-scoring changed pixels')
            metrics,fields=scoring(sample,private['_private_text'])
            rescued=sum(k not in sample['body_target'] and k in fields and any(canonical(k,fields[k])==canonical(k,e['value'],e['kind']) for e in refs) for k,refs in sample['source_refs'].items())
            outputs.append(dict(uid=row['uid'],physical_id=row['physical_id'],source=row['source'],device=row['device'],layout=row['layout'],
                held_layout=row['held_layout'],capture=row['capture'],input_sha256=row['input_sha256'],**metrics,
                prediction_sha256=row['prediction_sha256'],model_sha256=row['model_sha256'],
                wall_seconds=row['wall_seconds'],generated_tokens=row['generated_tokens'],hit_token_limit=row['hit_token_limit'],
                reused_R2_inference=True,body_false_extra_but_source_supported=rescued))
        records[key]=dict(signature=signature(),model_sha256=body['model_sha256'],summary=summary(outputs),rows=outputs,reused_R2_inference=True)
        save(OUT/f'{role}_{key}.json',records[key])
    slices={}
    for key,record in records.items():
        slices[key]={}
        for col in ('source','capture','device','layout','held_layout'):
            for value in {r[col] for r in record['rows']}:
                slices[key][col+'/'+str(value)]=summary([r for r in record['rows'] if r[col]==value])
    save(OUT/f'{role}_comparison.json',dict(signature=signature(),summaries={k:v['summary'] for k,v in records.items()},slices=slices,
        R2_predictions_reused=True,not_independent_second_inference=True))

def seal():
    comp=read(OUT/'development_comparison.json');cpu=read(OUT/'development_cpu.json')
    best=max(MODELS,key=lambda k:(comp['summaries'][k]['f1'],-comp['summaries'][k]['unsupported_nonempty']))
    cpu_best=max(cpu['summaries'].values(),key=lambda s:s['f1']);s=comp['summaries'][best]
    approved=(best not in ('original','v1') and s['f1']>=cpu_best['f1'] and s['unsupported_nonempty']<=cpu_best['unsupported_nonempty'])
    models={}
    for key in MODELS:
        path,digest=adapter_for(key);models[key]=dict(path=path.relative_to(ROOT).as_posix() if path else None,sha256=digest)
    save(OUT/'test_lock.json',dict(signature=signature(),models=models,selected_model=best,deployment_approved=approved,
        profile=profile(),R2_lock_sha256=sha(R2OUT/'test_lock.json'),development=comp['summaries'],development_cpu=cpu['summaries'],
        cpu_source_sha256=sha(ROOT/'research/v3_cpu.py'),test_scored=False,
        created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))

def fresh():
    from PIL import Image
    from peft import PeftModel
    import numpy as np
    lock=verify_test();key=lock['selected_model'];adapter,digest=adapter_for(key)
    model=VLM(42,profile())
    if adapter:model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(adapter),is_trainable=False)
    rows={r['uid']:r for r in load('test')};selected=panel('test',4);results=[]
    reference={r['uid']:r for r in read(OUT/f'test_{key}.json')['rows']}
    for r0 in selected:
        r=rows[r0['uid']]
        for repeat in (1,2):
            path=CACHE/'fresh'/(hashlib.sha256((r['uid']+'/'+str(repeat)).encode()).hexdigest()+'.json')
            if path.exists():
                record=read(path)
                if record['signature']!=signature() or record['input_sha256']!=r['input_sha256'] or record['model']!=key:raise ValueError('Fresh source cache differs')
            else:
                with Image.open(ROOT/r['path']) as image:pred=model.fresh(image)
                metrics,_=scoring(r,pred['text']);digest0=hashlib.sha256(pred['text'].encode()).hexdigest()
                record=dict(signature=signature(),uid=r['uid'],physical_id=r['physical_id'],repeat=repeat,model=key,
                    input_sha256=r['input_sha256'],prediction_sha256=digest0,identical_to_test=digest0==reference[r['uid']]['prediction_sha256'],
                    **metrics,**{k:v for k,v in pred.items() if k!='text'},_private_text=pred['text'])
                save(path,record)
            results.append({k:v for k,v in record.items() if not k.startswith('_private')});print('SOURCE_FRESH',len(results),16,flush=True)
    save(OUT/'fresh_repeats.json',dict(signature=signature(),model=key,additional_calls=16,groups=8,
        mismatches=sum(not r['identical_to_test'] for r in results),
        p50_fresh_seconds=float(np.percentile([r['wall_seconds'] for r in results],50)),
        p95_fresh_seconds=float(np.percentile([r['wall_seconds'] for r in results],95)),rows=results))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','evaluate','rescore','seal','fresh']);p.add_argument('--seed',type=int,choices=CONFIG['seeds'],default=42)
    p.add_argument('--role',choices=['development','test'],default='development');p.add_argument('--model',choices=['source_42','source_31415'],default='source_42');a=p.parse_args()
    with trainer.process_lock():
        trainer.CACHE=CACHE;trainer.OUT=OUT
        try:
            if a.action=='train':train(a.seed)
            elif a.action=='evaluate':evaluate(a.role,a.model)
            elif a.action=='rescore':rescore(a.role)
            elif a.action=='seal':seal()
            else:fresh()
        except Exception as exc:
            save(CACHE/f'failure_{time.time_ns()}.json',dict(action=a.action,type=type(exc).__name__,detail=str(exc)));raise

if __name__=='__main__':main()
