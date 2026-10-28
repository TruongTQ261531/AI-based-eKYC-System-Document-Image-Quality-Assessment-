"""Reproducible geometry/field-retention benchmark; predictions never see GT."""
import argparse
import csv
import gzip
import hashlib
import json
import math
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from research.support_regions import (area,intersection,frame_polygon,expand_region,
    required_margin,conformal_quantile,iou,predict)

SEEDS=(13,29,47,71,97)
METHODS=('single','medoid','fixed_05','fixed_10','fixed_20','adaptive_uncalibrated',
         'calibrated_constant','calibrated_adaptive','calibrated_fields')


def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')


def build_samples(data_root,annotation_dir):
    sources=json.loads((annotation_dir/'sources.json').read_text(encoding='utf-8'))
    if sources['failures'] or len(sources['records'])!=100:raise ValueError('Complete 100-archive annotation fetch required')
    labels={row['relative_path'].removeprefix('full_dataset_original/'):row['label'] for row in
            csv.DictReader(Path('data/manifest.csv').open(encoding='utf-8-sig'))}
    samples=[];missing=[];references=0;all_frames=0
    for record in sorted(sources['records'],key=lambda r:(r['source'],r['path'])):
        source=record['source'];name=Path(record['path']).stem;physical_id=int(name[:2])
        path=annotation_dir/f'{source}_{name}.json'
        if digest(path)!=record['normalized_sha256']:raise ValueError('Annotation hash mismatch')
        entries=json.loads(path.read_text(encoding='utf-8'))
        template=next(value for value in entries.values() if 'quad' not in value)
        reference=(data_root/'midv500_dataset'/name/'images'/f'{name}.tif' if source=='midv500' else
                   data_root/'midv2019_dataset'/f'{name}.tif')
        with Image.open(reference) as im:rw,rh=im.size
        for filename,annotation in entries.items():
            if 'quad' not in annotation:references+=1;continue
            all_frames+=1
            stem=Path(filename).stem;frame=int(stem.split('_')[-1])
            if frame not in (1,8,15,22,30):continue
            suffix=filename.split('ground_truth/',1)[1]
            relative=(Path('midv500_dataset')/name/'images'/Path(suffix).with_suffix('.tif') if source=='midv500' else
                      Path('midv2019_dataset')/Path(suffix).with_suffix('.tif'))
            image_path=data_root/relative
            if not image_path.is_file():missing.append(relative.as_posix());continue
            with Image.open(image_path) as im:width,height=im.size
            gt=np.asarray(annotation['quad'],np.float32)
            matrix=cv2.getPerspectiveTransform(np.float32([[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]]),gt)
            fields=[]
            for key,item in template.items():
                if not isinstance(item,dict) or not isinstance(item.get('value'),str) or not item.get('value') or 'quad' not in item:continue
                quad=cv2.perspectiveTransform(np.asarray(item['quad'],np.float32)[None],matrix)[0]
                if not np.isfinite(quad).all():raise ValueError('Nonfinite projected field')
                fields.append(dict(key=key,quad=quad.tolist(),text=item['value']))
            samples.append(dict(uid=f'{source}/{stem}',physical_id=physical_id,source=source,
                relative_path=relative.as_posix(),width=width,height=height,gt=gt.tolist(),fields=fields,
                file_bytes=image_path.stat().st_size,file_mtime_ns=image_path.stat().st_mtime_ns,
                quality_label=labels.get(relative.as_posix(),'unlabelled')))
    if missing:raise ValueError(f'{len(missing)} sampled images missing: {missing[:3]}')
    if len(samples)!=3500 or len({s['uid'] for s in samples})!=3500:raise ValueError(f'Expected 3500 unique frames, found {len(samples)}')
    if len({s['physical_id'] for s in samples})!=50:raise ValueError('Expected all 50 physical documents')
    samples.sort(key=lambda s:s['uid'])
    audit=dict(frames_in_annotations=all_frames,reference_annotations=references,sampled_frames=len(samples),
        physical_documents=50,source_counts=dict(Counter(s['source'] for s in samples)),
        quality_label_counts=dict(Counter(s['quality_label'] for s in samples)),missing_images=missing,
        annotations_source_hash=digest(annotation_dir/'sources.json'),
        license='MIDV author FTP: CC BY-SA 2.5, source transport FTP; JSON entry CRC checked',
        selection='Every clip, frame numbers 01/08/15/22/30; reference images not independent benchmark rows')
    return samples,audit


def worker(arguments):
    data_root,sample=arguments;cv2.setNumThreads(1);started=time.monotonic()
    path=Path(data_root)/sample['relative_path']
    raw=np.fromfile(str(path),np.uint8)
    image=cv2.imdecode(raw,cv2.IMREAD_COLOR)
    if image is None or image.shape[:2]!=(sample['height'],sample['width']):raise ValueError('Frame dimension mismatch')
    prediction=predict(image)
    return dict(uid=sample['uid'],prediction=prediction,input_sha256=hashlib.sha256(raw).hexdigest(),seconds=time.monotonic()-started)


def extract(data_root,samples,cache_path,workers,analyze_only=False):
    cached={}
    signature=hashlib.sha256((digest('research/support_regions.py')+digest('ekyc/module2_homography.py')+
        json.dumps([(s['uid'],s['width'],s['height'],s['file_bytes'],s['file_mtime_ns']) for s in samples])).encode()).hexdigest()
    meta=cache_path.with_suffix('.meta.json')
    if cache_path.exists():
        if not meta.exists() or json.loads(meta.read_text())['signature']!=signature:raise ValueError('Stale cache; use a new path')
        for line in cache_path.read_text(encoding='utf-8').splitlines():
            row=json.loads(line);cached[row['uid']]=row
    else:save(meta,dict(signature=signature,workers=workers,model_training=False,views_per_image=3))
    pending=[s for s in samples if s['uid'] not in cached]
    if analyze_only and pending:raise ValueError('Analysis-only requires complete prediction cache')
    started=time.monotonic()
    with cache_path.open('a',encoding='utf-8') as output,ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(worker,(str(data_root),s)):s for s in pending}
        for future in as_completed(futures):
            sample=futures[future]
            try:row=future.result()
            except Exception as error:
                # Extraction crashes abort the benchmark rather than silently
                # fabricating a successful crop or removing difficult frames.
                raise RuntimeError(f"Prediction failed on {sample['uid']}: {type(error).__name__}") from error
            cached[row['uid']]=row;output.write(json.dumps(row,allow_nan=False)+'\n');output.flush()
            if len(cached)%50==0:print(f'Predicted {len(cached)}/{len(samples)}, wall {time.monotonic()-started:.1f}s',flush=True)
    if len(cached)!=len(samples):raise ValueError('Incomplete prediction cache')
    return cached


def visible_targets(sample):
    frame=frame_polygon(sample['width'],sample['height'])
    visible=intersection(sample['gt'],frame)
    fields=[intersection(field['quad'],frame) for field in sample['fields']]
    return visible,[field for field in fields if area(field)>1.]


def scale_sets(pred):
    base=pred['safe_base'];constant=[max(1.5,.01*math.sqrt(max(area(base),1.)))]*4
    return constant,np.asarray(pred['scales']) if pred['consistent'] else np.asarray(constant)


def calibrate(samples,predictions,calibration_ids,alpha):
    grouped={key:{} for key in ('constant','adaptive','fields')}
    for sample in samples:
        group=sample['physical_id']
        if group not in calibration_ids:continue
        pred=predictions[sample['uid']]['prediction'];visible,fields=visible_targets(sample)
        constant,adaptive=scale_sets(pred)
        for name,target,scale in [('constant',[visible],constant),('adaptive',[visible],adaptive),('fields',fields,adaptive)]:
            score=required_margin(pred['safe_base'],target,scale)
            grouped[name][group]=max(grouped[name].get(group,0.),score)
    return {name:conformal_quantile(list(scores.values()),alpha) for name,scores in grouped.items()}


def region_for(sample,pred,method,quantiles):
    width,height=sample['width'],sample['height']
    if method=='single':return intersection(pred['original'],frame_polygon(width,height)),pred['original_detected'],pred['original']
    if method=='medoid':return intersection(pred['base'],frame_polygon(width,height)),pred['detected'],pred['base']
    if method.startswith('fixed_'):
        fraction={'fixed_05':.05,'fixed_10':.10,'fixed_20':.20}[method]
        base=pred['base'];margin=fraction*math.sqrt(max(area(base),1.))
        return expand_region(base,[margin]*4,width,height),pred['detected'],base
    base=pred['safe_base'];constant,adaptive=scale_sets(pred)
    if method=='adaptive_uncalibrated':margins=adaptive
    elif method=='calibrated_constant':margins=np.asarray(constant)*quantiles['constant']
    elif method=='calibrated_adaptive':margins=adaptive*quantiles['adaptive']
    elif method=='calibrated_fields':margins=adaptive*quantiles['fields']
    else:raise ValueError(method)
    return expand_region(base,margins,width,height),pred['consistent'],base


def metrics(sample,pred,method,quantiles):
    region,detected,base=region_for(sample,pred,method,quantiles)
    visible,fields=visible_targets(sample);gt_area=area(visible);pred_area=area(region)
    retained=area(intersection(visible,region))/gt_area if gt_area>1 else None
    field_retention=min((area(intersection(field,region))/area(field) for field in fields),default=None)
    contained=all(cv2.pointPolygonTest(np.asarray(region,np.float32),tuple(map(float,point)),True)>=-1 for point in visible) if gt_area>1 and area(region)>1 else False
    auto=bool(detected and pred_area/max(area(base),1.)<=1.35 and pred_area/((sample['width']-1)*(sample['height']-1))<=.95)
    return dict(uid=sample['uid'],physical_id=sample['physical_id'],source=sample['source'],quality_label=sample['quality_label'],
        method=method,iou=iou(region,visible) if gt_area>1 else 0.,retention=retained,
        field_retention=field_retention,strict_containment=bool(contained),visible=gt_area>1,
        clipped=bool(gt_area<area(sample['gt'])-.5),area_ratio=pred_area/gt_area if gt_area>1 else None,
        auto_accept=auto,utility_success=bool(gt_area>1 and iou(region,visible)>=.80 and retained>=.98))


def aggregate(rows):
    visible=[r for r in rows if r['visible']]
    fields=[r for r in visible if r['field_retention'] is not None]
    auto=[r for r in visible if r['auto_accept']]
    auto_fields=[r for r in auto if r['field_retention'] is not None]
    return dict(n=len(rows),visible_n=len(visible),mean_iou=float(np.mean([r['iou'] for r in visible])),
        retention_98=float(np.mean([r['retention']>=.98 for r in visible])),
        field_retention_98=float(np.mean([r['field_retention']>=.98 for r in fields])) if fields else None,
        strict_containment=float(np.mean([r['strict_containment'] for r in visible])),
        median_area_ratio=float(np.median([r['area_ratio'] for r in visible])),
        utility_success=float(np.mean([r['utility_success'] for r in visible])),
        auto_accept=float(np.mean([r['auto_accept'] for r in rows])),
        crop_harm_given_auto=float(np.mean([r['field_retention']<.98 for r in auto_fields])) if auto_fields else None,
        invisible_n=len(rows)-len(visible),invisible_auto_accept=sum(r['auto_accept'] for r in rows if not r['visible']))


def analyze(samples,predictions,out,alpha=.10):
    summary=[];all_rows=[];splits=[]
    ids=np.array(sorted({s['physical_id'] for s in samples}))
    for seed in SEEDS:
        shuffled=np.random.default_rng(seed).permutation(ids);cal=set(map(int,shuffled[:20]));test=set(map(int,shuffled[20:]))
        assert not cal&test
        quantiles=calibrate(samples,predictions,cal,alpha)
        splits.append(dict(seed=seed,calibration_ids=sorted(cal),test_ids=sorted(test),quantiles={k:v if np.isfinite(v) else 'infinity' for k,v in quantiles.items()}))
        for method in METHODS:
            rows=[dict(seed=seed,**metrics(s,predictions[s['uid']]['prediction'],method,quantiles)) for s in samples if s['physical_id'] in test]
            all_rows.extend(rows)
            for source in ('all','midv500','midv2019'):
                subset=rows if source=='all' else [r for r in rows if r['source']==source]
                summary.append(dict(seed=seed,method=method,source=source,**aggregate(subset)))
        print(f'Evaluated seed {seed}: {len(cal)} calibration IDs, {len(test)} test IDs',flush=True)
    save(out/'splits.json',splits);save(out/'summary.json',summary)
    with (out/'per_image.jsonl').open('w',encoding='utf-8') as f:
        for row in all_rows:f.write(json.dumps(row,allow_nan=False)+'\n')
    with (out/'per_image.jsonl.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as compressed:
        compressed.write((out/'per_image.jsonl').read_bytes())
    with (out/'summary.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    first=[r for r in all_rows if r['seed']==SEEDS[0] and r['visible']]
    comparisons=[];rng=np.random.default_rng(20261028)
    for method in METHODS:
        by_id={}
        for row in first:
            if row['method']==method:by_id.setdefault(row['physical_id'],[]).append(row['utility_success'])
        base={}
        for row in first:
            if row['method']=='single':base.setdefault(row['physical_id'],[]).append(row['utility_success'])
        delta=np.array([np.mean(by_id[g])-np.mean(base[g]) for g in sorted(by_id)])
        boot=delta[rng.integers(0,len(delta),(2000,len(delta)))].mean(axis=1)
        comparisons.append(dict(method=method,reference='single',metric='utility_success',physical_groups=len(delta),
            mean_paired_delta=float(delta.mean()),cluster_bootstrap_95_ci=np.quantile(boot,[.025,.975]).tolist()))
    save(out/'paired_bootstrap.json',comparisons)
    return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--annotations',type=Path,default=Path('research/data'))
    parser.add_argument('--cache',type=Path,default=Path('research/cache/predictions.jsonl'))
    parser.add_argument('--output',type=Path,default=Path('research/results/feasibility_v1'))
    parser.add_argument('--workers',type=int,default=3);parser.add_argument('--analyze-only',action='store_true')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);args.cache.parent.mkdir(parents=True,exist_ok=True)
    if args.analyze_only and not args.cache.exists():raise ValueError('Analysis-only requires complete prediction cache')
    started=time.monotonic();samples,audit=build_samples(args.data_root,args.annotations)
    save(args.annotations/'primary_samples.json',samples);save(args.output/'data_audit.json',audit)
    print(json.dumps(audit,indent=2),flush=True)
    predictions=extract(args.data_root,samples,args.cache,args.workers,args.analyze_only)
    summary=analyze(samples,predictions,args.output)
    save(args.output/'run.json',dict(protocol_sha256=digest('research/PROTOCOL.md'),
        support_code_sha256=digest('research/support_regions.py'),benchmark_sha256=digest(__file__),
        predictions_sha256=digest(args.cache),samples_sha256=digest(args.annotations/'primary_samples.json'),
        input_set_sha256=hashlib.sha256(json.dumps(sorted((r['uid'],r['input_sha256']) for r in predictions.values())).encode()).hexdigest(),
        seeds=list(SEEDS),distinct_images=len(samples),independent_physical_documents=50,
        inference_passes=1,views_per_image=3,model_training_runs=0,alpha=.10,
        elapsed_seconds=round(time.monotonic()-started,2),prediction_seconds_sum=sum(r['seconds'] for r in predictions.values()),
        localizer_failures=sum(not r['prediction']['detected'] for r in predictions.values()),
        analysis_repeats='calibration split repetitions, not independent model training',
        scope='geometric/text-field area retention, not OCR accuracy or eKYC verification'))
    print('SUMMARY',json.dumps([r for r in summary if r['seed']==SEEDS[0] and r['source']=='all']),flush=True)


if __name__=='__main__':main()
