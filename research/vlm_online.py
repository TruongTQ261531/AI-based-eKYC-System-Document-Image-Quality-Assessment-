"""Fresh image decoding + vision + generation timings, separate from cache runs."""
import gc
import hashlib
import json
import time

from PIL import Image
import torch

from research.vlm_setup import ROOT,CACHE,OUT,save,sha
from research.vlm_data import load
from research.vlm_runtime import VLM,pixels,signature,parsed,score


def main():
    from peft import PeftModel
    lock=json.loads((OUT/'test_lock.json').read_text(encoding='utf-8'));sig=signature()
    if lock['signature']!=sig:raise ValueError('Source changed after test lock')
    samples=load('test')
    ids=sorted({r['physical_id'] for r in samples},key=lambda x:hashlib.sha256(('vlm-repeat-v1/'+x).encode()).digest())[:6]
    panel=[r for r in samples if r['physical_id'] in ids and r['capture'] in ('full','value_mask')]
    rows=[];cold=[]
    for pass_id,models in [(1,['original','seed_42','seed_31415']),(2,['seed_31415','seed_42','original'])]:
        for key in models:
            model=VLM()
            if key!='original':
                record=lock['adapters'][key.split('_')[1]];path=ROOT/record['selected_checkpoint']
                if sha(path/'adapter_model.safetensors')!=record['selected_adapter_sha256']:raise ValueError('Adapter changed')
                model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
            model.model.eval();cold.append(dict(model=key,pass_id=pass_id,base_model_load_seconds=model.cold_load_seconds))
            order=panel if pass_id==1 else list(reversed(panel))
            for i,sample in enumerate(order,1):
                path=CACHE/'online'/f'{pass_id}_{key}'/(hashlib.sha256(sample['uid'].encode()).hexdigest()+'.json')
                if path.exists():
                    record=json.loads(path.read_text(encoding='utf-8'))
                    if record['signature']!=sig:raise ValueError('Online source changed')
                else:
                    torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.perf_counter()
                    if sha(ROOT/sample['path'])!=sample['input_sha256']:raise ValueError('Online input changed')
                    with Image.open(ROOT/sample['path']) as image:tensor=pixels(image).to(device='cuda',dtype=model.dtype)
                    with torch.no_grad():feature=model.model.extract_feature(tensor)
                    torch.cuda.synchronize();vision_end=time.perf_counter()
                    text,tokens=model.infer_features(feature);torch.cuda.synchronize();end=time.perf_counter()
                    fields,valid=parsed(text)
                    record=dict(signature=sig,uid=sample['uid'],model=key,pass_id=pass_id,
                        input_sha256=sample['input_sha256'],wall_seconds=end-start,
                        decode_and_vision_seconds=vision_end-start,generation_seconds=end-vision_end,
                        generated_tokens=tokens,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                        peak_reserved_bytes=torch.cuda.max_memory_reserved(),visual_features_cached=False,
                        prediction_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        **score(sample['target'],fields,valid),_private_text=text,_private_fields=fields)
                    cached=json.loads((CACHE/'predictions'/f'test_{key}_1'/(hashlib.sha256(sample['uid'].encode()).hexdigest()+'.json')).read_text(encoding='utf-8'))
                    record['cached_output_identical']=record['prediction_sha256']==cached['prediction_sha256']
                    save(path,record)
                rows.append({k:v for k,v in record.items() if not k.startswith('_private')})
                if i%4==0:print('FRESH_ONLINE',pass_id,key,i,'/',len(order),flush=True)
            del model;gc.collect();torch.cuda.empty_cache()
    save(OUT/'fresh_online.json',dict(signature=sig,script_sha256=sha(__file__),rows=rows,cold_loads=cold,
        calls=len(rows),cached_output_mismatches=sum(not r['cached_output_identical'] for r in rows),
        timing_scope='image file hash/decode, preprocessing, vision and generation; resident model; excludes HTTP',
        all_calls_recomputed_vision=True))


if __name__=='__main__':
    from research.vlm_train import process_lock
    with process_lock():main()
