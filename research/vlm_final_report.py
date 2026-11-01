"""Complete control audit/report; primary learner, V4 and mentor stay frozen."""
import argparse
import hashlib
import json
import numpy as np
from research.vlm_setup import ROOT,CACHE,OUT,save,sha
from research.vlm_data import load
from research.vlm_runtime import signature,parsed,score,aggregate
from research.vlm_control import signature as control_signature

MODELS=['original','seed_42','seed_31415']
CONTROL='control_seed_42'
LABELS={'ocr_raw_layout':'OCR CPU + layout','ocr_existing_web':'OCR web cũ (CPU)',
    'original':'Vintern gốc','seed_42':'LoRA seed42','seed_31415':'LoRA seed31415',CONTROL:'LoRA đủ nội dung (đối chứng)'}


def read(name):return json.loads((OUT/name).read_text(encoding='utf-8'))


def panel(samples):
    ids=sorted({r['physical_id'] for r in samples},key=lambda x:hashlib.sha256(('vlm-repeat-v1/'+x).encode()).digest())[:6]
    return {r['uid'] for r in samples if r['physical_id'] in ids and r['capture'] in ('full','value_mask')}


def require_cases(rows,expected):
    uids=[r['uid'] for r in rows]
    if len(uids)!=len(set(uids)) or set(uids)!=set(expected):raise ValueError('Missing, duplicate or wrong cases')


def paired_interval(candidate,comparator,seed=20261101):
    ids=sorted({r['physical_id'] for r in comparator})
    if set(ids)!={r['physical_id'] for r in candidate}:raise ValueError('Unpaired physical IDs')
    totals=[np.array([[sum(r[k] for r in rows if r['physical_id']==uid)
                      for k in ('correct','reference','predicted')] for uid in ids],dtype=float)
            for rows in (candidate,comparator)]
    draw=np.random.default_rng(seed).integers(0,len(ids),size=(2000,len(ids)))
    a,b=[x[draw].sum(axis=1) for x in totals]
    delta=2*a[:,0]/np.maximum(a[:,1]+a[:,2],1)-2*b[:,0]/np.maximum(b[:,1]+b[:,2],1)
    point=[2*x[:,0].sum()/max(x[:,1:].sum(),1) for x in totals]
    return dict(physical_ids=len(ids),f1_difference=point[0]-point[1],
        ci95=np.quantile(delta,[.025,.975]).tolist(),bootstrap_draws=2000,
        exploratory=True,multiplicity_adjusted=False,resampling_unit='physical_id')


def audit():
    lock=read('test_lock.json');sig=signature();cl=read('control/test_lock.json')
    if lock['signature']!=sig or cl['signature']!=control_signature():raise ValueError('Source changed after lock')
    samples={r['uid']:r for r in load()};published={};repeats={};total=control_count=0
    variants=[(m,m,OUT,CACHE,sig,lock) for m in MODELS]
    variants.append((CONTROL,'seed_42',OUT/'control',CACHE/'control',control_signature(),cl))
    base=next(x['sha256'] for x in read('assets.json')['model'] if x['file']=='model.safetensors')
    for label,key,public,private_root,expected_sig,seal in variants:
        digest=base if key=='original' else seal['adapters'][key.split('_')[1]]['selected_adapter_sha256']
        if key!='original' and sha(ROOT/seal['adapters'][key.split('_')[1]]['selected_checkpoint']/'adapter_model.safetensors')!=digest:raise ValueError('Adapter changed')
        for role in ('development','test'):
            rs=[s for s in samples.values() if s['role']==role]
            for repeat in ([1,2,3] if role=='test' else [1]):
                result=json.loads((public/f'{role}_{key}_{repeat}.json').read_text(encoding='utf-8'))
                if result['signature']!=expected_sig or result['model_sha256']!=digest:raise ValueError('Model/source mismatch')
                require_cases(result['rows'],{s['uid'] for s in rs} if repeat==1 else panel(rs))
                for row in result['rows']:
                    sample=samples[row['uid']]
                    path=private_root/'predictions'/f'{role}_{key}_{repeat}'/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')
                    private=json.loads(path.read_text(encoding='utf-8'));fields,valid=parsed(private['_private_text'])
                    actual=score(sample['target'],fields,valid)
                    actual['masked_field_outputs']=sum(f.get('occluded',False) and f['key'] in fields for f in sample['fields'])
                    if any(row[k]!=v for k,v in actual.items()) or fields!=private['_private_fields']:raise ValueError('Metric mismatch')
                    if hashlib.sha256(private['_private_text'].encode()).hexdigest()!=row['prediction_sha256']:raise ValueError('Output hash mismatch')
                    if row['model_sha256']!=digest or row['input_sha256']!=sample['input_sha256']:raise ValueError('Input/model mismatch')
                    if any(row[k]!=sample[k] for k in ('physical_id','role','capture')):raise ValueError('Sample metadata mismatch')
                    if any(k.startswith('_private') or k in ('target','text','fields') for k in row):raise ValueError('Private public key')
                    total+=1;control_count+=label==CONTROL
                    if role=='test':repeats.setdefault((label,row['uid']),[]).append(row['prediction_sha256'])
                if aggregate(result['rows'])!=result['summary']:raise ValueError('Aggregate mismatch')
                if repeat==1:published[(role,label)]=result['rows']
    groups3=[x for x in repeats.values() if len(x)==3]
    if len(groups3)!=48 or any(len(set(x))!=1 for x in groups3):raise ValueError('Fresh repeats missing/differ')
    cpu_count=0
    for role in ('development','test'):
        result=read(role+'_ocr.json')
        if result['signature']!=sig:raise ValueError('CPU source mismatch')
        for model,value in result['summaries'].items():
            rows=[r for r in result['rows'] if r['model']==model]
            require_cases(rows,{s['uid'] for s in samples.values() if s['role']==role})
            for row in rows:
                sample=samples[row['uid']]
                record=json.loads((CACHE/'cpu_baseline'/sig/role/(hashlib.sha256(row['uid'].encode()).hexdigest()+'.json')).read_text(encoding='utf-8'))
                private=next(x for x in record['rows'] if x['model']==model)
                actual=score(sample['target'],private['_private_fields'],True)
                actual['masked_field_outputs']=sum(f.get('occluded',False) and f['key'] in private['_private_fields'] for f in sample['fields'])
                if any(row[k]!=v for k,v in actual.items()):raise ValueError('CPU metric mismatch')
                cpu_count+=1
            if aggregate(rows)!=value:raise ValueError('CPU aggregate mismatch')
            published[(role,model)]=rows
    groups={}
    for row in samples.values():groups.setdefault(row['role'],set()).add(row['physical_id'])
    if any(groups[a]&groups[b] for a in groups for b in groups if a!=b):raise ValueError('Identity leakage')
    if {k:len(v) for k,v in groups.items()}!={'train':96,'development':16,'calibration':8,'test':24}:raise ValueError('Role sizes mismatch')
    intervals=[]
    for i,(a,b) in enumerate((a,b) for a in MODELS[1:] for b in ('original','ocr_existing_web',CONTROL)):
        intervals.append(dict(candidate=a,comparator=b,**paired_interval(published[('test',a)],published[('test',b)],20261101+i)))
    slices=[dict(role=role,model=model,capture=c,**aggregate([r for r in rows if r['capture']==c]))
            for (role,model),rows in published.items() for c in sorted({r['capture'] for r in rows})]
    value=dict(status='passed',signature=sig,control_signature=control_signature(),vlm_rows_replayed=total-control_count,
        control_rows_replayed=control_count,cpu_rows_replayed=cpu_count,repeated_groups=len(groups3),
        repeat_mismatches=0,metric_mismatches=0,paired_intervals=intervals,slices=slices,
        calibration_images_used=0,test_physical_ids=24,test_rasters=120,independent_human_annotation=False,
        pretest_publication=read('pretest_publication.json'),secondary_analysis_sha256=sha(OUT/'format_analysis.json'),
        script_sha256=sha(__file__),audit_scope='replay saved outputs with frozen scorer; not independent human verification')
    save(OUT/'audit.json',value);print('AUDIT_PASSED',total,cpu_count,len(groups3),flush=True)


def timing(rows):
    v=[r['wall_seconds'] for r in rows]
    return f'{np.median(v):.2f} / {np.quantile(v,.95):.2f}'


def report():
    audit=read('audit.json');lock=read('test_lock.json');online=read('fresh_online.json');cpu=read('test_ocr.json')
    if audit['signature']!=signature() or audit['status']!='passed' or online['signature']!=signature():raise ValueError('Evidence mismatch')
    if sha(OUT/'format_analysis.json')!=audit['secondary_analysis_sha256']:raise ValueError('Analysis changed')
    records={m:read(f'test_{m}_1.json') for m in MODELS};records[CONTROL]=read('control/test_seed_42_1.json')
    secondary={r['model']:r for r in read('format_analysis.json')['results'] if r['role']=='test'}
    summaries={**cpu['summaries'],**{k:v['summary'] for k,v in records.items()}}
    text=['# Fine-tune Vintern local: kết quả thực tế','',
        'Thử nghiệm LoRA trên SPECIMEN tổng hợp, tách khỏi V4 và bản mentor. Fine-tune mô hình có sẵn không tự tạo novelty hay bảo đảm CORE B.','',
        f"Chọn **{lock['selected_model']}** trên development, trước test; cổng development đạt: **{lock['deployment_approved']}**. Không đổi lựa chọn theo test/đối chứng.",'',
        '## Dữ liệu và khóa trước test','',
        '720 ảnh/144 mock physical IDs: train480/96IDs, development80/16, calibration40/8, test120/24. Calibration chưa dùng. Tách theo ID và checksum ảnh; cùng generator, hai bố cục/hai font giữa các tập. GT giữ cặp nhãn–giá trị còn đủ trong raster và bỏ trường che kín. Đây là proxy hình học tổng hợp, không phải nhãn legibility từ người chấm. Chưa có ảnh camera mới hoặc held-out-layout.',
        f"Commit khóa trước test: `{audit['pretest_publication']['lock_commit']}`. Hai seed chính và một đối chứng:192 optimizer steps,768 presentations/lượt. Đối chứng chỉ full/corner_clip/blur_glare:288ảnh, cùng96IDs; chính480ảnh. Khớp compute và identities, không khớp số raster/epoch. Đối chứng phát sinh từ development, đã khai báo trước test.",'',
        '## Test chính','',
        '| Phương án | Đúng/reference | Precision | Recall | F1 strict | F1 bỏ fence/null | Đúng định dạng | Xuất trường che kín |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for k,v in summaries.items():
        sf=f"{secondary[k]['tolerant_summary']['f1']:.4f}" if k in secondary else '—'
        fmt=f"{v['json_valid_rate']:.4f}" if k in secondary else 'dict sẵn'
        text.append(f"|{LABELS[k]}|{v['correct']}/{v['reference']}|{v['precision']:.4f}|{v['recall']:.4f}|{v['f1']:.4f}|{sf}|{fmt}|{v['masked_field_outputs']}|")
    text+=['','Đúng theo cặp khóa–giá trị; ngày/giới tính canonicalization giống nhau, vẫn lưu literal exact. Định dạng extraction strict không phải chỉ JSON syntax: null/bool/nested/fence đều bị từ chối. Parser phụ bỏ một fence toàn bộ và null/empty; không sửa giá trị/ánh xạ bằng GT. OCR trả dict sẵn nên không dùng làm đối chứng formatting sinh. Extra keys có thể có giá trị còn thấy nhưng nhãn bị cắt; không tự coi tất cả là hallucination. Trường bị che kín được đếm riêng.','',
        '| VLM | Object parse được | Fence | Null/empty | Literal đúng | Extra | Missing |','|---|---:|---:|---:|---:|---:|---:|']
    for k,r in records.items():
        a=secondary[k];v=r['summary'];text.append(f"|{LABELS[k]}|{a['syntax_success']}/120|{a['fenced_outputs']}|{a['null_or_empty_values']}|{v['literal_correct']}|{v['extra_keys']}|{v['missing_keys']}|")
    text+=['','## Từng điều kiện chụp (F1 strict)','', '| Phương án | full | corner_clip | field_clip | blur_glare | value_mask |','|---|---:|---:|---:|---:|---:|']
    for k in summaries:
        vals=[next(s for s in audit['slices'] if s['role']=='test' and s['model']==k and s['capture']==c)['f1'] for c in ('full','corner_clip','field_clip','blur_glare','value_mask')]
        text.append('|'+LABELS[k]+'|'+'|'.join(f'{v:.4f}' for v in vals)+'|')
    text+=['','Mỗi cột có24 ảnh của cùng24 IDs, không phải120 giấy tờ độc lập.','',
        '## Khoảng tin cậy và kiểm tra lặp','', '| So sánh | Chênh lệch F1 | CI95 |','|---|---:|---:|']
    for v in audit['paired_intervals']:
        text.append(f"|{LABELS[v['candidate']]} − {LABELS[v['comparator']]}|{v['f1_difference']:.4f}|[{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}]|")
    text+=['','Bootstrap ghép cặp2000 lần theo24 physical IDs, giữ5biến thể cùng ID đi chung. Exploratory, chưa điều chỉnh nhiều phép thử. Hai seed không phải hai corpus độc lập.',
        f"Replay: {audit['vlm_rows_replayed']} hàng VLM chính, {audit['control_rows_replayed']} đối chứng, {audit['cpu_rows_replayed']} OCR; {audit['repeated_groups']} nhóm, mỗi nhóm3 lần suy luận. Rerun là panel12ảnh ×2 sau test120, không phải3 bộ120ảnh. Không sai khác score/hash. Audit số từ output đã lưu, không phải xác nhận độc lập của người.",'',
        '## Thời gian, bộ nhớ','', '| Phương án | p50/p95 giây (cached vision) | p50/p95 giây (fresh ảnh+vision+sinh) |','|---|---:|---:|']
    for k,r in records.items():
        fresh=[x for x in online['rows'] if x['model']==k];text.append(f"|{LABELS[k]}|{timing(r['rows'])}|{timing(fresh) if fresh else 'chưa đo fresh riêng'}|")
    for k in cpu['summaries']:text.append(f"|{LABELS[k]}|—|{timing([r for r in cpu['rows'] if r['model']==k])} CPU|")
    text+=[f"Fresh-online:{online['calls']} lần (12ảnh ×3mô hình ×2thứ tự), luôn tính mới vision; {online['cached_output_mismatches']} khác output cache. Gồm hash/decode/preprocess/vision/generation, model resident; loại HTTP/camera/cold-load. CPU OCR và GPU VLM là cấu hình triển khai khác nhau, không phải benchmark cùng backend.",'',
        '| Train | Step chọn | Dev token loss | Optimizer invocation(s) | Feature setup(s) | Peak allocated VRAM(GiB) | Peak process RSS(GiB) |','|---|---:|---:|---:|---:|---:|---:|']
    for k,f in [('seed_42','train_seed_42.json'),('seed_31415','train_seed_31415.json'),(CONTROL,'control/train_seed_42.json')]:
        r=read(f);e=r['events'];text.append(f"|{LABELS[k]}|{r['selected_checkpoint'].rsplit('_',1)[-1]}|{r['development_loss']:.6f}|{r['invocation_train_seconds']:.2f}|{r['feature_cache_setup_seconds']:.2f}|{max(x['peak_allocated_bytes'] for x in e)/2**30:.3f}|{max(x['process_peak_rss_bytes'] for x in e)/2**30:.3f}|")
    smoke=read('smoke.json')
    text+=['','RAM16GB, RTX3050 Laptop6GB. Base938,193,024tham số, trainable1,081,344; BF16 LoRA r8/alpha16, không phải QLoRA. Frozen vision/projector/baseLM. Trace lưu cả allocated/reserved VRAM; RSS gồm load, không phải tổng RAM máy. Tải/chuẩn bị nhiềuGB tách thời gian optimizer.',
        f"GPU smoke:{smoke['optimizer_steps_continuous']} bước +resume{smoke['resumed_steps']} bước; 192tensor thay đổi; maxabs resume/continuous={smoke['resume_max_abs_difference']}. Lỗi logger sau4bước đầu và Host ở fixture TestClient được giữ trong lịch sử, đã sửa/kiểm tra lại.",'',
        '## Triển khai và giới hạn','',
        'Web LoRA opt-in: http://127.0.0.1:8002/ . Camera xử lý trong bộ nhớ, tính mới vision; không tra dataset/GT, không lưu ảnh/text, không gọi API ngoài. Demo lấy ảnh train để thử UI, không là accuracy test. Không phê duyệt danh tính hoặc tuyên bố liveness/PAD qua thí nghiệm OCR.',
        'Adapter xuất riêng khoảng4.35MB, cần full Vintern đúng revision/loader gắn language_model. Weights/checkpoints/corpus/raw output ở ignored cache/data, không đưa Git. Python OCR gốc giữ nguyên, CUDA runtime ở cache riêng.',
        'Kết quả xác nhận adaptation trên corpus tổng hợp nhỏ cùng họ bố cục/font. LoRA và synthetic masking là kỹ thuật có sẵn, chưa đủ kết luận thuật toán mới/CORE B. Cần ảnh chụp vật lý khác thiết bị/bố cục, nhãn legibility từ người chấm, closest-prior comparison và phân tích lỗi độc lập trước claim rộng.','']
    report_path=ROOT/'research/VLM_RESULTS_VI.md';report_path.write_text('\n'.join(text),encoding='utf-8',newline='\n')
    save(OUT/'report_provenance.json',dict(signature=signature(),report_sha256=sha(report_path),audit_sha256=sha(OUT/'audit.json'),
        model_lock_sha256=sha(OUT/'test_lock.json'),control_lock_sha256=sha(OUT/'control/test_lock.json'),
        fresh_online_sha256=sha(OUT/'fresh_online.json'),format_analysis_sha256=sha(OUT/'format_analysis.json'),report_script_sha256=sha(__file__)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','report']);args=p.parse_args()
    audit() if args.action=='audit' else report()
