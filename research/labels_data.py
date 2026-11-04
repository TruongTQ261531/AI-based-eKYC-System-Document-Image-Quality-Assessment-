"""Assemble annotations and fixed model-independent references for the new panel."""
from collections import Counter
import cv2
import numpy as np
from PIL import Image,ImageOps
from research.labels_common import *
from research.labels_schema import field
from research.labels_synth import build as build_authored
from research.v3_sources import source_graph,visible_realizations
from research.v2_common import FIELD_MAP,HELD_LAYOUTS

def pixels_hash(image):
    image=image.convert('RGB')
    return hashlib.sha256(str(image.size).encode()+image.tobytes()).hexdigest()

def photo_rows():
    sources=read(DATA/'sources.json');development=set()
    for code in sorted({r['code'] for r in sources}-set(HELD_LAYOUTS)):
        development.add(min((r['physical_id'] for r in sources if r['code']==code),key=lambda p:uid('labels-photo-dev/'+p)))
    if len(development)!=8:raise ValueError('Eight preselected photographed development IDs required')
    rows=[]
    for i,source in enumerate(sources,1):
        with Image.open(ROOT/source['path']) as image:full=ImageOps.exif_transpose(image).convert('RGB')
        width,height=full.size
        if (width,height)!=(source['width'],source['height']):raise ValueError('Photo annotation/display frame differs')
        nodes,mrz=source_graph(source)
        baseline,evidence,_=visible_realizations(nodes,np.eye(3),[],width,height)
        candidates=[]
        for key in sorted(baseline):
            masks=[]
            for node in nodes:
                if node['key']!=key:continue
                for quad in node['components']:
                    q=np.asarray(quad,np.float32);center=q.mean(axis=0);masks.append((q-center)*1.04+center)
            accepted,_,_=visible_realizations(nodes,np.eye(3),masks,width,height)
            if key in accepted:raise ValueError('Chosen declared source remains unmasked')
            collateral=len(set(baseline)-set(accepted)-{key})
            area=sum(abs(cv2.contourArea(m)) for m in masks)
            candidates.append((collateral,uid(source['physical_id']+'/'+key),area,key,masks))
        if not candidates:raise ValueError('Photo has no semantically covered author fields; retain/report failure')
        collateral,_,_,chosen,masks=min(candidates,key=lambda v:v[:3])
        for capture in ('full','value_mask'):
            active=[] if capture=='full' else masks
            image=full.copy();pixels=np.asarray(image).copy()
            for mask in active:cv2.fillConvexPoly(pixels,np.rint(mask).astype(np.int32),(36,44,51))
            native=source['physical_id']+'/labels-v1/'+capture
            if capture=='full':path=ROOT/source['path']
            else:
                path=DATA/'images'/('photo_'+uid(native)+'.png');path.parent.mkdir(parents=True,exist_ok=True)
                Image.fromarray(pixels).save(path)
            fields=[]
            for native_field in source['fields']:
                raw=native_field['author_key'];q=native_field['quad']
                intersections=[float(cv2.intersectConvexConvex(np.float32(q),m)[0]) for m in active]
                f=field(raw,native_field['value'],q,width,height,origin='author_template_projection',
                    annotation_ref=dict(source_record=(DATA/'sources'/source['code']/(source['filename']+'.json')).relative_to(ROOT).as_posix(),field=raw),
                    semantic_key=FIELD_MAP.get(raw),extra=dict(field_id=raw,mask_intersection_area=sum(intersections),
                    mask_geometry_is_not_ink_legibility=True))
                fields.append(f)
            accepted,evidence,occluded=visible_realizations(nodes,np.eye(3),active,width,height)
            rows.append(dict(uid=native,physical_id=source['physical_id'],role='development' if source['physical_id'] in development else 'test',
                source='midv2020',device=source['device'],layout=source['code'],font_sha256=None,condition='public_photo',
                capture=capture,path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),width=width,height=height,
                coordinate_mode='exif_display' if capture=='full' else 'raw_pixels',fields=fields,
                target={k:v[0]['value'] for k,v in accepted.items()},accepted_values={k:list(dict.fromkeys(v['value'] for v in values)) for k,values in accepted.items()},
                source_refs=accepted,source_evidence=evidence,source_coverage=mrz,masked_keys=sorted(occluded),
                mask_regions=[m.tolist() for m in active],selected_mask_key=chosen if active else None,
                collateral_hidden_keys=collateral if active else 0,provider_record=source['physical_id']))
        progress('photo_annotation',i,24)
    return rows

def prior_rows():
    result=[]
    for folder in ('vlm_lora_v1','vlm_lora_v2','vlm_lora_v2_r2','source_visibility_v3','hard_pairs_v1','fair_controls_v1'):
        for name in ('samples.json','train.json','evaluation.json'):
            path=ROOT/'research/data'/folder/name
            if not path.exists():continue
            value=read(path)
            if isinstance(value,dict):value=[r for rows in value.values() if isinstance(rows,list) for r in rows]
            result.extend(r for r in value if isinstance(r,dict) and 'physical_id' in r and 'input_sha256' in r)
    return result

def prepare():
    freeze_previous()
    if (DATA/'evaluation.json').exists():raise ValueError('Prepared release exists; use audit/resume, do not silently regenerate')
    rows=build_authored()+photo_rows();old=prior_rows()
    if len(rows)!=304 or len({r['uid'] for r in rows})!=304:raise ValueError('All 304 predeclared views required')
    old_ids={r['physical_id'] for r in old};old_bytes={r['input_sha256'] for r in old}
    if old_ids&{r['physical_id'] for r in rows} or old_bytes&{r['input_sha256'] for r in rows}:raise ValueError('New panel overlaps previous VLM roles')
    old_targets={digest(r['target']) for r in old if r.get('target')}
    if old_targets&{digest(r['target']) for r in rows if r['capture']=='full' and r['target']}:
        raise ValueError('New complete target duplicates a prior reference')
    pixel_ids={};pixels=set()
    for r in rows:
        with Image.open(ROOT/r['path']) as image:
            image=ImageOps.exif_transpose(image) if r['coordinate_mode']=='exif_display' else image
            r['pixel_sha256']=pixels_hash(image)
        pixels.add(r['pixel_sha256']);pixel_ids.setdefault(r['pixel_sha256'],set()).add(r['physical_id'])
        r['annotation_uid']=uid(r['uid'])
        if not all(f['readability']['status']=='unassessed' for f in r['fields']):raise ValueError('No actual human readability evidence yet')
    if any(len(v)>1 for v in pixel_ids.values()):raise ValueError('Cross-ID pixel duplicate in new panel')
    for pid in {r['physical_id'] for r in rows}:
        if len({r['role'] for r in rows if r['physical_id']==pid})!=1:raise ValueError('ID crosses roles')
    save(DATA/'evaluation.json',rows)
    public=[dict(uid=r['uid'],physical_id=r['physical_id'],role=r['role'],source=r['source'],device=r['device'],layout=r['layout'],
            condition=r['condition'],capture=r['capture'],input_sha256=r['input_sha256'],pixel_sha256=r['pixel_sha256'],
            native_fields=len(r['fields']),semantic_fields=len(r['target']),annotation_sha256=digest(r['fields'])) for r in rows]
    save(OUT/'evaluation_manifest.json',public)
    save(OUT/'evaluation_card.json',dict(views=len(rows),document_instances=len({r['physical_id'] for r in rows}),distinct_decoded_rasters=len(pixels),
        roles=dict(Counter(r['role'] for r in rows)),sources=dict(Counter(r['source'] for r in rows)),
        evaluation_sha256=sha(DATA/'evaluation.json'),render_specs_sha256=sha(DATA/'render_specs.json'),
        new_to_prior_VLM_ids=True,new_encoded_image_overlap=0,new_complete_answer_overlap=0,
        independent_camera_collection=False,human_legibility_verified=False,
        fonts=read(OUT/'fonts.json'),photographic_fonts='unknown; do not infer from template class',
        public_photo_devices=dict(Counter(r['device'] for r in rows if r['source']=='midv2020' and r['capture']=='full')),
        masked_photo_collateral_views=sum(r.get('collateral_hidden_keys',0)>0 for r in rows),
        raw_native_field_count=sum(len(r['fields']) for r in rows),
        scope='Controlled authored layout/value-font shifts and new public-photo instances; no human legibility or unseen-pretraining guarantee'))
    save(OUT/'analysis_plan.json',dict(primary='Descriptive source-aware semantic field F1; no registered superiority claim',
        layout_font_factorial='Paired full authored views by ID; four cells; masks reported separately',
        source_transfer='Photographs separate; not an isolated causal camera effect',
        bootstrap=10000,seed=20261109,cluster='physical_id',models=['rapid_v4','rapid_latin_v5','partial_42'],
        fresh_calls=24,fresh_distinct_inputs=4,fresh_document_instances=2,model_promotion=False))
    print('LABEL_PANEL_PREPARED',len(rows),len(pixels),flush=True)

if __name__=='__main__':prepare()
