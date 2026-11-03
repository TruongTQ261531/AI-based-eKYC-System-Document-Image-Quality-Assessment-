"""Fixed-checkpoint matched-control training and prospectively sealed evaluation."""
import argparse
import hashlib
import json
import time
from research.fc_common import *
from research.hp_metrics import scoring, summary


def configure(seed=42, training=False):
    import torch
    from research import v2_runtime, vlm_train as trainer
    v2_runtime.CACHE=CACHE;v2_runtime.PILOT_CACHE=HP_CACHE
    trainer.CACHE=CACHE;trainer.OUT=OUT;trainer.CONFIG=CONFIG;trainer.signature=signature
    model=v2_runtime.VLM(seed,'rect2')
    torch.set_num_threads(2 if training else read(OUT/'runtime_choice.json')['chosen_inference_host_threads'])
    return model,trainer


def train(arm,seed):
    if arm not in NEW_ARMS or seed not in SEEDS:raise ValueError('Only new registered arms may train')
    if (OUT/'test_lock.json').exists():raise ValueError('Sealed; never retrain against this test')
    if read(OUT/'prepare_publication.json')['signature']!=signature():raise ValueError('Unpublished training contract')
    preserve();rows=train_rows(arm);model,trainer=configure(seed,True)
    setup=trainer.feature_all(model,rows)
    counts=[model.tokens(r['target']) for r in rows]
    exposure=dict(input_and_answer_tokens=2*sum(int(a.numel()) for a,b in counts),
                  answer_loss_tokens=2*sum(int(b.ne(-100).sum()) for a,b in counts));del counts
    expected=read(OUT/'training_design.json')['answer_loss_tokens_per_seed'][arm]
    if exposure['answer_loss_tokens']!=expected:raise ValueError('Actual model tokenization differs from matched data')
    model.offload_vision();model.lora(CONFIG);folder=CACHE/'training'/f'{arm}_{seed}'
    completed=sorted(p for p in folder.glob('step_*') if (p/'complete.json').exists())
    resume=completed[-1] if completed else None
    if resume and (folder/'events.jsonl').exists():
        last=read(resume/'complete.json')['step']
        events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        if any(e['step']>last for e in events):
            save(folder/f'discarded_after_{last:04}_{time.time_ns()}.json',events)
            (folder/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events if e['step']<=last),encoding='utf-8',newline='\n')
    trainer.train_steps(model,rows,[],seed,320,4,folder,start_state=resume,save_every=80)
    final=folder/'step_0320';events=[json.loads(s) for s in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    if [e['step'] for e in events]!=list(range(1,321)):raise ValueError('Training event continuity differs')
    sequence=[trainer.sampler(rows,seed,i) for i in range(1280)]
    order=stable_hash([r['physical_id']+'/'+str(r['slot']) for r in sequence])
    if order!=read(HP_OUT/f'train_hard_{seed}.json')['identity_slot_sequence_sha256']:
        raise ValueError('Historical ID/slot exposure differs')
    save(OUT/f'train_{arm}_{seed}.json',dict(signature=signature(),arm=arm,seed=seed,steps=320,presentations=1280,
        identity_slot_sequence_sha256=order,pixel_sequence_sha256=stable_hash([r['input_sha256'] for r in sequence]),
        token_exposure=exposure,feature_setup_seconds=setup,events=events,
        selected_checkpoint=final.relative_to(ROOT).as_posix(),selected_adapter_sha256=sha(final/'adapter_model.safetensors'),
        resumed_from=resume.relative_to(ROOT).as_posix() if resume else None,selection='Fixed final320; never test-selected'))


def adapter_for(key):
    if key not in KEYS:raise ValueError('Unknown adapter')
    arm,seed=key.rsplit('_',1)
    folder=V3_OUT if arm=='uniform' else HP_OUT if arm=='hard' else OUT
    name=f'train_source_{seed}.json' if arm=='uniform' else f'train_{key}.json'
    record=read(folder/name);path=ROOT/record['selected_checkpoint'];digest=record['selected_adapter_sha256']
    if sha(path/'adapter_model.safetensors')!=digest:raise ValueError('Adapter changed')
    if arm in NEW_ARMS and record['signature']!=signature():raise ValueError('New arm contract differs')
    if record['steps']!=320 or record['presentations']!=1280:raise ValueError('Unmatched final checkpoint')
    return path,digest


def verify_test():
    lock=read(OUT/'test_lock.json');pub=read(OUT/'test_publication.json')
    if lock['signature']!=signature() or pub['signature']!=signature() or pub['lock_sha256']!=sha(OUT/'test_lock.json'):
        raise ValueError('Test contract was not sealed/published')
    return lock


def evaluate(role,key):
    if role not in ('development','test'):raise ValueError('Unknown role')
    preserve();path,digest=adapter_for(key)
    if role=='test' and verify_test()['models'][key]['sha256']!=digest:raise ValueError('Test model changed')
    rows=eval_rows(role);pixel_hashes={r['input_sha256']:r['pixel_sha256'] for r in read(OUT/'pixel_manifest.json')}
    reuse=role=='development' and key.split('_')[0] in ('uniform','hard') and read(OUT/'runtime_choice.json')['chosen_inference_host_threads']==2
    model=None
    if not reuse:
        from peft import PeftModel
        model,trainer=configure();trainer.feature_all(model,rows);model.offload_vision()
        model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    else:
        from research import vlm_train as trainer
        trainer.CACHE=CACHE
    outputs=[]
    for i,row in enumerate(rows,1):
        dest=CACHE/'predictions'/f'{role}_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
        if dest.exists():
            record=read(dest)
            if record['signature']!=signature() or record['model_sha256']!=digest or record['input_sha256']!=row['input_sha256']:
                raise ValueError('Incompatible prediction cache')
        else:
            if reuse:
                old=read(HP_CACHE/'predictions'/f'development_{key}'/dest.name)
                if old['input_sha256']!=row['input_sha256'] or old['model_sha256']!=digest:
                    raise ValueError('Historical dev inference does not match')
                pred=dict(text=old['_private_text'],generated_tokens=old['generated_tokens'],
                    wall_seconds=old['wall_seconds'],visual_features_cached=True)
            else:pred=model.infer(row)
            metrics,_=scoring(row,pred['text'])
            record=dict(signature=signature(),model=key,model_sha256=digest,uid=row['uid'],physical_id=row['physical_id'],
                input_sha256=row['input_sha256'],pixel_sha256=pixel_hashes[row['input_sha256']],source=row['source'],device=row['device'],layout=row['layout'],capture=row['capture'],
                **metrics,**{k:v for k,v in pred.items() if k!='text'},reused_historical_development=reuse,
                _private_text=pred['text'],prediction_sha256=hashlib.sha256(pred['text'].encode()).hexdigest(),
                hit_token_limit=pred['generated_tokens']>=384)
            save(dest,record)
        outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
        if i%4==0 or i==len(rows):trainer.progress(stage='fair_control_evaluation',role=role,model=key,complete=i,total=len(rows))
    save(OUT/f'{role}_{key}.json',dict(signature=signature(),rows=outputs,summary=summary(outputs),
        actual_cached_generation_calls=sum(not r['reused_historical_development'] for r in outputs),
        reused_development_outputs=sum(r['reused_historical_development'] for r in outputs)))


def seal():
    preserve()
    for key in KEYS:
        if read(OUT/f'development_{key}.json')['signature']!=signature():raise ValueError('Missing matching development')
    value=dict(signature=signature(),evaluation_sha256=sha(DATA/'evaluation.json'),profile='rect2',max_new_tokens=384,
        runtime=read(OUT/'runtime_choice.json'),models={k:dict(path=adapter_for(k)[0].relative_to(ROOT).as_posix(),sha256=adapter_for(k)[1]) for k in KEYS},
        primary_comparisons=[[f'hard_{s}',f'{a}_{s}'] for s in SEEDS for a in ('random','repeat')],
        analysis_plan_sha256=sha(OUT/'analysis_plan.json'),test_generation_started=False,
        model_promotion=False,selection='Fixed arms/final320; no test winner or deployment selection')
    dest=OUT/'test_lock.json'
    if dest.exists() and read(dest)!=value:raise ValueError('Existing seal differs')
    save(dest,value);print('FC_EIGHT_ADAPTERS_SEALED',flush=True)


def fresh(key):
    from PIL import Image
    from peft import PeftModel
    lock=verify_test();path,digest=adapter_for(key)
    model,trainer=configure();model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    rows=eval_rows('test');panel=[]
    for source in ('authored','midv2020'):
        pid=min({r['physical_id'] for r in rows if r['source']==source},key=lambda p:hashlib.sha256(('fc-fresh/'+p).encode()).digest())
        panel.extend(r for r in rows if r['physical_id']==pid and r['capture'] in ('full','pair_mask'))
    references={r['uid']:r for r in read(OUT/f'test_{key}.json')['rows']};outputs=[]
    for row in panel:
        for repeat in (1,2):
            dest=CACHE/'fresh'/key/(hashlib.sha256((row['uid']+'/'+str(repeat)).encode()).hexdigest()+'.json')
            if dest.exists():record=read(dest)
            else:
                with Image.open(ROOT/row['path']) as image:pred=model.fresh(image)
                metrics,_=scoring(row,pred['text']);digest_text=hashlib.sha256(pred['text'].encode()).hexdigest()
                record=dict(signature=signature(),model=key,model_sha256=digest,uid=row['uid'],physical_id=row['physical_id'],
                    repeat=repeat,input_sha256=row['input_sha256'],prediction_sha256=digest_text,
                    identical_to_test=digest_text==references[row['uid']]['prediction_sha256'],**metrics,
                    **{k:v for k,v in pred.items() if k!='text'},_private_text=pred['text'])
                save(dest,record)
            if record['signature']!=signature() or record['model_sha256']!=digest or record['input_sha256']!=row['input_sha256']:
                raise ValueError('Fresh cache differs')
            outputs.append({k:v for k,v in record.items() if not k.startswith('_private')})
            trainer.progress(stage='fair_control_fresh',model=key,complete=len(outputs),total=8)
    save(OUT/f'fresh_{key}.json',dict(signature=signature(),rows=outputs,additional_calls=8,distinct_inputs=4,document_instances=2,
        mismatches=sum(not r['identical_to_test'] for r in outputs)))


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['train','evaluate','seal','fresh'])
    p.add_argument('--arm',choices=NEW_ARMS,default='random');p.add_argument('--seed',type=int,choices=SEEDS,default=42)
    p.add_argument('--model',choices=KEYS,default=KEYS[0]);p.add_argument('--role',choices=['development','test'],default='development')
    a=p.parse_args()
    from research import vlm_train
    with vlm_train.process_lock():
        try:
            if a.action=='train':train(a.arm,a.seed)
            elif a.action=='evaluate':evaluate(a.role,a.model)
            elif a.action=='seal':seal()
            else:fresh(a.model)
        except Exception as exc:
            save(CACHE/f'failure_{time.time_ns()}.json',dict(action=a.action,error_type=type(exc).__name__,detail=str(exc)));raise


if __name__=='__main__':main()
