"""Supplementary frozen DocAligner comparator using existing ONNX Runtime."""
import gzip
import json
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from ekyc.io import StageError
from ekyc.module2_homography import order_corners
from research.benchmark import digest, save, metrics, aggregate
from research.support_regions import frame_polygon

MODEL_SHA = '7f9f5a8935b2eb22b3ee0245d34996063f54562df390d34714af2d76928695bc'


def decode_heatmap(heatmap, height, width):
    if heatmap.ndim!=4 or heatmap.shape[0]!=1 or heatmap.shape[1]<4 or not np.isfinite(heatmap).all():
        raise ValueError('Unexpected DocAligner heatmap contract')
    corners=[]
    for channel in heatmap[0,:4]:
        full=cv2.resize(channel,(width,height),interpolation=cv2.INTER_LINEAR)
        full[full<.3]=0
        mask=np.uint8(full*255)
        _,mask=cv2.threshold(mask,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        contours=[c for c in contours if len(c)>1 and cv2.contourArea(c)>0]
        if not contours:raise StageError('Missing neural corner')
        contour=max(contours,key=cv2.contourArea);moments=cv2.moments(contour)
        corners.append([moments['m10']/(moments['m00']+1e-5),moments['m01']/(moments['m00']+1e-5)])
    return order_corners(corners)


def infer(session,image):
    height,width=image.shape[:2]
    tensor=cv2.resize(image,(256,256),interpolation=cv2.INTER_LINEAR).transpose(2,0,1)[None].astype(np.float32)/255.
    heatmap=session.run(['heatmap'],{'img':np.ascontiguousarray(tensor)})[0]
    try:quad=decode_heatmap(heatmap,height,width);detected=True
    except StageError:quad=frame_polygon(width,height);detected=False
    return dict(original=quad.tolist(),base=quad.tolist(),safe_base=quad.tolist(),scales=[1.]*4,
                detected=detected,original_detected=detected,consistent=detected)


def main():
    output=Path('research/results/neural_baseline');output.mkdir(exist_ok=True,parents=True)
    model=Path('research/cache/docaligner/fastvit_sa24.onnx')
    if digest(model)!=MODEL_SHA:raise ValueError('Author-published model hash mismatch')
    options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
    session=ort.InferenceSession(str(model),options,providers=['CPUExecutionProvider'])
    io_contract=dict(inputs=[dict(name=x.name,shape=x.shape,type=x.type) for x in session.get_inputs()],
                     outputs=[dict(name=x.name,shape=x.shape,type=x.type) for x in session.get_outputs()])
    print('MODEL_IO',json.dumps(io_contract),flush=True)
    if session.get_inputs()[0].name!='img' or 'heatmap' not in [x.name for x in session.get_outputs()]:
        raise ValueError('Unexpected named neural IO')
    samples=[s for s in json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8')) if s['uid'].endswith('_15')]
    if len(samples)!=700:raise ValueError('Exactly 700 frame15 cases required')
    external=json.loads(Path('research/data/midv2020/selection.json').read_text())
    for record in external:
        uid=record['code']+'/'+Path(record['filename']).stem
        samples.append(dict(record,uid='midv2020/'+uid,physical_id=uid,source='midv2020',quality_label='external_photo'))
    cache_path=Path('research/cache/docaligner/predictions.jsonl')
    cached={r['uid']:r for r in map(json.loads,cache_path.read_text().splitlines())} if cache_path.exists() else {}
    started=time.monotonic();cv2.setNumThreads(1)
    with cache_path.open('a',encoding='utf-8') as stream:
        for index,sample in enumerate(samples,1):
            if sample['uid'] in cached:continue
            path=(Path('research/data/midv2020')/sample['code']/sample['filename'] if sample['source']=='midv2020' else
                  Path('D:/laptrinhcuatao/Ekyc/full_dataset_original')/sample['relative_path'])
            tick=time.monotonic();image=cv2.imdecode(np.fromfile(str(path),np.uint8),cv2.IMREAD_COLOR)
            prediction=infer(session,image)
            row=dict(uid=sample['uid'],prediction=prediction,input_sha256=digest(path),seconds=time.monotonic()-tick,
                     model_sha256=MODEL_SHA,adapter_sha256=digest(__file__))
            stream.write(json.dumps(row)+'\n');stream.flush();cached[row['uid']]=row
            if index%50==0:print(f'Neural {index}/{len(samples)}',flush=True)
    if len(cached)!=len(samples):raise ValueError('Neural cache sample mismatch')
    for row in cached.values():
        if row['model_sha256']!=MODEL_SHA or row['adapter_sha256']!=digest(__file__):raise ValueError('Stale neural cache')
    splits=json.loads(Path('research/results/feasibility_v1/splits.json').read_text())
    all_rows=[];summary=[]
    for split in splits:
        for method in ('neural_single','neural_fixed_05'):
            rows=[dict(metrics(s,cached[s['uid']]['prediction'],'single' if method=='neural_single' else 'fixed_05',{}),
                       method=method,seed=split['seed']) for s in samples if s['source']!='midv2020' and s['physical_id'] in split['test_ids']]
            all_rows.extend(rows)
            for source in ('all','midv500','midv2019'):
                summary.append(dict(seed=split['seed'],method=method,source=source,**aggregate(rows if source=='all' else [r for r in rows if r['source']==source])))
    with gzip.open('research/results/feasibility_v1/per_image.jsonl.gz','rt',encoding='utf-8') as stream:
        baseline=[json.loads(line) for line in stream]
    baseline=[r for r in baseline if r['uid'].endswith('_15') and r['method'] in ('single','adaptive_uncalibrated')]
    all_rows.extend(baseline)
    for split in splits:
        for method in ('single','adaptive_uncalibrated'):
            rows=[r for r in baseline if r['seed']==split['seed'] and r['method']==method]
            for source in ('all','midv500','midv2019'):
                summary.append(dict(seed=split['seed'],method=method,source=source,**aggregate(rows if source=='all' else [r for r in rows if r['source']==source])))
    external_rows=[]
    for method in ('neural_single','neural_fixed_05'):
        rows=[dict(metrics(s,cached[s['uid']]['prediction'],'single' if method=='neural_single' else 'fixed_05',{}),method=method)
              for s in samples if s['source']=='midv2020']
        external_rows.extend(rows)
    save(output/'summary.json',summary);save(output/'external_rows.json',external_rows)
    with (output/'per_image.jsonl.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as stream:
        for row in all_rows:stream.write((json.dumps(row)+'\n').encode())
    save(output/'run.json',dict(model_sha256=MODEL_SHA,code_sha256=digest(__file__),protocol_sha256=digest('research/NEURAL_BASELINE_PROTOCOL.md'),
        primary_images=700,external_images=20,localizer_failures=sum(not r['prediction']['detected'] for r in cached.values()),
        elapsed_seconds=round(time.monotonic()-started,2),prediction_seconds_sum=sum(r['seconds'] for r in cached.values()),
        io_contract=io_contract,training_split_provenance='Not independently established; possible MIDV exposure',
        upstream_package_numeric_equivalence_verified=False,device='CPU',new_dependencies=False))
    print('NEURAL_COMPLETE',flush=True)


if __name__=='__main__':main()
