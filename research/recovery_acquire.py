"""Acquire a bounded new MIDV subset; source text remains in private data."""
import hashlib
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path,PurePosixPath

import cv2
import numpy as np
from PIL import Image

from research.benchmark import save,digest
from research.external_midv2020 import metadata,index_directories,header,padded,displayed_geometry
from research.fetch_annotations import read_range

ROOT=Path('research/data/recovery_v4/midv')


def read_retry(path,offset,count):
    for attempt in range(3):
        try:return read_range(path,offset,count)
        except Exception:
            if attempt==2:raise
            time.sleep(1+attempt)


def index_prefix(kind,code,meta,start):
    cache=ROOT/(kind+'_'+code+'_index.json')
    if cache.exists():return json.loads(cache.read_text())
    rows=[];offset=start+512
    for _ in range(12):
        raw=read_retry('/midv-2020/dataset/'+kind+'.tar',offset,512)
        name,size=header(raw);name=PurePosixPath(name)
        if name.parts[:2]!=('images',code) or name.name not in meta or size!=meta[name.name]['size']:
            raise ValueError('Source TAR header differs from author metadata')
        rows.append(dict(filename=name.name,bytes=size,offset=offset+512,header_sha256=hashlib.sha256(raw).hexdigest()))
        offset+=512+padded(size)
    save(cache,rows);return rows


def acquire(job):
    code,photos,templates,pstart,tstart,old=job
    dest=ROOT/code;dest.mkdir(exist_ok=True,parents=True);record_file=dest/'records.json'
    if record_file.exists():
        records=json.loads(record_file.read_text(encoding='utf-8'))
        for r in records:
            if digest(dest/r['filename'])!=r['image_sha256']:raise ValueError('Cached MIDV source hash changed')
        return records
    photo_rows=index_prefix('photo',code,photos,pstart);template_rows=index_prefix('templates',code,templates,tstart)
    by_name={r['filename']:r for r in template_rows}
    candidates=[r for r in photo_rows if (code,r['filename']) not in old]
    candidates.sort(key=lambda r:hashlib.sha256(('recovery-v4/20261030/'+code+'/'+r['filename']).encode()).digest())
    chosen=candidates[:6]
    if len(chosen)!=6 or any(r['filename'] not in by_name for r in chosen):
        raise ValueError('Bounded template/photo pools do not match; do not silently change selection')
    records=[]
    for index,entry in enumerate(chosen):
        name=entry['filename'];template=by_name[name]
        for length in (8192,65536,262144,1048576):
            prefix=read_retry('/midv-2020/dataset/templates.tar',template['offset'],min(length,template['bytes']))
            try:
                with Image.open(io.BytesIO(prefix)) as im:rw,rh=im.size
                break
            except OSError:
                if length==1048576:raise
        raw=read_retry('/midv-2020/dataset/photo.tar',entry['offset'],entry['bytes'])
        with Image.open(io.BytesIO(raw)) as im:im.verify()
        path=dest/name;path.write_bytes(raw);geom=displayed_geometry(path)
        region=next(r['shape_attributes'] for r in photos[name]['regions'] if r['region_attributes']['field_name']=='doc_quad')
        quad=np.float32(list(zip(region['all_points_x'],region['all_points_y'])))
        matrix=cv2.getPerspectiveTransform(np.float32([[0,0],[rw-1,0],[rw-1,rh-1],[0,rh-1]]),quad)
        fields=[]
        for item in templates[name]['regions']:
            attrs=item['region_attributes'];shape=item['shape_attributes'];value=attrs.get('value');key=attrs['field_name']
            if not isinstance(value,str) or not value or key in ('photo','face','signature'):continue
            if shape['name']!='rect':raise ValueError('Unexpected template field shape')
            x,y,w,h=[shape[k] for k in ('x','y','width','height')]
            if not (0<=x<x+w<=rw+1 and 0<=y<y+h<=rh+1):raise ValueError('Field outside verified template dimensions')
            q=cv2.perspectiveTransform(np.float32([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]]),matrix)[0]
            fields.append(dict(key=key,text=value,quad=q.tolist()))
        records.append(dict(code=code,filename=name,**geom,gt=quad.tolist(),fields=fields,
            role='development' if index<2 else 'calibration' if index==2 else 'test',
            physical_id='midv2020/'+code+'/'+Path(name).stem,image_sha256=digest(path),source_entry=entry,
            template_prefix_sha256=hashlib.sha256(prefix).hexdigest(),template_dimensions=[rw,rh]))
    save(record_file,records);print('ACQUIRED',code,len(records),flush=True);return records


def main():
    ROOT.mkdir(parents=True,exist_ok=True);photos,pstart=metadata('photo');templates,tstart=metadata('templates')
    pd=index_directories('photo',photos,pstart);td=index_directories('templates',templates,tstart)
    old={(r['code'],r['filename']) for r in json.loads(Path('research/data/midv2020/selection.json').read_text())}
    jobs=[(code,photos[code],templates[code],pd[code],td[code],old) for code in sorted(photos)]
    with ThreadPoolExecutor(3) as pool:rows=[r for group in pool.map(acquire,jobs) for r in group]
    assert len(rows)==60 and len({r['physical_id'] for r in rows})==60
    save(ROOT/'selection.json',rows)
    save(Path('research/results/recovery_v4')/'acquisition.json',dict(identities=60,newly_selected_study_ids=True,
        verified_unseen_pretraining=False,bytes=sum(r['source_entry']['bytes'] for r in rows),
        license='MIDV-2020 CC BY-SA2.5; Generated Photos portrait attribution retained in source',
        source='ftp://smartengines.com/midv-2020/dataset/photo.tar',
        transport='Bounded FTP REST; checked TAR headers/sizes; local SHA256, not whole TAR MD5',
        selection=[{k:r[k] for k in ('physical_id','role','image_sha256')} for r in rows]))
    print('ACQUISITION_COMPLETE',len(rows),flush=True)


if __name__=='__main__':main()
