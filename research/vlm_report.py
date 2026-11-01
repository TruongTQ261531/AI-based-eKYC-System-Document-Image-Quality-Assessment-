"""Separate prediction replay, grouped intervals and transparent LoRA report."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from research.vlm_setup import ROOT,CACHE,OUT,save,sha
from research.vlm_data import load
from research.vlm_runtime import signature,parsed,score,aggregate

MODELS=['original','seed_42','seed_31415']


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))


def audit():
    lock=read('test_lock.json');sig=signature()
    if lock['signature']!=sig:raise ValueError('Study changed after test lock')
    samples={r['uid']:r for r in load()};total=0;repeat={};published={}
    for role in ('development','test'):
        for model in MODELS:
            for pass_id in ([1,2,3] if role=='test' else [1]):
                result=read(f'{role}_{model}_{pass_id}.json')
                if result['signature']!=sig:raise ValueError('Published source changed')
                expected=80 if role=='development' else 120 if pass_id==1 else 12
                if len(result['rows'])!=expected:raise ValueError('Missing evaluation cases')
                rows=[]
                for row in result['rows']:
                    sample=samples[row['uid']]
                    path=CACHE/'predictions'/f'{role}_{model}_{pass_id}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
                    private=json.loads(path.read_text(encoding='utf-8'))
                    fields,valid=parsed(private['_private_text']);actual=score(sample['target'],fields,valid)
                    actual['masked_field_outputs']=sum(f.get('occluded',False) and f['key'] in fields for f in sample['fields'])
                    if any(row[k]!=v for k,v in actual.items()):raise ValueError('Public metric mismatch')
                    if fields!=private['_private_fields']:raise ValueError('Private parsed fields differ')
                    if hashlib.sha256(private['_private_text'].encode()).hexdigest()!=row['prediction_sha256']:raise ValueError('Prediction changed')
                    if row['model_sha256']!=result['model_sha256']:raise ValueError('Wrong adapter provenance')
                    if any(k.startswith('_private') or k in ('target','text','fields') for k in row):raise ValueError('Private public key')
                    rows.append(row);total+=1
                    if role=='test':repeat.setdefault((model,row['uid']),[]).append(row['prediction_sha256'])
                if aggregate(rows)!=result['summary']:raise ValueError('Aggregate differs')
                if pass_id==1:published[(role,model)]=rows
    if any(len(values)==3 and len(set(values))!=1 for values in repeat.values()):raise ValueError('Fresh repeats differ')
    cpu_count=0
    for role in ('development','test'):
        result=read(role+'_ocr.json')
        if result['signature']!=sig:raise ValueError('CPU baseline source changed')
        for row in result['rows']:
            sample=samples[row['uid']]
            path=CACHE/'cpu_baseline'/sig/role/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
            record=json.loads(path.read_text(encoding='utf-8'))
            private=next(x for x in record['rows'] if x['model']==row['model'])
            actual=score(sample['target'],private['_private_fields'],True)
            actual['masked_field_outputs']=sum(f.get('occluded',False) and f['key'] in private['_private_fields'] for f in sample['fields'])
            if any(row[k]!=v for k,v in actual.items()):raise ValueError('CPU metric differs')
            cpu_count+=1
        for model,value in result['summaries'].items():
            if aggregate([r for r in result['rows'] if r['model']==model])!=value:raise ValueError('CPU aggregate differs')
    groups={}
    for row in samples.values():groups.setdefault(row['role'],set()).add(row['physical_id'])
    if any(groups[a]&groups[b] for a in groups for b in groups if a!=b):raise ValueError('Identity leakage')
    intervals=[];rng=np.random.default_rng(20261101)
    for candidate in MODELS[1:]:
        # Paired ratio of aggregate exact fields, resampling entire document IDs.
        ids=sorted({r['physical_id'] for r in published[('test','original')]})
        by={}
        for key in ('original',candidate):
            by[key]={uid:[r for r in published[('test',key)] if r['physical_id']==uid] for uid in ids}
        differences=[]
        for _ in range(2000):
            selected=rng.choice(ids,len(ids),replace=True)
            totals={}
            for key in ('original',candidate):
                rr=[r for uid in selected for r in by[key][uid]]
                totals[key]=aggregate(rr)['f1']
            differences.append(totals[candidate]-totals['original'])
        point=aggregate(published[('test',candidate)])['f1']-aggregate(published[('test','original')])['f1']
        intervals.append(dict(candidate=candidate,comparator='original',physical_ids=len(ids),
            f1_difference=point,ci95=np.quantile(differences,[.025,.975]).tolist(),bootstrap_draws=2000,
            exploratory=True,multiplicity_adjusted=False))
    result=dict(status='passed',signature=sig,vlm_rows_replayed=total,cpu_rows_replayed=cpu_count,
        repeated_groups=sum(len(x)==3 for x in repeat.values()),repeat_mismatches=0,metric_mismatches=0,
        paired_intervals=intervals,independent_human_annotation=False,
        audit_scope='separate replay of saved outputs with the frozen scorer; not independent human verification')
    save(OUT/'audit.json',result);print(json.dumps(result),flush=True)


def report():
    audit_result=read('audit.json')
    if audit_result['signature']!=signature():raise ValueError('Audit source changed')
    records={m:read(f'test_{m}_1.json') for m in MODELS}
    cpu=read('test_ocr.json');lock=read('test_lock.json');smoke=read('smoke.json')
    lines=['# Fine-tune Vintern local: kết quả thực tế','',
        'Đây là thử nghiệm LoRA bổ sung trên SPECIMEN tổng hợp, tách khỏi V4 và bản mentor. '
        'Fine-tune mô hình có sẵn không tự tạo novelty hoặc bảo đảm CORE B.','',
        '720 ảnh / 144 mock document IDs; train480, development80, calibration40, test120. '
        'Tách theo giấy tờ gốc; cùng generator và hai bố cục/hai font giữa các tập. '
        'Không có ảnh camera mới hoặc nhãn legibility độc lập.','',
        '| Phương án | Đúng trường / GT | Precision | Recall | F1 | JSON hợp lệ | Xuất trường che kín |',
        '|---|---:|---:|---:|---:|---:|---:|']
    summaries={**cpu['summaries'],**{k:v['summary'] for k,v in records.items()}}
    for key,value in summaries.items():
        lines.append(f"|{key}|{value['correct']}/{value['reference']}|{value['precision']:.4f}|{value['recall']:.4f}|{value['f1']:.4f}|{value['json_valid_rate']:.4f}|{value['masked_field_outputs']}|")
    lines+=['','Đếm đúng theo cặp khóa–giá trị; ngày/giới tính có canonicalization, vẫn lưu literal exact. '
        'Extra keys ngoài reference có thể chứa giá trị còn nhìn thấy nhưng nhãn bị cắt; '
        'không tự gán tất cả thành hallucination. Trường che kín bằng mặt nạ được đếm riêng.','',
        f"GPU smoke: {smoke['optimizer_steps_continuous']} bước thật, resume thêm{smoke['resumed_steps']} bước; "
        f"chênh lệch adapter tối đa {smoke['resume_max_abs_difference']}; "
        f"VRAM allocated đỉnh {smoke['training_peak_allocated_bytes']/2**30:.3f} GiB.",
        '',f"Lựa chọn trên development: {lock['selected_model']}; cổng triển khai đạt: {lock['deployment_approved']}.",
        'Lựa chọn checkpoint/seed đã khóa trước khi chấm test. Hai seed là hai lần huấn luyện, '
        'không phải hai bộ dữ liệu độc lập. CI bootstrap theo physical ID được ghi trong audit.json; '
        'các so sánh là exploratory và chưa điều chỉnh nhiều phép thử.','',
        f"Audit: {audit_result['vlm_rows_replayed']} hàng VLM, {audit_result['cpu_rows_replayed']} hàng OCR; "
        f"{audit_result['repeated_groups']} nhóm lặp, không có sai khác score/repeat.",
        '', 'Thời gian trong các file test_* là suy luận ngôn ngữ với visual features đã cache; '
        'không được coi là thời gian đầu cuối. Feature setup và model cold-load được lưu riêng; '
        'OCR chạy CPU, VLM chạy GPU nên không diễn giải chênh lệch như so cùng backend. '
        'Đo fresh-online riêng trước khi nêu tốc độ triển khai.','',
        'Weights gốc và adapter lưu trong research/cache/vlm_lora_v1, không đưa lên Git. '
        'Code, phiên bản/checksum, manifest, log số và kết quả được lưu trong nhánh nghiên cứu.','',
        'Các điểm còn thiếu cho paper: kiểm chứng ảnh chụp vật lý độc lập, người chấm legibility, '
        'đối chiếu closest prior và phạm vi đóng góp cụ thể. Kết quả của corpus nhỏ này không '
        'chứng minh khả năng nhận mọi giấy tờ thật, chống giả khuôn mặt hoặc phê duyệt danh tính.','']
    (ROOT/'research/VLM_RESULTS_VI.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    save(OUT/'report_provenance.json',dict(signature=signature(),report_sha256=sha(ROOT/'research/VLM_RESULTS_VI.md'),
        audit_sha256=sha(OUT/'audit.json'),model_lock_sha256=sha(OUT/'test_lock.json')))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','report']);args=p.parse_args()
    audit() if args.action=='audit' else report()
