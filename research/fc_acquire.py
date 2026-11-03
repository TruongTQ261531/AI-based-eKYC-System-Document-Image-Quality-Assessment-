"""Metadata-selected author images following the last inspected TAR member15."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import PurePosixPath
from research.fc_common import *
from research import hp_acquire as acquisition
from research.external_midv2020 import metadata, header, padded
from research.recovery_acquire import read_retry


def extend(kind,code,meta):
    dest=DATA/'indices'/f'{kind}_{code}.json'
    if dest.exists():return read(dest)
    last=read(HP_DATA/'indices'/f'{kind}_{code}.json')[-1]
    offset=last['offset']+padded(last['bytes']);rows=[]
    for _ in range(3):
        raw=read_retry('/midv-2020/dataset/'+kind+'.tar',offset,512)
        name,size=header(raw);path=PurePosixPath(name)
        if path.parts[:2]!=('images',code) or path.name not in meta or size!=meta[path.name]['size']:
            raise ValueError('Fresh TAR member differs from author metadata')
        rows.append(dict(filename=path.name,bytes=size,offset=offset+512,header_sha256=hashlib.sha256(raw).hexdigest()))
        offset+=512+padded(size)
    save(dest,rows);return rows


def main():
    freeze_previous()
    if (DATA/'sources.json').exists():
        rows=read(DATA/'sources.json')
        if len(rows)!=24 or any(sha(ROOT/r['path'])!=r['source_sha256'] for r in rows):
            raise ValueError('Fresh sources changed')
        print('FC_SOURCES_ALREADY_READY',flush=True);return
    photos,_=metadata('photo');templates,_=metadata('templates')
    extras=set(sorted(photos,key=lambda c:hashlib.sha256(('fc1-extra/'+c).encode()).digest())[:4])
    acquisition.DATA=DATA;acquisition.extend=extend
    jobs=[(c,photos[c],templates[c],c in extras) for c in sorted(photos)]
    with ThreadPoolExecutor(3) as pool:
        rows=[r for group in pool.map(acquisition.acquire_code,jobs) for r in group]
    previous={r['physical_id'] for r in read(HP_DATA/'samples.json')}
    previous.update(r['physical_id'] for r in read(V3_DATA/'samples.json'))
    if len(rows)!=24 or previous & {r['physical_id'] for r in rows}:
        raise ValueError('Fresh photo identities overlap prior roles')
    save(DATA/'sources.json',rows)
    save(OUT/'acquisition.json',dict(photo_instances=24,selection='Members16/17 per type; member18 in four fixed SHA-ranked types',
        source='ftp://smartengines.com/midv-2020/dataset/photo.tar',
        integrity='TAR header checksum/size plus per-image SHA256; full archive MD5 not reverified',
        license='MIDV-2020 CC BY-SA2.5; original author/portrait attribution retained',
        independent_camera_collection=False,unknown_pretraining_overlap=True,
        sources=[{k:r[k] for k in ('physical_id','code','device','source_sha256')} for r in rows]))
    print('FC_NEW_SOURCES_READY',len(rows),flush=True)


if __name__=='__main__':main()
