"""Three frozen pixel-only readers; private raw outputs, all scheduled cases retained."""
import argparse
import importlib.metadata
import time
import uuid
import cv2
import numpy as np
from PIL import Image,ImageOps
from research.labels_common import *
from research.labels_metrics import evaluate,summary

MODELS=('rapid_v4','rapid_latin_v5','partial_42')

def setup():
    import torch
    from research.recovery_assets import prepare,CACHE as ASSETS
    prepare()
    import rapidocr_onnxruntime
    from research.vlm_setup import OUT as V1_OUT
    train=read(ROOT/'research/results/vlm_lora_v2_r2/train_partial_42.json')
    adapter=ROOT/train['selected_checkpoint']
    if sha(adapter/'adapter_model.safetensors')!=train['selected_adapter_sha256']:raise ValueError('Current partial adapter changed')
    package=Path(rapidocr_onnxruntime.__file__).parent
    paths=list((package/'models').glob('*.onnx'))
    paths += [ASSETS/'latin_PP-OCRv5_rec_mobile.onnx',ASSETS/'lcnet100.onnx',ROOT/'research/cache/docaligner/fastvit_sa24.onnx']
    if len(paths)<6 or any(not p.is_file() for p in paths):raise ValueError('Existing OCR/localizer weights incomplete; no downloads')
    reused=('v2_cpu.py','v3_cpu.py','v2_inputs.py','v2_runtime.py','vlm_runtime.py','v3_sources.py','v3_metrics.py','recovery_runtime.py','recovery_assets.py')
    device=torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    value=dict(models=list(MODELS),adapter_path=adapter.relative_to(ROOT).as_posix(),adapter_sha256=sha(adapter/'adapter_model.safetensors'),
        adapter_config_sha256=sha(adapter/'adapter_config.json'),adapter_selection='Existing current partial_42; no selection using new panel',
        base_assets_sha256=sha(V1_OUT/'assets.json'),profile='rect2',max_new_tokens=384,seed=42,host_threads=2,
        reused_sources={name:sha(ROOT/'research'/name) for name in reused},
        onnx_weights=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in paths],
        packages={p:importlib.metadata.version(p) for p in ('torch','transformers','peft','onnxruntime','rapidocr-onnxruntime','Pillow','numpy')},
        gpu=None if device is None else dict(name=device.name,physical_memory_bytes=device.total_memory),
        CPU_readers='Existing shared detector/classifier; v4 recognizer or Latin PP-OCRv5 recognizer',
        predictor_annotation_access=False,new_model_training=False,new_dependencies_installed=False)
    save(OUT/'models.json',value);print('LABEL_MODELS_FROZEN',flush=True)

def verify_lock():
    freeze_previous();sig=signature();lock=read(OUT/'test_lock.json');pub=read(OUT/'prepare_publication.json')
    if lock['signature']!=sig or pub['signature']!=sig or pub['lock_sha256']!=sha(OUT/'test_lock.json'):
        raise ValueError('Published annotation/evaluation lock required')
    return sig

def predictor(name):
    manifest=read(OUT/'models.json')
    for file,expected in manifest['reused_sources'].items():
        if sha(ROOT/'research'/file)!=expected:raise ValueError('Reused reader/preprocessing changed')
    if name=='partial_42':
        import torch
        from peft import PeftModel
        from research import v2_runtime
        model=v2_runtime.VLM(42,'rect2');torch.set_num_threads(2)
        path=ROOT/manifest['adapter_path']
        if sha(path/'adapter_model.safetensors')!=manifest['adapter_sha256']:raise ValueError('Adapter differs')
        model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
        def predict(image):
            torch.cuda.reset_peak_memory_stats();start=time.process_time();out=model.fresh(image)
            return dict(out,cpu_seconds=time.process_time()-start,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                        peak_reserved_bytes=torch.cuda.max_memory_reserved(),predictor_receives='pixels_only')
        return predict
    if name not in MODELS[:2]:raise ValueError('Unknown frozen reader')
    for weight in manifest['onnx_weights']:
        if sha(Path(weight['path']))!=weight['sha256']:raise ValueError('Frozen OCR weight changed')
    from research.recovery_runtime import RecoveryEngine
    from research.v2_inputs import Views
    from research.v2_cpu import extract
    from research.v3_cpu import fallback
    engine=RecoveryEngine();views=Views()
    def predict(image):
        wall=time.perf_counter();cpu=time.process_time();view,meta=views.prepare(image,'rect2')
        result=engine.ocr(cv2.cvtColor(np.asarray(view),cv2.COLOR_RGB2BGR),name)
        fields,info=fallback(extract(result['predictions']),result['predictions'],strict=True)
        return dict(text=json.dumps(fields,ensure_ascii=False),wall_seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu,
                    generated_tokens=None,visual_features_cached=False,predictor_receives='pixels_only',
                    _private_boxes=result['predictions'],**meta,**info)
    return predict

def event(value):
    CACHE.mkdir(parents=True,exist_ok=True)
    with (CACHE/'execution_events.jsonl').open('a',encoding='utf-8',newline='\n') as stream:
        stream.write(canonical(dict(utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**value))+'\n');stream.flush()

def execute(predict,row,name,stage):
    start=time.perf_counter();image=open_image(row);decode=time.perf_counter()-start
    call_id=uuid.uuid4().hex;event(dict(call_id=call_id,status='begin',model=name,stage=stage,uid=row['uid']))
    try:
        out=predict(image)
    except Exception as exc:
        event(dict(call_id=call_id,status='failed',model=name,stage=stage,error_type=type(exc).__name__));raise
    event(dict(call_id=call_id,status='completed',model=name,stage=stage,output_sha256=hashlib.sha256(out['text'].encode()).hexdigest()))
    return dict(out,file_decode_seconds=decode,timing_scope='decoded RGB through rectification/OCR/parser; file decode measured separately')

def open_image(row):
    path=ROOT/row['path']
    if sha(path)!=row['input_sha256']:raise ValueError('Input bytes changed')
    with Image.open(path) as raw:
        image=ImageOps.exif_transpose(raw) if row['coordinate_mode']=='exif_display' else raw
        return image.convert('RGB')

def record(row,out,name,sig):
    metric=evaluate(row,out['text'])
    public=dict(signature=sig,uid=row['uid'],physical_id=row['physical_id'],source=row['source'],role=row['role'],
        device=row['device'],layout=row['layout'],condition=row['condition'],capture=row['capture'],model=name,
        input_sha256=row['input_sha256'],pixel_sha256=row['pixel_sha256'],**metric,
        prediction_sha256=hashlib.sha256(out['text'].encode()).hexdigest(),
        hit_token_limit=bool(out.get('generated_tokens')==384),
        **{k:v for k,v in out.items() if k!='text' and not k.startswith('_private')})
    return public

def run(name):
    sig=verify_lock();rows=sorted(sample_rows(),key=lambda r:(r['role']!='development',r['uid']))
    predict=predictor(name);records=[];new=0;resumed=0
    for i,row in enumerate(rows,1):
        path=CACHE/'predictions'/name/(uid(row['uid'])+'.json')
        if path.exists():
            raw=read(path);resumed+=1
            if raw['signature']!=sig or raw['input_sha256']!=row['input_sha256']:raise ValueError('Raw prediction cache differs')
        else:
            out=execute(predict,row,name,'main');public=record(row,out,name,sig)
            raw=dict(signature=sig,input_sha256=row['input_sha256'],uid=row['uid'],output=out,public=public)
            save(path,raw);new+=1
        recomputed=record(row,raw['output'],name,sig)
        if recomputed!=raw['public']:raise ValueError('Saved score differs from raw output')
        records.append(recomputed)
        if i%4==0 or i==len(rows):progress('evaluation',i,len(rows),model=name,new_calls=new,resumed=resumed)
    save(OUT/f'evaluation_{name}.json',dict(signature=sig,rows=records,summaries={r:summary([x for x in records if x['role']==r]) for r in ('development','test')},
        scheduled_calls=len(rows),prediction_source='All original pixels; no inherited OCR outputs',
        counts_are_image_calls_not_independent_documents=True))

def fresh_panel():
    rows=sample_rows('test');panel=[]
    for source in ('authored','midv2020'):
        pid=min({r['physical_id'] for r in rows if r['source']==source},key=lambda p:uid('labels-fresh/'+p))
        panel.extend(r for r in rows if r['physical_id']==pid and r['capture'] in ('full','value_mask') and
                     (source!='authored' or r['condition']=='new_layout_new_font'))
    if len(panel)!=4:raise ValueError('Four fixed fresh inputs required')
    return panel

def fresh(name):
    sig=verify_lock();predict=predictor(name);refs={r['uid']:r for r in read(OUT/f'evaluation_{name}.json')['rows']};rows=[]
    for sample in fresh_panel():
        for repeat in (1,2):
            path=CACHE/'fresh'/name/(uid(sample['uid']+'/'+str(repeat))+'.json')
            if path.exists():raw=read(path)
            else:
                out=execute(predict,sample,name,'fresh');public=record(sample,out,name,sig)
                raw=dict(signature=sig,input_sha256=sample['input_sha256'],uid=sample['uid'],output=out,public=public,repeat=repeat)
                save(path,raw)
            if raw['signature']!=sig or raw['input_sha256']!=sample['input_sha256']:raise ValueError('Fresh record differs')
            public=record(sample,raw['output'],name,sig)
            if public!=raw['public']:raise ValueError('Fresh rescoring differs')
            rows.append(dict(public,repeat=repeat,identical_to_main=public['prediction_sha256']==refs[sample['uid']]['prediction_sha256']))
            progress('fresh',len(rows),8,model=name)
    save(OUT/f'fresh_{name}.json',dict(signature=sig,rows=rows,additional_generation_calls=8,distinct_input_views=4,
        document_instances=2,mismatches=sum(not r['identical_to_main'] for r in rows)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['setup','run','fresh']);p.add_argument('--model',choices=MODELS,default=MODELS[0]);a=p.parse_args()
    if a.action=='setup':setup()
    elif a.model=='partial_42':
        from research.vlm_train import process_lock
        with process_lock():run(a.model) if a.action=='run' else fresh(a.model)
    else:run(a.model) if a.action=='run' else fresh(a.model)
