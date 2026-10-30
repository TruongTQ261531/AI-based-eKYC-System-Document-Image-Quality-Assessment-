"""Bounded ZIP acquisition and locked external camera/template transfer check."""
import argparse
import copy
import hashlib
import io
import json
import struct
import time
import zlib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path,PurePosixPath

import cv2
import numpy as np
from PIL import Image,ImageOps

from research.benchmark import save,digest
from research.e2e_benchmark import atomic_json
from research.e2e_eval import score,target_fields
from research.e2e_pipeline import to_source
from research.fetch_annotations import read_range
from research.recovery_runtime import RecoveryEngine,semantic
from research.recovery_data import load_samples
from research.recovery_study import OUT,CACHE,process_lock
from research.recovery_validate import canonical

ROOT=Path('research/data/midv_up')
ARCHIVE='/midv-up/dataset.zip'


def get_range(offset,count):
    for attempt in range(3):
        try:return read_range(ARCHIVE,offset,count)
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt)


def entry_bytes(entry,prefix_only=False):
    offset=entry['header_offset'];header=get_range(offset,30)
    values=struct.unpack('<4s5H3I2H',header)
    if values[0]!=b'PK\x03\x04' or values[2]&1:raise ValueError('Invalid/encrypted ZIP local header')
    begin=offset+30+values[-2]+values[-1];count=min(entry['compressed'],8192) if prefix_only else entry['compressed']
    if entry['size']>30_000_000 or count>30_000_000:raise ValueError('ZIP entry exceeds bounded budget')
    raw=get_range(begin,count)
    if entry['compression']==8:
        value=zlib.decompressobj(-15).decompress(raw,64 if prefix_only else entry['size']+1)
    elif entry['compression']==0:value=raw[:64] if prefix_only else raw
    else:raise ValueError('Unsupported compression; do not silently skip selected image')
    if not prefix_only and (len(value)!=entry['size'] or zlib.crc32(value)&0xffffffff!=entry['crc']):
        raise ValueError('ZIP entry CRC/length mismatch')
    return value,hashlib.sha256(raw).hexdigest()


def acquisition():
    index=json.loads((ROOT/'index.json').read_text());entries=index['entries'];by={e['name']:e for e in entries}
    prefix='dataset/dataset/';photo_groups=defaultdict(list)
    for e in entries:
        if '/photo/images/' in e['name'] and e['name'].endswith('.jpg'):
            photo_groups[PurePosixPath(e['name']).parent.name].append(e)
    if len(photo_groups)!=8:raise ValueError('Expected four types/two cameras')
    seen=set();selected=[]
    for group,values in sorted(photo_groups.items()):
        doc,camera=group.rsplit('_',1)
        ordered=sorted(values,key=lambda e:hashlib.sha256(('up-transfer-20261031/'+e['name']).encode()).digest())
        chosen=[]
        for e in ordered:
            identity=doc+'/'+PurePosixPath(e['name']).stem
            if identity in seen:continue
            seen.add(identity);chosen.append(dict(e,document_type=doc,camera=camera,physical_id='midvup/'+identity))
            if len(chosen)==3:break
        if len(chosen)!=3:raise ValueError('Missing fixed transfer identity')
        selected.extend(chosen)
    meta={};source_blocks=[]
    for entry in selected:
        group=entry['document_type']+'_'+entry['camera'];doc=entry['document_type']
        for kind,name in [('photo',group),('templates',doc)]:
            key=(kind,name)
            if key in meta:continue
            source=by[prefix+kind+'/annotations/'+name+'.json'];path=ROOT/(kind+'_'+name+'.json')
            if path.exists():raw=path.read_bytes()
            else:raw,_=entry_bytes(source);path.write_bytes(raw)
            if len(raw)!=source['size'] or zlib.crc32(raw)&0xffffffff!=source['crc']:raise ValueError('Annotation CRC mismatch')
            data=json.loads(raw);meta[key]={v['filename']:v for v in data['_via_img_metadata'].values()}
            source_blocks.append(dict(entry=source['name'],sha256=hashlib.sha256(raw).hexdigest(),crc32=source['crc']))
    def acquire(entry):
        identity=entry['physical_id'];name=PurePosixPath(entry['name']).name;doc=entry['document_type'];camera=entry['camera']
        path=ROOT/(identity.replace('/','_')+'.jpg')
        if path.exists():raw=path.read_bytes()
        else:raw,_=entry_bytes(entry);path.write_bytes(raw)
        if len(raw)!=entry['size'] or zlib.crc32(raw)&0xffffffff!=entry['crc']:raise ValueError('Photo CRC mismatch')
        template=by[prefix+'templates/images/'+doc+'/'+Path(name).stem+'.png']
        png,prefix_sha=entry_bytes(template,True)
        if png[:8]!=b'\x89PNG\r\n\x1a\n' or zlib.crc32(png[12:29])&0xffffffff!=struct.unpack('>I',png[29:33])[0]:
            raise ValueError('Template PNG IHDR CRC mismatch')
        rw,rh=struct.unpack('>II',png[16:24]);ann=meta[('photo',doc+'_'+camera)][name]
        region=next(r['shape_attributes'] for r in ann['regions'] if r['region_attributes']['field_name']=='doc_quad')
        gt=np.float32(list(zip(region['all_points_x'],region['all_points_y'])))
        H=cv2.getPerspectiveTransform(np.float32([[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]]),gt)
        reference=meta[('templates',doc)][Path(name).stem+'.png'];fields=[]
        for item in reference['regions']:
            attrs=item['region_attributes'];shape=item['shape_attributes'];value=attrs.get('value')
            if not isinstance(value,str) or not value or shape['name']!='rect':continue
            x,y,w,h=[shape[k] for k in ('x','y','width','height')]
            quad=cv2.perspectiveTransform(np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]]),H)[0]
            fields.append(dict(key=attrs['field_name'],text=value,quad=quad.tolist()))
        with Image.open(io.BytesIO(raw)) as image:width,height=ImageOps.exif_transpose(image).size
        return dict(uid=identity,physical_id=identity,document_type=doc,camera=camera,path=str(path),source='midv_up_external',
            width=width,height=height,gt=gt.tolist(),fields=fields,input_sha256=hashlib.sha256(raw).hexdigest(),template_prefix_sha256=prefix_sha)
    with ThreadPoolExecutor(3) as pool:samples=list(pool.map(acquire,selected))
    if len(samples)!=24 or len({s['physical_id'] for s in samples})!=24:raise ValueError('Incomplete external selection')
    if {s['input_sha256'] for s in samples}&{s['input_sha256'] for s in load_samples()}:raise ValueError('Primary/external image overlap')
    save(ROOT/'samples.json',samples)
    public=[dict(**{k:s[k] for k in ('uid','physical_id','document_type','camera','input_sha256','width','height')},
                 eligible_fields=len(target_fields(s)[0]),excluded_fields=target_fields(s)[1]) for s in samples]
    save(OUT/'up_acquisition.json',dict(samples=public,source_blocks=source_blocks,protocol_sha256=digest('research/RECOVERY_EXTERNAL_UP_PROTOCOL.md'),
        archive_bytes=index['archive_size'],whole_archive_checksum_verified=False,source='ftp://smartengines.com/midv-up/dataset.zip',
        license='CC BY-SA2.5 Generic',new_self_captured_collection=False,unseen_pretraining_verified=False))
    print('UP_ACQUIRED',len(samples),'fixed external photos',flush=True)


def run():
    model=json.loads((OUT/'selector_models.json').read_text());lock=json.loads((OUT/'selector_lock.json').read_text())
    if digest(OUT/'selector_models.json')!=lock['model_sha256']:raise ValueError('Selector lock mismatch')
    engine=RecoveryEngine();reader='rapid_latin_v5';fixed=copy.deepcopy(model)
    fixed['selectors'][reader]['primary_method']='forced_completion'
    fixed['selectors'][reader]['models']['forced_completion']=dict(regressor=dict(kind='stumps',base=-1.,stumps=[]),expected_fallback_wall={p:0. for p in ('raw','bbox','contour','lcnet')})
    fixed['review_thresholds'][reader]['forced_completion']=model['review_thresholds'][reader]['fixed_completion']
    samples=json.loads((ROOT/'samples.json').read_text());rows=[]
    for repeat in (1,2):
        for i,sample in enumerate(samples):
            image=cv2.imread(sample['path']);methods=['raw','fixed_completion','primary_cascade']
            methods=methods[(i+repeat)%3:]+methods[:(i+repeat)%3]
            for method in methods:
                path=CACHE/'up_external'/f'{repeat}_{i}_{method}.json'
                if path.exists():
                    row=json.loads(path.read_text(encoding='utf-8'))
                    if row['model_sha256']!=lock['model_sha256']:raise ValueError('Stale external result')
                else:
                    if method=='raw':
                        tw=time.perf_counter();tc=time.process_time();answer=engine.ocr(image,reader)
                        response=dict(predictions=answer['predictions'],actual_wall_seconds=time.perf_counter()-tw,
                            actual_cpu_seconds=time.process_time()-tc,ocr_executions=1,selected_policy='raw',
                            review_recommended=not answer['predictions'])
                    else:response=engine.online(image,model if method=='primary_cascade' else fixed,reader)
                    row=dict(uid=sample['uid'],physical_id=sample['physical_id'],document_type=sample['document_type'],camera=sample['camera'],
                        method=method,repeat=repeat,model_sha256=lock['model_sha256'],input_sha256=sample['input_sha256'],
                        score=score(sample,response['predictions'],True),actual_wall=response['actual_wall_seconds'],actual_cpu=response['actual_cpu_seconds'],
                        ocr_executions=response['ocr_executions'],selected_policy=response['selected_policy'],
                        review_recommended=response['review_recommended'],prediction_sha256=canonical(response['predictions']),_private_predictions=response['predictions'])
                    atomic_json(path,row)
                rows.append({k:v for k,v in row.items() if not k.startswith('_private')});print('UP_EVAL',len(rows),'/144',flush=True)
    save(OUT/'up_external.json',dict(rows=rows,images=24,passes=2,newly_selected_templates=4,cameras=['iphone','samsung'],
        test_threshold_retuned=False,language_scope='Latin/alphanumeric targets only; Persian/Urdu support not established',
        code_sha256=digest(__file__),protocol_sha256=digest('research/RECOVERY_EXTERNAL_UP_PROTOCOL.md')))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('acquire','run'));args=parser.parse_args()
    if args.phase=='acquire':acquisition()
    else:
        with process_lock(CACHE/'process.lock'):run()
