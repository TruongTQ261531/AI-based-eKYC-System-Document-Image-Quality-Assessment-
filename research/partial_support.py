"""Preserve visible document support from exactly three observed corners."""
import gzip
import json
import math
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from ekyc.io import StageError
from ekyc.module2_homography import order_corners
from research.benchmark import digest, save, metrics
from research.neural_baseline import MODEL_SHA
from research.risk_policy import aggregate
from research.support_regions import area, frame_polygon

POLICIES=('neural_original','partial_triangle','partial_parallelogram','partial_support','partial_support_padded')


def observed_support(points,width,height,margin=0.):
    present=[i for i,p in enumerate(points) if p is not None]
    if len(present)!=3:raise StageError('Three observed corners required')
    found=np.array([points[i] for i in present],float)
    if not np.isfinite(found).all() or area(cv2.convexHull(found.astype(np.float32)))<100:
        raise StageError('Degenerate observed corners')
    poly=frame_polygon(width,height).astype(float)
    for i in range(4):
        j=(i+1)%4
        if points[i] is None or points[j] is None:continue
        p,q=np.asarray(points[i]),np.asarray(points[j]);edge=q-p
        normal=np.array([-edge[1],edge[0]])/np.linalg.norm(edge)
        other=np.asarray(points[next(k for k in present if k not in (i,j))])
        if (other-p)@normal<0:normal=-normal
        bound=p@normal-margin;clipped=[]
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            da,db=a@normal-bound,b@normal-bound
            if da>=-1e-7:clipped.append(a)
            if (da>=0)!=(db>=0):clipped.append(a+(b-a)*da/(da-db))
        if len(clipped)<3:raise StageError('Empty observed support')
        poly=np.asarray(clipped)
    return np.float32(poly)


def decode_partial(heatmap,height,width):
    points=[]
    for channel in heatmap[0,:4]:
        full=cv2.resize(channel,(width,height),interpolation=cv2.INTER_LINEAR)
        full[full<.3]=0
        _,mask=cv2.threshold(np.uint8(full*255),0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        contours=[c for c in contours if len(c)>1 and cv2.contourArea(c)>0]
        if not contours:points.append(None);continue
        moments=cv2.moments(max(contours,key=cv2.contourArea))
        points.append([moments['m10']/(moments['m00']+1e-5),moments['m01']/(moments['m00']+1e-5)])
    return points


def measure(sample,region,detected,method,corner_count):
    prediction=dict(original=np.asarray(region).tolist(),original_detected=detected)
    row=metrics(sample,prediction,'single',{})
    harm=row['field_retention'] is None or row['field_retention']<.98
    return dict(row,method=method,harm=harm,harmful_auto=harm and row['auto_accept'],
                correct_field_auto=not harm and row['auto_accept'],accepted_utility=row['auto_accept'] and row['utility_success'],
                observed_corners=corner_count)


def main():
    started=time.monotonic();cv2.setNumThreads(1)
    model=Path('research/cache/docaligner/fastvit_sa24.onnx')
    if digest(model)!=MODEL_SHA:raise ValueError('Pinned model hash mismatch')
    opt=ort.SessionOptions();opt.intra_op_num_threads=2;opt.inter_op_num_threads=1
    session=ort.InferenceSession(str(model),opt,providers=['CPUExecutionProvider'])
    cached={r['uid']:r for r in map(json.loads,Path('research/cache/docaligner/predictions.jsonl').read_text().splitlines())}
    samples=[s for s in json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8')) if s['uid'].endswith('_15')]
    for record in json.loads(Path('research/data/midv2020/selection.json').read_text()):
        uid=record['code']+'/'+Path(record['filename']).stem
        samples.append(dict(record,uid='midv2020/'+uid,physical_id=uid,source='midv2020',quality_label='external_photo'))
    partial_path=Path('research/cache/docaligner/partial_corners.json')
    partial=json.loads(partial_path.read_text()) if partial_path.exists() else {}
    newly_inferred=0
    for sample in samples:
        uid=sample['uid']
        if cached[uid]['prediction']['detected'] or uid in partial:continue
        path=(Path('research/data/midv2020')/sample['code']/sample['filename'] if sample['source']=='midv2020' else
              Path('D:/laptrinhcuatao/Ekyc/full_dataset_original')/sample['relative_path'])
        if digest(path)!=cached[uid]['input_sha256']:raise ValueError('Neural input changed')
        image=cv2.imdecode(np.fromfile(str(path),np.uint8),cv2.IMREAD_COLOR)
        height,width=image.shape[:2]
        if (height,width)!=(sample['height'],sample['width']):raise ValueError('Frame dimensions changed')
        tensor=cv2.resize(image,(256,256),interpolation=cv2.INTER_LINEAR).transpose(2,0,1)[None].astype(np.float32)/255.
        heatmap=session.run(['heatmap'],{'img':np.ascontiguousarray(tensor)})[0]
        if not np.isfinite(heatmap).all():raise ValueError('Nonfinite neural output')
        partial[uid]=dict(points=decode_partial(heatmap,height,width),heatmap_dimensions=list(heatmap.shape[-2:]))
        newly_inferred+=1
        save(partial_path,partial)
    all_rows=[];counts=Counter()
    for sample in samples:
        uid=sample['uid'];original=cached[uid]['prediction'];valid=original['detected']
        points=partial[uid]['points'] if not valid else None
        count=4 if valid else sum(p is not None for p in points);counts[count]+=1
        for method in POLICIES:
            region=original['original'];detected=valid
            if not valid and count==3 and method!='neural_original':
                try:
                    if method=='partial_triangle':region=cv2.convexHull(np.float32([p for p in points if p is not None])).reshape(-1,2)
                    elif method=='partial_parallelogram':
                        missing=points.index(None);completed=list(points)
                        completed[missing]=(np.asarray(points[(missing-1)%4])+np.asarray(points[(missing+1)%4])-np.asarray(points[(missing+2)%4])).tolist()
                        region=order_corners(completed)
                    else:
                        hh,ww=partial[uid]['heatmap_dimensions']
                        margin=.5*math.hypot(sample['width']/ww,sample['height']/hh) if method=='partial_support_padded' else 0.
                        region=observed_support(points,sample['width'],sample['height'],margin)
                    detected=True
                except StageError:region=frame_polygon(sample['width'],sample['height']);detected=False
            all_rows.append(measure(sample,region,detected,method,count))
    output=Path('research/results/partial_support_v3');summary=[];test_rows=[]
    splits=json.loads(Path('research/results/feasibility_v1/splits.json').read_text())
    for split in splits:
        for method in POLICIES:
            rows=[dict(r,seed=split['seed']) for r in all_rows if r['source']!='midv2020' and r['method']==method and r['physical_id'] in split['test_ids']]
            test_rows.extend(rows)
            for stratum in ('all','midv500','midv2019','Clean','Blur','Cropped','Dark','Distorted'):
                subset=rows if stratum=='all' else [r for r in rows if r['source']==stratum or r['quality_label']==stratum]
                summary.append(dict(seed=split['seed'],method=method,stratum=stratum,**aggregate(subset)))
    external=[r for r in all_rows if r['source']=='midv2020']
    save(output/'summary.json',summary);save(output/'external_rows.json',external)
    save(output/'external_summary.json',[dict(method=m,**aggregate([r for r in external if r['method']==m])) for m in POLICIES])
    with (output/'per_image.jsonl.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as stream:
        for row in test_rows:stream.write((json.dumps(row)+'\n').encode())
    save(output/'run.json',dict(protocol_sha256=digest('research/PARTIAL_SUPPORT_PROTOCOL.md'),code_sha256=digest(__file__),model_sha256=MODEL_SHA,
        primary_images=700,external_images=20,corner_counts={str(k):v for k,v in sorted(counts.items())},
        eligible_three_corner_cases=counts[3],new_neural_calls=newly_inferred,training_runs=0,
        elapsed_seconds=round(time.monotonic()-started,2),exploratory_after_neural_comparator=True))
    print('PARTIAL_COMPLETE',dict(counts),flush=True)


if __name__=='__main__':main()
