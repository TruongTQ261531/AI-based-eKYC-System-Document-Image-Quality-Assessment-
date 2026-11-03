"""Matched-update pair-mask LoRA and sealed, genuinely new evaluation inputs."""
import argparse
import hashlib
import json
import math
import time
from research.hp_common import *
from research.hp_metrics import scoring,summary


def configure(seed=42):
    from research import v2_runtime
    from research.v2_common import CACHE as OLD_FEATURES
    from research import vlm_train as trainer
    # Shared old features are copied into a separate content-addressed cache.
    v2_runtime.CACHE=CACHE;v2_runtime.PILOT_CACHE=OLD_FEATURES
    trainer.CACHE=CACHE;trainer.OUT=OUT;trainer.CONFIG=CONFIG;trainer.signature=signature
    return v2_runtime.VLM(seed,'rect2'),trainer


def train(seed0):
    if (OUT/'test_lock.json').exists():raise ValueError('Study sealed; never retrain against this test')
    prepare=read(OUT/'prepare_publication.json')
    if prepare['signature']!=signature():raise ValueError('Pretraining publication differs')
    preserve();model,trainer=configure(seed0);rows=load('train')
    expected=[r for r in read(OLD_DATA/'samples.json') if r['role']=='train' and r['variant']=='partial']
    if [(r['physical_id'],r['slot']) for r in rows]!=[(r['physical_id'],r['slot']) for r in expected]:raise ValueError('Train slot order differs')
    start=time.perf_counter()
    trainer.feature_all(model,rows)
    setup=time.perf_counter()-start
    token_counts=[model.tokens(r['target']) for r in rows]
    tokens=dict(input_and_answer_tokens=2*sum(int(a.numel()) for a,b in token_counts),
                answer_loss_tokens=2*sum(int(b.ne(-100).sum()) for a,b in token_counts));del token_counts
    model.offload_vision();model.lora(CONFIG);folder=CACHE/'training'/f'hard_{seed0}'
    complete=sorted(p for p in folder.glob('step_*') if (p/'complete.json').exists());resume=complete[-1] if complete else None
    # Retain interrupted trailing events but do not count their replay twice.
    if resume and (folder/'events.jsonl').exists():
        last=read(resume/'complete.json')['step']
        events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        if any(e['step']>last for e in events):
            save(folder/f'interrupted_events_after_{last:04}_{time.time_ns()}.json',events)
            (folder/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events if e['step']<=last),encoding='utf-8',newline='\n')
    trainer.train_steps(model,rows,[],seed0,320,4,folder,start_state=resume,save_every=80)
    checkpoint=folder/'step_0320';events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    if [e['step'] for e in events]!=list(range(1,321)):raise ValueError('Training event continuity differs')
    sequence=[trainer.sampler(rows,seed0,i) for i in range(1280)]
    slot_hash=stable_hash([r['physical_id']+'/'+str(r['slot']) for r in sequence])
    if slot_hash!=read(OLD_OUT/f'train_source_{seed0}.json')['identity_slot_sequence_sha256']:raise ValueError('Unmatched identity exposure')
    save(OUT/f'train_hard_{seed0}.json',dict(signature=signature(),seed=seed0,steps=320,presentations=1280,
        identities=128,identity_slot_sequence_sha256=slot_hash,
        pixel_sequence_sha256=stable_hash([r['input_sha256'] for r in sequence]),token_exposure=tokens,
        selected_checkpoint=checkpoint.relative_to(ROOT).as_posix(),selected_adapter_sha256=sha(checkpoint/'adapter_model.safetensors'),
        events=events,feature_setup_seconds=setup,resumed_from=str(resume.relative_to(ROOT)) if resume else None,
        selection_rule='Fixed final320; same ID slots, seed, accumulation and optimizer as uniform V3'))


def adapter_for(key):
    if key not in KEYS:raise ValueError('Unknown model')
    if key.startswith('uniform_'):return baseline(key)
    record=read(OUT/f'train_{key}.json')
    if record['signature']!=signature():raise ValueError('Training contract changed')
    path=ROOT/record['selected_checkpoint']
    if sha(path/'adapter_model.safetensors')!=record['selected_adapter_sha256']:raise ValueError('Hard adapter changed')
    return path,record['selected_adapter_sha256']


def verify_test():
    lock=read(OUT/'test_lock.json');publication=read(OUT/'test_publication.json')
    if lock['signature']!=signature() or publication['lock_sha256']!=sha(OUT/'test_lock.json') or publication['signature']!=signature():
        raise ValueError('Test seal not published or contract changed')
    return lock


def evaluate(role,key):
    if role not in ('development','test'):raise ValueError('Unknown eval role')
    path,digest=adapter_for(key)
    if role=='test' and verify_test()['models'][key]['sha256']!=digest:raise ValueError('Test model differs from lock')
    model,trainer=configure();rows=load(role);trainer.feature_all(model,rows);model.offload_vision()
    from peft import PeftModel
    model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    outputs=[]
    for i,row in enumerate(rows,1):
        dest=CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
        if dest.exists():
            record=read(dest)
            if record['signature']!=signature() or record['input_sha256']!=row['input_sha256'] or record['model_sha256']!=digest:
                raise ValueError('Prediction cache changed')
        else:
            reused=False
            if role=='development' and key.startswith('uniform_') and '/hp/' not in row['uid']:
                old=OLD_CACHE/'predictions'/f'development_source_{key.split("_")[1]}'/dest.name
                previous=read(old)
                if previous['input_sha256']!=row['input_sha256'] or previous['model_sha256']!=digest:raise ValueError('Reused dev output differs')
                pred=dict(text=previous['_private_text'],**{k:previous[k] for k in ('wall_seconds','generated_tokens','visual_features_cached')})
                reused=True
            else:pred=model.infer(row)
            metrics,_=scoring(row,pred['text'])
            record=dict(signature=signature(),model=key,model_sha256=digest,uid=row['uid'],physical_id=row['physical_id'],
                input_sha256=row['input_sha256'],source=row['source'],device=row['device'],layout=row['layout'],capture=row['capture'],
                **metrics,**{k:v for k,v in pred.items() if k!='text'},reused_old_development_inference=reused,
                _private_text=pred['text'],prediction_sha256=hashlib.sha256(pred['text'].encode()).hexdigest(),
                hit_token_limit=pred['generated_tokens']>=384)
            save(dest,record)
        outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0 or i==len(rows):trainer.progress(stage='hard_pair_evaluation',role=role,model=key,complete=i,total=len(rows))
    save(OUT/f'{role}_{key}.json',dict(signature=signature(),model_sha256=digest,rows=outputs,summary=summary(outputs),
        inference_calls=sum(not r['reused_old_development_inference'] for r in outputs),
        reused_calls=sum(r['reused_old_development_inference'] for r in outputs)))


def seal():
    preserve();records={k:read(OUT/f'development_{k}.json') for k in KEYS}
    hard=min((k for k in KEYS if k.startswith('hard_')),
        key=lambda k:(-records[k]['summary']['f1'],records[k]['summary']['unsupported_nonempty'],int(k.split('_')[1])))
    chosen=records[hard]['summary']
    approved=all(chosen['f1']>records[k]['summary']['f1'] and
        chosen['unsupported_nonempty']<=records[k]['summary']['unsupported_nonempty'] and
        chosen['neighbor_omissions']<=records[k]['summary']['neighbor_omissions'] for k in KEYS if k.startswith('uniform_'))
    value=dict(signature=signature(),samples_sha256=sha(DATA/'samples.json'),profile='rect2',generation_max_new_tokens=384,
        models={k:dict(path=adapter_for(k)[0].relative_to(ROOT).as_posix(),sha256=adapter_for(k)[1]) for k in KEYS},
        selected_hard_candidate=hard,promotion_approved=approved,test_scoring_started=False,
        selection='Development F1, unsupported outputs, seed; promotion requires strict improvement over both controls without additional omissions/unsupported outputs',
        development_summaries={k:r['summary'] for k,r in records.items()})
    dest=OUT/'test_lock.json'
    if dest.exists() and read(dest)!=value:raise ValueError('Existing test seal differs')
    save(dest,value);print('HP_TEST_SEALED',hard,'promotion',approved,flush=True)


def fresh():
    from PIL import Image
    import numpy as np
    from peft import PeftModel
    lock=verify_test();key=lock['selected_hard_candidate'];path,digest=adapter_for(key)
    model,trainer=configure();model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    rows=load('test');chosen=[]
    for source in ('authored','midv2020'):
        ids=sorted({r['physical_id'] for r in rows if r['source']==source},key=lambda p:hashlib.sha256(('hp-fresh/'+p).encode()).digest())[:2]
        chosen.extend(r for r in rows if r['physical_id'] in ids and r['capture'] in ('full','pair_mask'))
    references={r['uid']:r for r in read(OUT/f'test_{key}.json')['rows']};outputs=[]
    for row in chosen:
        for repeat in (1,2):
            dest=CACHE/'fresh'/(hashlib.sha256((row['uid']+'/'+str(repeat)).encode()).hexdigest()+'.json')
            if dest.exists():
                record=read(dest)
                if record['signature']!=signature() or record['input_sha256']!=row['input_sha256']:raise ValueError('Fresh input differs')
            else:
                with Image.open(ROOT/row['path']) as image:pred=model.fresh(image)
                metrics,_=scoring(row,pred['text']);text_hash=hashlib.sha256(pred['text'].encode()).hexdigest()
                record=dict(signature=signature(),uid=row['uid'],physical_id=row['physical_id'],repeat=repeat,model=key,
                    model_sha256=digest,input_sha256=row['input_sha256'],prediction_sha256=text_hash,
                    identical_to_test=text_hash==references[row['uid']]['prediction_sha256'],**metrics,
                    **{k:v for k,v in pred.items() if k!='text'},_private_text=pred['text'])
                save(dest,record)
            outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
            trainer.progress(stage='hard_pair_fresh',complete=len(outputs),total=16)
    save(OUT/'fresh_repeats.json',dict(signature=signature(),model=key,additional_calls=16,distinct_inputs=8,document_instances=4,
        mismatches=sum(not r['identical_to_test'] for r in outputs),rows=outputs,
        p50_fresh_seconds=float(np.percentile([r['wall_seconds'] for r in outputs],50)),
        p95_fresh_seconds=float(np.percentile([r['wall_seconds'] for r in outputs],95))))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','evaluate','seal','fresh'])
    p.add_argument('--seed',type=int,choices=[42,31415],default=42);p.add_argument('--role',choices=['development','test'],default='development')
    p.add_argument('--model',choices=KEYS,default='hard_42');a=p.parse_args()
    from research import vlm_train as trainer
    # Use the original shared GPU lock before changing the trainer output paths.
    with trainer.process_lock():
        try:
            if a.action=='train':train(a.seed)
            elif a.action=='evaluate':evaluate(a.role,a.model)
            elif a.action=='seal':seal()
            else:fresh()
        except Exception as exc:
            save(CACHE/f'failure_{time.time_ns()}.json',dict(action=a.action,error_type=type(exc).__name__,detail=str(exc)));raise


if __name__=='__main__':main()
