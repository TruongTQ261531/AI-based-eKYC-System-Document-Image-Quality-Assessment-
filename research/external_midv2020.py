"""Bounded author-TAR reads and a fixed 20-identity external diagnostic."""
import hashlib
import io
import json
import math
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

import cv2
import numpy as np
from PIL import Image

from research.fetch_annotations import read_range
from research.benchmark import METHODS, metrics, save, digest
from research.risk_policy import row_for, aggregate
from research.support_regions import predict

ROOT = Path('research/data/midv2020')
SIZES = {'photo':4002467840, 'templates':863293440}


def padded(size): return ((size+511)//512)*512


def header(raw):
    if len(raw)!=512 or raw[257:262]!=b'ustar': raise ValueError('Unexpected TAR header')
    stored=int(raw[148:156].strip(b'\0 '),8)
    if sum(raw[:148])+sum(b' '*8)+sum(raw[156:])!=stored: raise ValueError('TAR checksum mismatch')
    name=raw[:100].split(b'\0')[0].decode('utf-8')
    if '..' in PurePosixPath(name).parts: raise ValueError('Invalid archive name')
    return name,int(raw[124:136].strip(b'\0 ') or b'0',8)


def metadata(kind):
    raw=(ROOT/('head.bin' if kind=='photo' else 'template_head.bin')).read_bytes()
    result={};images_start=None
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        for entry in archive:
            if entry.name.rstrip('/')=='images': images_start=entry.offset_data;break
            if not entry.name.endswith('.json'):continue
            data=json.loads(archive.extractfile(entry).read())
            code=PurePosixPath(entry.name).stem
            result[code]={v['filename']:v for v in data['_via_img_metadata'].values()}
    if len(result)!=10 or images_start is None:raise ValueError('All ten annotation files required')
    return result,images_start


def index_directories(kind, annotations, start):
    cache=ROOT/(kind+'_directory_offsets.json')
    if cache.exists(): return json.loads(cache.read_text())
    positions={};offset=start
    for _ in range(10):
        raw=read_range('/midv-2020/dataset/'+kind+'.tar',offset,512)
        name,size=header(raw);code=PurePosixPath(name.rstrip('/')).name
        if size!=0 or code not in annotations or code in positions:raise ValueError('Unexpected TAR directory layout')
        positions[code]=offset
        rows=annotations[code]
        if len(rows)!=100:raise ValueError('Expected 100 photos/templates per type')
        offset+=512+sum(512+padded(row['size']) for row in rows.values())
    if not 0<=SIZES[kind]-offset<=10240:raise ValueError('TAR directory size accounting mismatch')
    save(cache,positions);return positions


def selected_entries(kind,code,annotations,start):
    entries=[];offset=start+512
    for _ in range(2):
        raw=read_range('/midv-2020/dataset/'+kind+'.tar',offset,512)
        name,size=header(raw);path=PurePosixPath(name)
        if path.parts[:2]!=('images',code) or path.name not in annotations or size!=annotations[path.name]['size']:
            raise ValueError('JPEG header does not match author metadata')
        entries.append(dict(filename=path.name,bytes=size,data_offset=offset+512,header_sha256=hashlib.sha256(raw).hexdigest()))
        offset+=512+padded(size)
    return entries


def acquire_class(args):
    code,photo_meta,template_meta,photo_start,template_start=args
    folder=ROOT/code;folder.mkdir(exist_ok=True)
    record_path=folder/'records.json'
    if record_path.exists():
        records=json.loads(record_path.read_text())
        for record in records:
            if digest(folder/record['filename'])!=record['image_sha256']:raise ValueError('Cached external image hash mismatch')
        return records
    photos=selected_entries('photo',code,photo_meta,photo_start)
    templates=selected_entries('templates',code,template_meta,template_start)
    if [p['filename'] for p in photos]!=[t['filename'] for t in templates]:
        raise ValueError('Selected photo/template order differs; do not guess correspondence')
    records=[]
    for photo,template in zip(photos,templates):
        prefix=read_range('/midv-2020/dataset/templates.tar',template['data_offset'],min(template['bytes'],8192))
        with Image.open(io.BytesIO(prefix)) as image:rw,rh=image.size
        raw=read_range('/midv-2020/dataset/photo.tar',photo['data_offset'],photo['bytes'])
        with Image.open(io.BytesIO(raw)) as image:width,height=image.size;image.verify()
        (folder/photo['filename']).write_bytes(raw)
        annotation=photo_meta[photo['filename']]
        region=next(r for r in annotation['regions'] if r['region_attributes']['field_name']=='doc_quad')['shape_attributes']
        quad=np.float32(list(zip(region['all_points_x'],region['all_points_y'])))
        if quad.shape!=(4,2):raise ValueError('Four source corners required')
        matrix=cv2.getPerspectiveTransform(np.float32([[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]]),quad)
        fields=[]
        for item in template_meta[photo['filename']]['regions']:
            attrs=item['region_attributes'];shape=item['shape_attributes'];key=attrs['field_name']
            if key in ('photo','signature','face') or not isinstance(attrs.get('value'),str) or not attrs['value']:continue
            if shape['name']!='rect':raise ValueError('Unexpected text-field geometry')
            x,y,w,h=[shape[k] for k in ('x','y','width','height')]
            if not (0<=x<x+w<=rw+1 and 0<=y<y+h<=rh+1):raise ValueError('Template field outside canonical frame')
            corners=np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])
            points=cv2.perspectiveTransform(corners[None],matrix)[0]
            fields.append(dict(key=key,quad=points.tolist()))
        if not fields:raise ValueError('No annotated text fields')
        records.append(dict(code=code,**photo,image_sha256=hashlib.sha256(raw).hexdigest(),
            template_prefix_sha256=hashlib.sha256(prefix).hexdigest(),width=width,height=height,
            template_dimensions=[rw,rh],gt=quad.tolist(),fields=fields))
    save(record_path,records);print(f'Acquired {code}: 2 external photos',flush=True)
    return records


def main():
    ROOT.mkdir(exist_ok=True,parents=True);started=time.monotonic()
    photos,start=metadata('photo');templates,template_start=metadata('templates')
    photo_dirs=index_directories('photo',photos,start);template_dirs=index_directories('templates',templates,template_start)
    jobs=[(code,photos[code],templates[code],photo_dirs[code],template_dirs[code]) for code in sorted(photos)]
    with ThreadPoolExecutor(3) as pool:records=[row for group in pool.map(acquire_class,jobs) for row in group]
    if len(records)!=20:raise ValueError('Complete selected set required')
    save(ROOT/'selection.json',records)
    quantiles=json.loads(Path('research/results/feasibility_v1/splits.json').read_text())[0]['quantiles']
    choices=[r for r in json.loads(Path('research/results/risk_policy_v2/choices.json').read_text()) if r['seed']==13]
    rows=[];identities=[]
    cv2.setNumThreads(1)
    for index,record in enumerate(records,1):
        uid=record['code']+'/'+Path(record['filename']).stem
        sample=dict(record,uid='midv2020/'+uid,physical_id=uid,source='midv2020',quality_label='external_photo')
        image=cv2.imdecode(np.fromfile(str(ROOT/record['code']/record['filename']),np.uint8),cv2.IMREAD_COLOR)
        pred=predict(image)
        for method in METHODS:
            row=metrics(sample,pred,method,quantiles)
            harm=row['field_retention'] is None or row['field_retention']<.98
            rows.append(dict(row,harm=harm,harmful_auto=harm and row['auto_accept'],correct_field_auto=not harm and row['auto_accept'],
                             accepted_utility=row['auto_accept'] and row['utility_success']))
        for choice in choices:
            family=choice['method'].split('_')[0]
            amount=math.inf if choice['parameter']=='infinity' else choice['parameter']
            rows.append(dict(row_for(sample,pred,family,amount),method=choice['method']))
        identities.append(dict(uid=sample['uid'],filename=record['filename'],image_sha256=record['image_sha256'],
            file_bytes=record['bytes'],dimensions=[record['width'],record['height']],text_fields=len(record['fields']),
            prediction_sha256=hashlib.sha256(json.dumps(pred,sort_keys=True).encode()).hexdigest()))
        print(f'External inference {index}/20',flush=True)
    output=Path('research/results/external_midv2020')
    summary=[dict(method=method,**aggregate([r for r in rows if r['method']==method])) for method in dict.fromkeys(r['method'] for r in rows)]
    save(output/'per_image.json',rows);save(output/'summary.json',summary)
    save(output/'run.json',dict(protocol_sha256=digest('research/EXTERNAL_PROTOCOL.md'),code_sha256=digest(__file__),
        images=20,physical_ids=20,template_types=10,calibration_images=0,transferred_primary_seed=13,
        raw_image_bytes=sum(r['bytes'] for r in records),elapsed_seconds=round(time.monotonic()-started,2),
        scope='Small new-identity check; overlapping template types; no OOD coverage guarantee',
        license='MIDV-2020 CC BY-SA 2.5; synthetic portraits attributed to Generated Photos',
        transport='Author FTP; TAR header checksums/metadata sizes and block hashes; whole TAR MD5 not verified',
        selection=identities))
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
