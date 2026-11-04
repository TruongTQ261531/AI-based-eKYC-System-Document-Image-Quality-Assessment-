"""Source-to-label audit, independent projective math, and raw-output replay."""
import argparse
from collections import Counter
from functools import lru_cache
import numpy as np
from PIL import Image,ImageOps
from research.labels_common import *
from research.labels_schema import validate_field

def homography(src,dst):
    rows=[];values=[]
    for (x,y),(u,v) in zip(src,dst):
        rows.extend(([x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]));values.extend((u,v))
    return np.r_[np.linalg.solve(np.asarray(rows,float),np.asarray(values,float)),1.].reshape(3,3)

def project(quad,H):
    q=np.c_[np.asarray(quad,float),np.ones(len(quad))]@H.T
    return q[:,:2]/q[:,2:]

def clipped_polygon(points,width,height):
    result=[tuple(map(float,p)) for p in points]
    for axis,bound,greater in ((0,0,True),(0,width,False),(1,0,True),(1,height,False)):
        if not result:return []
        output=[]
        for a,b in zip(result,result[1:]+result[:1]):
            inside_a=a[axis]>=bound if greater else a[axis]<=bound
            inside_b=b[axis]>=bound if greater else b[axis]<=bound
            if inside_a:output.append(a)
            if inside_a!=inside_b:
                t=(bound-a[axis])/(b[axis]-a[axis]);output.append(tuple(a[j]+t*(b[j]-a[j]) for j in (0,1)))
        result=output
    return result

def area(points):
    if len(points)<3:return 0.
    q=np.asarray(points,float);return abs(float(np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))))/2

def data_scope():
    return digest(dict(files={name:sha(ROOT/'research'/name) for name in
        ('labels_schema.py','labels_import.py','labels_synth.py','labels_acquire.py','labels_data.py')},
        corpus_release=sha(OUT/'corpus_release.json'),evaluation_card=sha(OUT/'evaluation_card.json')))

@lru_cache(maxsize=4)
def annotation_file(path):return read(ROOT/path)

def data_audit():
    freeze_previous();scope=data_scope();release=read(OUT/'corpus_release.json')
    if sha(DB)!=release['annotation_database_sha256']:raise ValueError('Released annotation database changed')
    import csv
    with (ROOT/'data/manifest.csv').open(encoding='utf-8-sig',newline='') as stream:manifest={r['relative_path']:r for r in csv.DictReader(stream)}
    checked=set();field_count=0;max_error=0.;max_fraction_error=0.;quality=Counter();groups={};bytes_read=0
    with connect() as conn:
        rows=conn.execute('SELECT * FROM images ORDER BY native_uid').fetchall()
        for i,row in enumerate(rows,1):
            if row['path'] not in manifest:raise ValueError('Unrequested legacy row')
            expected_manifest=manifest[row['path']];checked.add(row['path'])
            if row['quality']!=expected_manifest['label']:raise ValueError('Original quality assignment changed')
            path=ROOT/row['path']
            if sha(path)!=row['sha256']:raise ValueError('Original image hash mismatch')
            bytes_read+=path.stat().st_size
            with Image.open(path) as im:
                if im.size!=(row['width'],row['height']):raise ValueError('Original dimensions differ')
            meta=json.loads(row['metadata']);ref=meta['annotation_ref'];author=annotation_file(ref['file']);template=author[ref['template_entry']]
            name=Path(ref['file']).stem.removeprefix(row['source']+'_')
            if row['physical_id']!='midv_legacy_document/'+str(int(name[:2])):raise ValueError('Incorrect physical-document grouping')
            groups.setdefault(row['physical_id'],set()).add(row['role']);quality[row['quality']]+=1
            reference=(ROOT/'full_dataset_original/midv500_dataset'/name/'images'/(name+'.tif') if row['source']=='midv500'
                       else ROOT/'full_dataset_original/midv2019_dataset'/(name+'.tif'))
            with Image.open(reference) as image:rw,rh=image.size
            if [rw,rh]!=meta['template_dimensions']:raise ValueError('Template coordinate size differs')
            src=[[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]]
            dst=src if meta['reference'] else author[ref['entry']]['quad']
            if not np.array_equal(np.asarray(dst),np.asarray(meta['card_quad'])):raise ValueError('Card corners differ from provider')
            H=homography(src,dst)
            actual={r['field_id']:json.loads(r['annotation']) for r in conn.execute('SELECT field_id,annotation FROM fields WHERE image_uid=?',(row['uid'],))}
            expected={k:v for k,v in template.items() if isinstance(v,dict) and isinstance(v.get('value'),str) and 'quad' in v}
            if set(actual)!=set(expected):raise ValueError('Missing, invented or renamed native fields')
            for key,f in actual.items():
                validate_field(f,row['width'],row['height']);target=expected[key]
                if f['reference_text']!=target['value'] or f['semantic_key'] is not None:raise ValueError('Author transcript or unknown semantics changed')
                expected_quad=project(target['quad'],H);q=np.asarray(f['polygon'])
                error=float(np.max(np.abs(q-expected_quad)));max_error=max(max_error,error)
                tolerance=.001+1e-5*max(1.,float(np.max(np.abs(expected_quad))))
                if error>tolerance:raise ValueError('Independent homography differs beyond fixed numeric tolerance')
                fraction=area(clipped_polygon(q,row['width'],row['height']))/area(q)
                fraction_error=abs(fraction-f['frame_visibility']['area_fraction']);max_fraction_error=max(max_fraction_error,fraction_error)
                if fraction_error>2e-4:raise ValueError('Independent frame clipping differs')
                if f['readability']['status']!='unassessed':raise ValueError('Fabricated legacy human readability')
                field_count+=1
            if i%64==0:progress('legacy_source_audit',i,len(rows),fields=field_count)
    if checked!=set(manifest) or len(groups)!=50 or any(len(v)!=1 for v in groups.values()):raise ValueError('Corpus coverage/group split failed')
    if field_count!=release['fields'] or bytes_read!=release['original_encoded_bytes']:raise ValueError('Corpus totals differ')
    new=sample_rows();specs={s['physical_id']:s for s in read(DATA/'render_specs.json')}
    from research.labels_synth import render,CONDITIONS
    from research.labels_data import pixels_hash,prior_rows
    authored=0;photographed=0;ink_checks=0
    for i,row in enumerate(new,1):
        with Image.open(ROOT/row['path']) as image:
            image=ImageOps.exif_transpose(image) if row['coordinate_mode']=='exif_display' else image
            image=image.convert('RGB')
            if sha(ROOT/row['path'])!=row['input_sha256'] or pixels_hash(image)!=row['pixel_sha256']:raise ValueError('New panel bytes/pixels changed')
            if row['source']=='authored':
                fresh,fields,meta=render(specs[row['physical_id']],row['condition'],row['capture'])
                if not np.array_equal(np.asarray(fresh),np.asarray(image)) or fields!=row['fields']:raise ValueError('Renderer pixels/labels do not reproduce')
                for f in fields:
                    if ''.join(g['character'] for g in f['glyphs'])!=''.join(c for c in f['reference_text'] if not c.isspace()):raise ValueError('Glyph transcript differs')
                    q=np.asarray(f['polygon']);glyphs=np.concatenate([np.asarray(g['polygon']) for g in f['glyphs']])
                    if np.max(np.abs(q.min(axis=0)-glyphs.min(axis=0)))>.001 or np.max(np.abs(q.max(axis=0)-glyphs.max(axis=0)))>.001:
                        raise ValueError('Field box does not enclose actual glyph support')
                    if f['frame_visibility']['status']!='in_frame':raise ValueError('Unintended synthetic value clipping')
                    ink_checks+=1
                authored+=1
            else:
                source=next(s for s in read(DATA/'sources.json') if s['physical_id']==row['physical_id'])
                if {f['raw_key']:f['reference_text'] for f in row['fields']}!={f['author_key']:f['value'] for f in source['fields']}:
                    raise ValueError('New photo native transcript coverage differs')
                with Image.open(ROOT/source['path']) as original:expected=np.asarray(ImageOps.exif_transpose(original).convert('RGB')).copy()
                import cv2
                for q in row['mask_regions']:cv2.fillConvexPoly(expected,np.rint(q).astype(np.int32),(36,44,51))
                if not np.array_equal(expected,np.asarray(image)):raise ValueError('Photographed mask raster differs')
                photographed+=1
        if any(f['readability']['status']!='unassessed' for f in row['fields']):raise ValueError('Unverified human labels in new panel')
        if i%16==0:progress('new_annotation_audit',i,len(new))
    for pid,spec in specs.items():
        for capture in ('full','value_mask'):
            subset=[r for r in new if r['physical_id']==pid and r['capture']==capture]
            if {r['condition'] for r in subset}!=set(CONDITIONS) or len({canonical(r['target']) for r in subset})!=1:
                raise ValueError('Layout/font conditions change semantic exposure')
            for f in subset[0]['fields']:
                if len({next(g['font_size'] for g in r['fields'] if g['raw_key']==f['raw_key']) for r in subset})!=1:
                    raise ValueError('Font size is confounded with layout/font condition')
    old={r['input_sha256']:r for r in prior_rows()};old_pixels=set()
    for i,r in enumerate(old.values(),1):
        p=ROOT/r['path']
        if not p.is_file() or sha(p)!=r['input_sha256']:raise ValueError('Prior source image unavailable/changed for overlap audit')
        with Image.open(p) as image:old_pixels.add(pixels_hash(ImageOps.exif_transpose(image)))
        if i%128==0:progress('prior_pixel_audit',i,len(old))
    if old_pixels&{r['pixel_sha256'] for r in new}:raise ValueError('New pixel overlap with previous VLM inputs')
    result=dict(status='passed',data_scope=data_scope(),code_sha256=sha(__file__),
        original_images=len(checked),author_field_records_checked=field_count,original_bytes_rehashed=bytes_read,
        physical_document_groups=len(groups),quality_counts=dict(quality),
        independent_projection_max_absolute_error=max_error,independent_clipping_max_fraction_error=max_fraction_error,
        synthetic_rasters_rebuilt=authored,photographed_views_rebuilt=photographed,glyph_field_checks=ink_checks,
        previous_unique_encoded_images_checked=len(old),previous_distinct_pixels_checked=len(old_pixels),new_pixel_overlap=0,
        human_readability_evidence_created=False,source_GT_is_not_human_legibility=True)
    save(OUT/'data_audit.json',result);print('LABEL_DATA_AUDIT_PASSED',field_count,flush=True)

def scores_audit():
    from research.labels_study import MODELS,record,fresh_panel
    from research.labels_metrics import summary,slices,effects
    from research.v2_cpu import extract
    from research.v3_cpu import fallback
    freeze_previous();sig=signature();rows=sample_rows();by={r['uid']:r for r in rows};all_records={};replayed=0;fresh_calls=0;mismatches=0
    model_lock=read(OUT/'models.json')
    for weight in model_lock['onnx_weights']:
        if sha(Path(weight['path']))!=weight['sha256']:raise ValueError('Reader weight changed after inference')
    if sha(ROOT/model_lock['adapter_path']/'adapter_model.safetensors')!=model_lock['adapter_sha256']:raise ValueError('Adapter changed after inference')
    for row in rows:
        if sha(ROOT/row['path'])!=row['input_sha256']:raise ValueError('Panel image changed after inference')
    for model in MODELS:
        published=read(OUT/f'evaluation_{model}.json')
        if published['signature']!=sig or len(published['rows'])!=304:raise ValueError('Missing planned reader output')
        replay=[]
        for p in published['rows']:
            sample=by[p['uid']];raw=read(CACHE/'predictions'/model/(uid(p['uid'])+'.json'))
            if raw['signature']!=sig:raise ValueError('Raw contract differs')
            if model!='partial_42':
                fields,_=fallback(extract(raw['output']['_private_boxes']),raw['output']['_private_boxes'],strict=True)
                if json.dumps(fields,ensure_ascii=False)!=raw['output']['text']:raise ValueError('CPU text not reproduced from recognized boxes')
            expected=record(sample,raw['output'],model,sig)
            if expected!=p or expected!=raw['public']:raise ValueError('Score not reproduced from raw reader output')
            replay.append(expected);replayed+=1
        if {r['uid'] for r in replay}!=set(by):raise ValueError('Reader case set differs')
        for role,value in published['summaries'].items():
            if summary([r for r in replay if r['role']==role])!=value:raise ValueError('Aggregate score differs')
        fresh=read(OUT/f'fresh_{model}.json')
        if len(fresh['rows'])!=8:raise ValueError('Missing repeat outputs')
        for sample in fresh_panel():
            for repeat in (1,2):
                raw=read(CACHE/'fresh'/model/(uid(sample['uid']+'/'+str(repeat))+'.json'))
                expected=record(sample,raw['output'],model,sig)
                p=next(r for r in fresh['rows'] if r['uid']==sample['uid'] and r['repeat']==repeat)
                if any(p[k]!=v for k,v in expected.items()):raise ValueError('Fresh score differs')
                original=next(r for r in replay if r['uid']==sample['uid'])
                same=expected['prediction_sha256']==original['prediction_sha256']
                if same!=p['identical_to_main']:raise ValueError('Fresh hash comparison differs')
                fresh_calls+=1;mismatches+=not same
        all_records[model]=replay
    events=[json.loads(line) for line in (CACHE/'execution_events.jsonl').read_text(encoding='utf-8').splitlines()]
    begin={r['call_id']:r for r in events if r['status']=='begin'}
    end={r['call_id']:r for r in events if r['status'] in ('completed','failed')}
    completed=[r for r in end.values() if r['status']=='completed'];failed=[r for r in end.values() if r['status']=='failed']
    if len(completed)!=replayed+fresh_calls:raise ValueError('Completed generation ledger differs from saved calls')
    save(OUT/'slices.json',dict(signature=sig,models={m:slices(r) for m,r in all_records.items()}))
    save(OUT/'factorial_effects.json',dict(signature=sig,models={m:{c:effects(r,c) for c in ('full','value_mask')} for m,r in all_records.items()}))
    save(OUT/'audit.json',dict(status='passed',signature=sig,replayed_score_rows=replayed,additional_fresh_calls=fresh_calls,
        fresh_output_hash_mismatches=mismatches,completed_text_generation_calls=len(completed),failed_generation_attempts=len(failed),
        interrupted_attempts_without_end=len(set(begin)-set(end)),generation_attempts=len(begin),
        execution_ledger_sha256=sha(CACHE/'execution_events.jsonl'),data_audit_sha256=sha(OUT/'data_audit.json'),
        source_boxes_used_by_predictors=False,training_runs=0,model_promoted=False,human_readability_verification_completed=False))
    print('LABEL_SCORES_AUDIT_PASSED',replayed,fresh_calls,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['data','scores']);a=p.parse_args()
    data_audit() if a.action=='data' else scores_audit()
