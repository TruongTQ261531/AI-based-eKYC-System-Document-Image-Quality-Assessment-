"""Fixed missing-field checksum-MRZ fallback; separate prospective secondary study."""
import argparse
import hashlib
import json
import time
import cv2
import numpy as np
from PIL import Image
from research.v3_common import *
from research.v3_cpu import fallback
from research.v3_metrics import scoring,summary

READER='rapid_v4'
BASES=('original','v1','control_42','partial_42','control_31415','partial_31415')
MODELS=BASES+tuple('source_'+str(s) for s in CONFIG['seeds'])

def fusion_signature():
    return stable_hash(dict(source_signature=signature(),code=sha(ROOT/'research/v3_fusion.py'),
        parser=sha(ROOT/'research/v3_cpu.py'),protocol=sha(ROOT/'research/V3_FUSION_PROTOCOL.md')))

def register():
    if list((R2CACHE/'predictions').glob('test_*')) or list((CACHE/'predictions').glob('test_*')):raise ValueError('Cannot register a new method after test generation')
    save(OUT/'fusion_registration.json',dict(signature=fusion_signature(),source_signature=signature(),reader=READER,
        policy='Checksum-validated missing-field fallback; no overwrites or century inference',
        selected_component_rule='Original V3 development-selected VLM only',test_inference_started=False,
        created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),human_validation_available=False))

def compose(fields,predictions):
    merged,info=fallback(fields,predictions,True)
    return merged,{k:('model' if k in fields else 'mrz') for k in merged},info

def verify(role=None):
    reg=read(OUT/'fusion_registration.json')
    if reg['signature']!=fusion_signature():raise ValueError('Secondary method changed after registration')
    if role=='test':
        pub=read(OUT/'lock_publication.json')
        if pub['fusion_lock_sha256']!=sha(OUT/'fusion_lock.json'):raise ValueError('Secondary seal not published')

def evaluate(role):
    from research.vlm_analysis import tolerant
    verify(role);records={};sig=fusion_signature()
    for key in MODELS:
        cache=R2CACHE if key in BASES else CACHE;outputs=[]
        for row in load(role):
            token=hashlib.sha256(row['uid'].encode()).hexdigest()
            original=read(cache/'predictions'/f'{role}_{key}'/(token+'.json'))
            ocr=read(CACHE/'cpu_raw'/role/READER/(token+'.json'))
            if original['input_sha256']!=row['input_sha256'] or ocr['input_sha256']!=row['input_sha256']:raise ValueError('Hybrid inputs differ')
            fields,_=tolerant(original['_private_text']);start=time.perf_counter()
            fields,origins,info=compose(fields,ocr['predictions']);text=json.dumps(fields,ensure_ascii=False)
            metrics,_=scoring(row,text)
            result=dict(uid=row['uid'],physical_id=row['physical_id'],source=row['source'],capture=row['capture'],
                model=key,input_sha256=row['input_sha256'],model_sha256=original['model_sha256'],signature=sig,**metrics,
                added_fields=info['added'],prediction_sha256=hashlib.sha256(text.encode()).hexdigest(),
                wall_seconds=original['wall_seconds']+ocr['wall_seconds']+time.perf_counter()-start,
                latency_is_sum_of_component_timers=True,shared_CPU_OCR=True,_private_text=text,_private_origins=origins)
            save(CACHE/'fusion'/role/key/(token+'.json'),result)
            outputs.append({k:v for k,v in result.items() if not k.startswith('_private')})
        records[key]=dict(rows=outputs,summary=summary(outputs))
    save(OUT/f'{role}_fusion.json',dict(signature=sig,reader=READER,shared_CPU_OCR=True,new_benchmark_VLM_calls=0,models=records))

def seal():
    verify();lock=read(OUT/'test_lock.json');key=lock['selected_model']
    base=read(OUT/'development_comparison.json')['summaries'][key]
    fused=read(OUT/'development_fusion.json')['models'][key]['summary']
    use=fused['f1']>base['f1'] and fused['unsupported_nonempty']<=base['unsupported_nonempty']
    cpu=max(read(OUT/'development_cpu.json')['summaries'].values(),key=lambda s:s['f1']);chosen=fused if use else base
    save(OUT/'fusion_lock.json',dict(signature=fusion_signature(),source_lock_sha256=sha(OUT/'test_lock.json'),
        component=key,component_model_sha256=lock['models'][key]['sha256'],use_fusion_on_development=use,
        deployment_approved=chosen['f1']>=cpu['f1'] and chosen['unsupported_nonempty']<=cpu['unsupported_nonempty'],
        reader=READER,base_development=base,hybrid_development=fused,test_scored=False))

def online(image,fields,profile,engine,views):
    start=time.perf_counter()
    view,_=views.prepare(Image.fromarray(cv2.cvtColor(image,cv2.COLOR_BGR2RGB)),profile)
    predictions=engine.ocr(cv2.cvtColor(np.asarray(view),cv2.COLOR_RGB2BGR),READER)['predictions']
    merged,origins,info=compose(fields,predictions)
    return merged,origins,dict(**info,cpu_seconds=time.perf_counter()-start)

def fresh():
    from peft import PeftModel
    from research.v3_study import adapter_for
    from research.v2_study import panel
    from research.v2_runtime import VLM
    from research.recovery_runtime import RecoveryEngine
    from research.v2_inputs import Views
    from research.vlm_analysis import tolerant
    verify('test');seal0=read(OUT/'fusion_lock.json');key=seal0['component'];profile=read(OUT/'test_lock.json')['profile']
    if not seal0['use_fusion_on_development']:
        save(OUT/'fusion_fresh.json',dict(signature=fusion_signature(),component=key,additional_VLM_and_CPU_calls=0,
            groups=0,mismatches=0,rows=[],skipped_because_not_promoted_on_development=True))
        return
    model=VLM(42,profile);adapter,_=adapter_for(key)
    if adapter:model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(adapter),is_trainable=False)
    engine=RecoveryEngine();views=Views();samples={r['uid']:r for r in load('test')};results=[]
    reference={r['uid']:r for r in read(OUT/'test_fusion.json')['models'][key]['rows']}
    for item in panel('test',4):
        row=samples[item['uid']]
        for repeat in (1,2):
            token=hashlib.sha256((row['uid']+'/'+str(repeat)).encode()).hexdigest();path=CACHE/'fusion_fresh'/(token+'.json')
            if path.exists():result=read(path)
            else:
                start=time.perf_counter()
                bgr=cv2.imread(str(ROOT/row['path']));pred=model.fresh(Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)))
                fields,_=tolerant(pred['text']);fields,origins,info=online(bgr,fields,profile,engine,views)
                text=json.dumps(fields,ensure_ascii=False);digest=hashlib.sha256(text.encode()).hexdigest();metrics,_=scoring(row,text)
                result=dict(signature=fusion_signature(),uid=row['uid'],repeat=repeat,input_sha256=row['input_sha256'],**metrics,
                    prediction_sha256=digest,identical=digest==reference[row['uid']]['prediction_sha256'],
                    wall_seconds=time.perf_counter()-start,_private_text=text,_private_origins=origins)
                save(path,result)
            if result['signature']!=fusion_signature() or result['input_sha256']!=row['input_sha256']:raise ValueError('Hybrid fresh cache differs')
            results.append({k:v for k,v in result.items() if not k.startswith('_private')});print('HYBRID_FRESH',len(results),16,flush=True)
    save(OUT/'fusion_fresh.json',dict(signature=fusion_signature(),component=key,additional_VLM_and_CPU_calls=16,
        groups=8,mismatches=sum(not r['identical'] for r in results),rows=results,
        p50_seconds=float(np.percentile([r['wall_seconds'] for r in results],50)),p95_seconds=float(np.percentile([r['wall_seconds'] for r in results],95))))

def audit():
    verify('test')
    from research.vlm_analysis import tolerant
    replayed=0
    for role in ('development','test'):
        samples={r['uid']:r for r in load(role)};data=read(OUT/f'{role}_fusion.json')
        if data['signature']!=fusion_signature():raise ValueError('Hybrid result signature differs')
        for key in MODELS:
            value=data['models'][key]
            if len(value['rows'])!=len(samples) or {r['uid'] for r in value['rows']}!=set(samples):raise ValueError('Hybrid coverage differs')
            cache=R2CACHE if key in BASES else CACHE
            for row in value['rows']:
                token=hashlib.sha256(row['uid'].encode()).hexdigest()
                original=read(cache/'predictions'/f'{role}_{key}'/(token+'.json'));ocr=read(CACHE/'cpu_raw'/role/READER/(token+'.json'))
                if original['input_sha256']!=samples[row['uid']]['input_sha256'] or ocr['input_sha256']!=samples[row['uid']]['input_sha256']:raise ValueError('Hybrid replay input differs')
                if hashlib.sha256(original['_private_text'].encode()).hexdigest()!=original['prediction_sha256']:raise ValueError('Original generation bytes differ')
                fields,_=tolerant(original['_private_text']);merged,_,_=compose(fields,ocr['predictions']);text=json.dumps(merged,ensure_ascii=False)
                metrics,_=scoring(samples[row['uid']],text)
                if any(row[k]!=v for k,v in metrics.items()) or hashlib.sha256(text.encode()).hexdigest()!=row['prediction_sha256']:raise ValueError('Hybrid raw replay differs')
                if row['model_sha256']!=read(OUT/'test_lock.json')['models'][key]['sha256']:raise ValueError('Hybrid model differs from lock')
                replayed+=1
            if summary(value['rows'])!=value['summary']:raise ValueError('Hybrid summary differs')
    repeats=read(OUT/'fusion_fresh.json');key=read(OUT/'fusion_lock.json')['component'];expected={r['uid']:r for r in read(OUT/'test_fusion.json')['models'][key]['rows']}
    pairs=set()
    for row in repeats['rows']:
        token=hashlib.sha256((row['uid']+'/'+str(row['repeat'])).encode()).hexdigest();private=read(CACHE/'fusion_fresh'/(token+'.json'))
        digest=hashlib.sha256(private['_private_text'].encode()).hexdigest()
        if row['signature']!=fusion_signature() or row['prediction_sha256']!=digest or expected[row['uid']]['prediction_sha256']!=digest:raise ValueError('Hybrid fresh replay differs')
        pairs.add((row['uid'],row['repeat']))
    expected_calls=16 if read(OUT/'fusion_lock.json')['use_fusion_on_development'] else 0
    if len(pairs)!=expected_calls or repeats['mismatches']:raise ValueError('Hybrid repeats incomplete or nondeterministic')
    save(OUT/'fusion_audit.json',dict(status='passed',signature=fusion_signature(),rows_replayed=replayed,fresh_calls=expected_calls,
        primary_training_policy_hypothesis_unchanged=True,human_annotations_used=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['register','development','test','seal','fresh','audit']);a=p.parse_args().action
    if a=='register':register()
    elif a in ('development','test'):evaluate(a)
    else:globals()[a]()
