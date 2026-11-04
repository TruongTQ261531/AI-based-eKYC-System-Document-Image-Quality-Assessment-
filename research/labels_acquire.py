"""A metadata-only selection of author photo instances beyond FC member18."""
import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath
from PIL import Image
from research.labels_common import *
from research.external_midv2020 import metadata,header,padded,displayed_geometry
from research.recovery_acquire import read_retry
from research.v2_acquire import fields_for

def extend(kind,code,annotations):
    path=DATA/'indices'/f'{kind}_{code}.json'
    if path.exists():return read(path)
    old=read(ROOT/f'research/data/fair_controls_v1/indices/{kind}_{code}.json')
    last=old[-1];offset=last['offset']+padded(last['bytes']);rows=[]
    for _ in range(3):
        raw=read_retry('/midv-2020/dataset/'+kind+'.tar',offset,512)
        name,size=header(raw);p=PurePosixPath(name)
        if p.parts[:2]!=('images',code) or p.name not in annotations or size!=annotations[p.name]['size']:
            raise ValueError('Author TAR member changed')
        rows.append(dict(filename=p.name,bytes=size,offset=offset+512,header_sha256=hashlib.sha256(raw).hexdigest()))
        offset+=512+padded(size)
    save(path,rows);return rows

def acquire(job):
    code,photos,templates,extra=job
    members=extend('photo',code,photos);template_index={r['filename']:r for r in extend('templates',code,templates)}
    rows=[]
    for entry in members[:3 if extra else 2]:
        name=entry['filename'];folder=DATA/'sources'/code;path=folder/name;record=folder/(name+'.json')
        if record.exists():
            row=read(record)
            if sha(path)!=row['source_sha256']:raise ValueError('New photo cache changed')
            rows.append(row);continue
        template=template_index[name]
        for count in (8192,65536,262144,1048576):
            prefix=read_retry('/midv-2020/dataset/templates.tar',template['offset'],min(count,template['bytes']))
            try:
                with Image.open(io.BytesIO(prefix)) as image:dimensions=image.size
                break
            except OSError:
                if count==1048576:raise
        raw=read_retry('/midv-2020/dataset/photo.tar',entry['offset'],entry['bytes'])
        if len(raw)!=entry['bytes']:raise ValueError('Photo byte count differs')
        with Image.open(io.BytesIO(raw)) as image:image.verify()
        folder.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        with Image.open(path) as image:device=str(image.getexif().get(272,'unknown'))
        region=next(r['shape_attributes'] for r in photos[name]['regions'] if r['region_attributes']['field_name']=='doc_quad')
        quad=list(map(list,zip(region['all_points_x'],region['all_points_y'])))
        row=dict(physical_id='midv2020/'+code+'/'+Path(name).stem,code=code,filename=name,path=path.relative_to(ROOT).as_posix(),
            device=device,source_sha256=sha(path),quad=quad,template_dimensions=list(dimensions),
            fields=fields_for(code,name,quad,dimensions,{code:templates}),source_entry=entry,template_entry=template,
            template_prefix_sha256=hashlib.sha256(prefix).hexdigest(),**displayed_geometry(path))
        save(record,row);rows.append(row);print('LABEL_PHOTO',code,len(rows),flush=True)
    return rows

def main():
    freeze_previous()
    if (DATA/'sources.json').exists():
        rows=read(DATA/'sources.json')
        if len(rows)!=24 or any(sha(ROOT/r['path'])!=r['source_sha256'] for r in rows):raise ValueError('Photo acquisition changed')
        print('LABEL_PHOTOS_VERIFIED',24,flush=True);return
    photos,_=metadata('photo');templates,_=metadata('templates')
    extra=set(sorted(photos,key=lambda c:uid('labels-photo-extra-20261104/'+c))[:4])
    with ThreadPoolExecutor(2) as pool:
        rows=[r for group in pool.map(acquire,[(c,photos[c],templates[c],c in extra) for c in sorted(photos)]) for r in group]
    previous=set()
    for rel in ('research/data/vlm_lora_v2_r2/sources.json','research/data/hard_pairs_v1/sources.json','research/data/fair_controls_v1/sources.json'):
        previous.update(r['physical_id'] for r in read(ROOT/rel))
    if len(rows)!=24 or len({r['physical_id'] for r in rows})!=24 or previous&{r['physical_id'] for r in rows}:
        raise ValueError('Fresh photo identity overlap or incomplete selection')
    save(DATA/'sources.json',rows)
    save(OUT/'acquisition.json',dict(photo_instances=24,selection='Members19/20 per type; member21 in four fixed SHA-ranked types',
        source='ftp://smartengines.com/midv-2020/dataset/photo.tar',
        integrity='Author TAR header checksum/entry sizes and per-image SHA256; full archive checksum not reverified',
        independent_new_camera_collection=False,unknown_pretraining_overlap=True,
        license='MIDV CC BY-SA2.5; retain author/portrait attribution',
        author_photo_metadata_sha256=sha(ROOT/'research/data/midv2020/head.bin'),
        sources=[{k:r[k] for k in ('physical_id','code','device','source_sha256')} for r in rows]))
    print('LABEL_PHOTOS_READY',24,flush=True)

if __name__=='__main__':main()
