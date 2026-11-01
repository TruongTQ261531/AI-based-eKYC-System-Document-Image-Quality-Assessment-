"""Author-annotated, new MIDV-2020 identities; no model is used to create labels."""
import hashlib
import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from research.v2_common import ROOT,DATA,OUT,PILOT_DATA,HELD_LAYOUTS,read,save,sha
from research.external_midv2020 import metadata,displayed_geometry
from research.recovery_acquire import read_retry

def fields_for(code,name,quad,dimensions,templates):
    w,h=dimensions
    H=cv2.getPerspectiveTransform(np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]),np.float32(quad))
    fields=[]
    for r in templates[code][name]['regions']:
        a=r['region_attributes'];s=r['shape_attributes']
        if not isinstance(a.get('value'),str) or not a['value'] or a['field_name'] in ('face','photo','signature'): continue
        if s['name']!='rect': raise ValueError('Unexpected author field geometry')
        x,y,b,h0=[s[k] for k in ('x','y','width','height')]
        q=cv2.perspectiveTransform(np.float32([[[x,y],[x+b,y],[x+b,y+h0],[x,y+h0]]]),H)[0]
        fields.append(dict(author_key=a['field_name'],value=a['value'],quad=q.tolist()))
    return fields

def cached_old(templates):
    rows=[]
    for rel in ('research/data/midv2020','research/data/recovery_v4/midv'):
        folder=ROOT/rel
        for r in read(folder/'selection.json'):
            path=folder/r['code']/r['filename']
            if sha(path)!=r['image_sha256']: raise ValueError('Prior source image changed')
            im=Image.open(path);device=str(im.getexif().get(272,'unknown'));im.close()
            rows.append(dict(physical_id='midv2020/'+r['code']+'/'+Path(r['filename']).stem,
                code=r['code'],filename=r['filename'],path=path.relative_to(ROOT).as_posix(),
                device=device,source_sha256=r['image_sha256'],quad=r['gt'],
                fields=fields_for(r['code'],r['filename'],r['gt'],r['template_dimensions'],templates),
                prior_study_used=True))
    return rows

def acquire_code(job):
    code,photos,templates,excluded=job
    dest=DATA/'sources'/code;dest.mkdir(parents=True,exist_ok=True)
    pi=read(ROOT/f'research/data/recovery_v4/midv/photo_{code}_index.json')
    ti={r['filename']:r for r in read(ROOT/f'research/data/recovery_v4/midv/templates_{code}_index.json')}
    records=[]
    for entry in pi:
        name=entry['filename'];pid='midv2020/'+code+'/'+Path(name).stem
        if pid in excluded: continue
        record=dest/(name+'.json');path=dest/name
        if record.exists():
            row=read(record)
            if sha(path)!=row['source_sha256']: raise ValueError('New source hash changed')
            records.append(row);continue
        template=ti[name]
        for length in (8192,65536,262144,1048576):
            prefix=read_retry('/midv-2020/dataset/templates.tar',template['offset'],min(length,template['bytes']))
            try:
                with Image.open(io.BytesIO(prefix)) as im: dimensions=im.size
                break
            except OSError:
                if length==1048576: raise
        raw=read_retry('/midv-2020/dataset/photo.tar',entry['offset'],entry['bytes'])
        if len(raw)!=entry['bytes']: raise ValueError('Photo byte count changed')
        with Image.open(io.BytesIO(raw)) as im: im.verify()
        path.write_bytes(raw)
        im=Image.open(path);device=str(im.getexif().get(272,'unknown'));im.close()
        s=next(r['shape_attributes'] for r in photos[name]['regions'] if r['region_attributes']['field_name']=='doc_quad')
        quad=list(map(list,zip(s['all_points_x'],s['all_points_y'])))
        row=dict(physical_id=pid,code=code,filename=name,path=path.relative_to(ROOT).as_posix(),device=device,
            source_sha256=sha(path),quad=quad,fields=fields_for(code,name,quad,dimensions,{code:templates}),
            prior_study_used=False,source_entry=entry,template_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
            **displayed_geometry(path))
        save(record,row);records.append(row)
        print('ACQUIRED',code,name,device,flush=True)
    if len(records)!=4: raise ValueError('Exactly four untouched identities expected per type')
    return records

def main():
    preserve=__import__('research.v2_common',fromlist=['preserve_v1']).preserve_v1()
    if (PILOT_DATA/'sources.json').exists():
        selected=read(PILOT_DATA/'sources.json')
        for r in selected:
            if sha(ROOT/r['path'])!=r['source_sha256']:raise ValueError('Pilot acquisition source changed')
        save(DATA/'sources.json',selected)
        acquisition=read(ROOT/'research/results/vlm_lora_v2/acquisition.json')
        acquisition.update(revision='r2 author-label coverage correction; exact same source selection, no test outputs seen',
            acquisition_reused_without_redownload=True)
        save(OUT/'acquisition.json',acquisition)
        print('V2_R2_SOURCES_VERIFIED',len(selected),flush=True);return
    photos,_=metadata('photo');templates,_=metadata('templates');old=cached_old(templates)
    old_ids={r['physical_id'] for r in old}
    jobs=[(c,photos[c],templates[c],old_ids) for c in sorted(photos)]
    with ThreadPoolExecutor(3) as pool: fresh=[r for group in pool.map(acquire_code,jobs) for r in group]
    train=[r for r in old if r['code'] not in HELD_LAYOUTS and r['device']=='iPhone XS Max']
    train.sort(key=lambda r:hashlib.sha256(('v2-train/'+r['physical_id']).encode()).digest())
    train=train[:32]
    if len(train)!=32: raise ValueError('Insufficient device-separated training sources')
    selected=[dict(r,role='train') for r in train]
    for code in sorted(photos):
        pool=sorted([r for r in fresh if r['code']==code],key=lambda r:r['physical_id'])
        if code in HELD_LAYOUTS: selected += [dict(r,role='test') for r in pool];continue
        # Predetermined EXIF-based split, without viewing any OCR predictions.
        iphone=[r for r in pool if r['device']=='iPhone XS Max']
        if not iphone: raise ValueError('No new iPhone development source for '+code)
        dev=iphone[0]; selected.append(dict(dev,role='development'))
        remain=[r for r in pool if r['physical_id']!=dev['physical_id']]
        remain.sort(key=lambda r:(r['device']!='SM-G973F',r['physical_id']))
        selected += [dict(r,role='test') for r in remain[:2]]
    save(DATA/'sources.json',selected)
    save(OUT/'acquisition.json',dict(frozen_v1_files_verified=preserve,downloaded_new_ids=len(fresh),
        selected_ids=len(selected),prior_ids_allowed_only_in_training=True,
        author='MIDV-2020, Bulatov et al.',source='ftp://smartengines.com/midv-2020/dataset/photo.tar',
        integrity='Previously verified TAR header checksums/sizes; selected image SHA256; not full archive MD5',
        license='MIDV-2020 CC BY-SA 2.5; retain original portrait/dataset attribution',
        independent_camera_collection=False,pretraining_overlap_unknown=True,
        sources=[{k:r[k] for k in ('physical_id','code','role','device','source_sha256','prior_study_used')} for r in selected]))
    print('V2_SOURCES_READY',len(selected),flush=True)

if __name__=='__main__': main()
