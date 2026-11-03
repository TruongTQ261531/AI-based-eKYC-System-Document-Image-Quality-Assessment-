"""New author MIDV entries beyond the first twelve used by previous studies."""
import hashlib
import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath
from PIL import Image
from research.hp_common import *
from research.external_midv2020 import metadata,header,padded,displayed_geometry
from research.recovery_acquire import read_retry
from research.v2_acquire import fields_for


def extend(kind,code,meta):
    dest=DATA/'indices'/f'{kind}_{code}.json'
    if dest.exists():return read(dest)
    old=read(ROOT/f'research/data/recovery_v4/midv/{kind}_{code}_index.json')
    last=old[-1];offset=last['offset']+padded(last['bytes'])
    result=[]
    for _ in range(3):
        raw=read_retry('/midv-2020/dataset/'+kind+'.tar',offset,512)
        name,size=header(raw);path=PurePosixPath(name)
        if path.parts[:2]!=('images',code) or path.name not in meta or size!=meta[path.name]['size']:
            raise ValueError('New TAR member does not match author metadata')
        if path.name in {r['filename'] for r in old}:raise ValueError('Repeated old TAR member')
        result.append(dict(filename=path.name,bytes=size,offset=offset+512,header_sha256=hashlib.sha256(raw).hexdigest()))
        offset+=512+padded(size)
    save(dest,result);return result


def acquire_code(job):
    code,photo_meta,template_meta,extra=job
    photos=extend('photo',code,photo_meta);templates={r['filename']:r for r in extend('templates',code,template_meta)}
    rows=[]
    for entry in photos[:3 if extra else 2]:
        name=entry['filename'];folder=DATA/'sources'/code
        path=folder/name;record=folder/(name+'.json')
        if record.exists():
            value=read(record)
            if sha(path)!=value['source_sha256']:raise ValueError('New test source changed')
            rows.append(value);continue
        template=templates[name]
        for length in (8192,65536,262144,1048576):
            prefix=read_retry('/midv-2020/dataset/templates.tar',template['offset'],min(length,template['bytes']))
            try:
                with Image.open(io.BytesIO(prefix)) as im:dimensions=im.size
                break
            except OSError:
                if length==1048576:raise
        raw=read_retry('/midv-2020/dataset/photo.tar',entry['offset'],entry['bytes'])
        with Image.open(io.BytesIO(raw)) as im:im.verify()
        folder.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        with Image.open(path) as im:device=str(im.getexif().get(272,'unknown'))
        s=next(r['shape_attributes'] for r in photo_meta[name]['regions'] if r['region_attributes']['field_name']=='doc_quad')
        quad=list(map(list,zip(s['all_points_x'],s['all_points_y'])))
        value=dict(physical_id='midv2020/'+code+'/'+Path(name).stem,code=code,filename=name,
            path=path.relative_to(ROOT).as_posix(),device=device,source_sha256=sha(path),quad=quad,
            fields=fields_for(code,name,quad,dimensions,{code:template_meta}),
            source_entry=entry,template_prefix_sha256=hashlib.sha256(prefix).hexdigest(),**displayed_geometry(path))
        save(record,value);rows.append(value);print('HP_NEW_SOURCE',code,len(rows),flush=True)
    return rows


def main():
    preserve()
    if (DATA/'sources.json').exists():
        rows=read(DATA/'sources.json')
        if len(rows)!=24 or any(sha(ROOT/r['path'])!=r['source_sha256'] for r in rows):raise ValueError('Cached new sources differ')
        print('HP_NEW_SOURCES_ALREADY_VERIFIED',len(rows));return
    photos,_=metadata('photo');templates,_=metadata('templates')
    extras=set(sorted(photos,key=lambda c:hashlib.sha256(('hard-pair-v1-extra/'+c).encode()).digest())[:4])
    jobs=[(code,photos[code],templates[code],code in extras) for code in sorted(photos)]
    with ThreadPoolExecutor(3) as pool:rows=[r for group in pool.map(acquire_code,jobs) for r in group]
    previous={r['physical_id'] for r in read(OLD_DATA/'samples.json')}
    for rel in ('research/data/midv2020/selection.json','research/data/recovery_v4/midv/selection.json'):
        previous.update(r.get('physical_id') or 'midv2020/'+r['code']+'/'+Path(r['filename']).stem for r in read(ROOT/rel))
    if len(rows)!=24 or len({r['physical_id'] for r in rows})!=24 or previous & {r['physical_id'] for r in rows}:
        raise ValueError('New photo IDs overlap previous experiments')
    save(DATA/'sources.json',rows)
    save(OUT/'acquisition.json',dict(new_photo_document_instances=24,old_document_overlap=0,
        source='ftp://smartengines.com/midv-2020/dataset/photo.tar',
        selection='Members 13/14 per type plus member15 in four SHA-ranked types; no OCR-based selection',
        integrity='Author TAR header checksum/size, per-image SHA256; full archive MD5 not verified',
        license='MIDV-2020 CC BY-SA 2.5, original author/portrait attribution retained',
        independent_new_camera_collection=False,unknown_pretraining_overlap=True,
        sources=[{k:r[k] for k in ('physical_id','code','device','source_sha256')} for r in rows]))
    print('HP_NEW_SOURCES_READY',len(rows),flush=True)


if __name__=='__main__':main()
