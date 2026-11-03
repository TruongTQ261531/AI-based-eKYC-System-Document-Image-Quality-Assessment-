"""Development-only host-thread probe, retaining both timings and token hashes."""
import hashlib
import statistics
import time
from research.fc_common import *


def probe():
    import torch
    from peft import PeftModel
    from research import v2_runtime
    from research.hp_common import baseline
    if (OUT/'runtime_choice.json').exists():
        print('FC_RUNTIME_PROBE_ALREADY_SAVED', flush=True)
        return
    freeze_previous()
    v2_runtime.CACHE=CACHE
    v2_runtime.PILOT_CACHE=HP_CACHE
    model=v2_runtime.VLM(42, 'rect2')
    rows=read(HP_DATA/'samples.json')
    panel=[]
    for source in ('authored','midv2020'):
        ids=sorted({r['physical_id'] for r in rows if r['role']=='development' and r['source']==source},
            key=lambda p:hashlib.sha256(('fc-host-probe/'+p).encode()).digest())[:1]
        panel.extend(r for r in rows if r['role']=='development' and r['physical_id'] in ids
                     and r['capture'] in ('full','pair_mask'))
    if len(panel)!=4:
        raise ValueError('Expected four development inputs')
    for row in panel:
        model.features(row)
    model.offload_vision()
    path,digest=baseline('uniform_42')
    model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(path),is_trainable=False)
    generated=[]
    original=model.model.language_model.generate
    def capture(*args,**kwargs):
        result=original(*args,**kwargs)
        generated[:] = result[0].detach().cpu().tolist()
        return result
    model.model.language_model.generate=capture
    warmups=[]
    for threads in (2,1):
        torch.set_num_threads(threads)
        started=time.perf_counter()
        model.infer_features(model.features(panel[0]),24)
        torch.cuda.synchronize()
        warmups.append(dict(threads=threads,seconds=time.perf_counter()-started,tokens=len(generated)))
    records=[]
    for i,row in enumerate(panel):
        for threads in ((2,1) if i%2==0 else (1,2)):
            torch.set_num_threads(threads)
            pred=model.infer(row)
            records.append(dict(uid=row['uid'],input_sha256=row['input_sha256'],threads=threads,
                token_ids_sha256=stable_hash(generated),prediction_sha256=hashlib.sha256(pred['text'].encode()).hexdigest(),
                generated_tokens=pred['generated_tokens'],wall_seconds=pred['wall_seconds']))
            save(CACHE/'runtime_probe_progress.json',dict(completed=len(records),total=8))
            print('FC_HOST_PROBE',len(records),threads,round(pred['wall_seconds'],3),flush=True)
    pairs=[[r for r in records if r['uid']==row['uid']] for row in panel]
    equal=all(p[0]['token_ids_sha256']==p[1]['token_ids_sha256'] for p in pairs)
    medians={str(n):statistics.median(r['wall_seconds'] for r in records if r['threads']==n) for n in (1,2)}
    chosen=1 if equal and medians['1']<medians['2'] else 2
    save(OUT/'runtime_choice.json',dict(chosen_inference_host_threads=chosen,training_host_threads=2,
        exact_token_parity_on_panel=equal,median_cached_seconds=medians,rows=records,warmups=warmups,
        rule='Choose1 only with identical generated token IDs on all four development inputs and lower median latency; otherwise2',
        scope='One frozen adapter, four development inputs, two host-thread settings; not global parity proof',
        model_sha256=digest,new_model_calls=10,probe_source_sha256=sha(ROOT/'research/fc_runtime_probe.py'),
        old_test_used=False,new_dependencies=False))
    print('FC_RUNTIME_CHOICE',chosen,medians,flush=True)


if __name__=='__main__':
    from research import vlm_train
    with vlm_train.process_lock():
        probe()
