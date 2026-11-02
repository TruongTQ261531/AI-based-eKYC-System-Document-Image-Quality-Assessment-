"""Post-hoc availability diagnostics; never edit primary generations or scores."""
import argparse
import hashlib
import numpy as np
from research.v2_common import *


def appendix(groups,names,destination):
    path=OUT/'execution_interruptions.json'
    if not path.exists():return []
    incident=read(path);affected={(r['model'],r['uid']) for r in incident['affected_generations']}
    summaries={}
    for key,rows in groups.items():
        kept=[r for r in rows if (key,r['uid']) not in affected]
        a=[r['wall_seconds'] for r in rows];b=[r['wall_seconds'] for r in kept]
        summaries[key]=dict(total=len(rows),excluded_from_latency_sensitivity_only=len(rows)-len(kept),
            raw_p50=float(np.percentile(a,50)),raw_p95=float(np.percentile(a,95)),raw_max=float(max(a)),
            sensitivity_p50=float(np.percentile(b,50)),sensitivity_p95=float(np.percentile(b,95)))
    save(destination/'latency_sensitivity.json',dict(post_hoc_descriptive=True,all_accuracy_rows_retained=True,
        raw_timers_retained=True,criterion='Only the generation overlapping the documented Windows battery sleep',
        incident_sha256=sha(path),models=summaries))
    text=['','## Gián đoạn nguồn điện và độ nhạy thời gian','',
        'Windows ghi nhận sleep do pin lúc 09:25:46 UTC và thức lại 14:45:48 UTC ngày 2026-11-02. '
        'Một lượt V1 đang sinh văn bản bị tính cả thời gian ngủ. Output, hash, số đo thời gian gốc và mọi hàng '
        'độ chính xác được giữ nguyên. Bảng sau là phân tích thời gian bổ sung sau khi phát hiện sự cố, '
        'chỉ bỏ đúng lượt có nhật ký sleep khỏi thống kê độ trễ; không bỏ các lượt OCR khó hoặc sai. '
        'Nguồn điện/chế độ GPU không được kiểm soát xuyên suốt; các con số này không thiết lập ưu thế tốc độ.','',
        '| Model | Số lượt | Lượt sleep | p50/p95 gốc (s) | p50/p95 bỏ lượt sleep (s) |',
        '|---|---:|---:|---:|---:|']
    for key,s in summaries.items():
        text.append(f"| {names[key]} | {s['total']} | {s['excluded_from_latency_sensitivity_only']} | {s['raw_p50']:.2f}/{s['raw_p95']:.2f} | {s['sensitivity_p50']:.2f}/{s['sensitivity_p95']:.2f} |")
    repeat=OUT/'interrupted_generation_replay.json'
    if repeat.exists():
        value=read(repeat)
        text+=['',f"Kiểm tra bổ sung: gọi lại {value['additional_cached_feature_generation_calls']} lượt bị gián đoạn "
            f"với cùng model/ảnh/profile, từ feature cache; số output khác hash: {value['mismatches']}. "
            'Đây là kiểm tra sau sự cố, tách riêng với 16 phép lặp ảnh mới và không thay kết quả gốc.']
    else:text+=['','Kiểm tra gọi lại riêng lượt bị gián đoạn còn chờ; chưa được coi là đã qua.']
    return text


def replay():
    from peft import PeftModel
    from research.vlm_train import process_lock
    from research.v2_runtime import VLM
    from research.v2_study import adapter_for
    incident=read(OUT/'execution_interruptions.json');seal0=read(OUT/'test_lock.json');samples={r['uid']:r for r in load('test')}
    results=[]
    with process_lock():
        for entry in incident['affected_generations']:
            key=entry['model'];row=samples[entry['uid']];adapter,digest=adapter_for(key)
            if digest!=seal0['models'][key]['sha256']:raise ValueError('Interrupted model differs from published lock')
            original=read(CACHE/'predictions'/f'test_{key}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json'))
            if original['prediction_sha256']!=entry['prediction_sha256'] or original['input_sha256']!=entry['input_sha256']:raise ValueError('Original interrupted record changed')
            model=VLM(42,seal0['profile']);model.offload_vision()
            if adapter:model.model.language_model=PeftModel.from_pretrained(model.model.language_model,str(adapter),is_trainable=False)
            prediction=model.infer(row);new_digest=hashlib.sha256(prediction['text'].encode()).hexdigest()
            record=dict(model=key,uid=row['uid'],input_sha256=row['input_sha256'],model_sha256=digest,
                original_prediction_sha256=original['prediction_sha256'],prediction_sha256=new_digest,
                identical=new_digest==original['prediction_sha256'],wall_seconds=prediction['wall_seconds'],
                visual_features_cached=True,_private_text=prediction['text'])
            save(CACHE/'interruption_replay'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json'),record)
            results.append({k:v for k,v in record.items() if not k.startswith('_private')})
            del model
    save(OUT/'interrupted_generation_replay.json',dict(post_hoc_availability_check=True,primary_accuracy_rows_unchanged=True,
        additional_cached_feature_generation_calls=len(results),new_unique_test_inputs=0,
        mismatches=sum(not r['identical'] for r in results),incident_sha256=sha(OUT/'execution_interruptions.json'),rows=results))
    if any(not r['identical'] for r in results):raise ValueError('Interrupted generation differs on replay; preserve both for review')
    print('INTERRUPTED_GENERATION_REPLAY_PASSED',len(results),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['replay']);p.parse_args();replay()
