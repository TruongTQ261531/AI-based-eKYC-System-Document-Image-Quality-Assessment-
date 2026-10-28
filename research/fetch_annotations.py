"""Read only small JSON blocks from author-published ZIPs, using FTP REST.

No archive extraction or downloaded code execution. FTP is the dataset's
published legacy transport; record per-block hashes/CRC, not a false claim
that a whole archive checksum was validated.
"""
import argparse
import hashlib
import io
import json
import re
import struct
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor,as_completed
from ftplib import FTP
from pathlib import Path

import numpy as np


def read_range(path,start,count,to_eof=False):
    ftp=FTP('smartengines.com',timeout=40);ftp.login()
    ftp.voidcmd('TYPE I')
    sock=ftp.transfercmd('RETR '+path,rest=start)
    chunks=[];remaining=count
    try:
        while remaining>0:
            data=sock.recv(min(65536,remaining))
            if not data:break
            chunks.append(data);remaining-=len(data)
    finally:
        sock.close();ftp.close()
    value=b''.join(chunks)
    if len(value)!=count: raise IOError(f'Short read: {path}')
    return value


def archive_annotations(path):
    ftp=FTP('smartengines.com',timeout=40);ftp.login();size=ftp.size(path);ftp.quit()
    length=min(size,131072)
    tail=read_range(path,size-length,length,True)
    archive=zipfile.ZipFile(io.BytesIO(tail))
    entries=[info for info in archive.infolist() if info.filename.endswith('.json') and '/ground_truth/' in '/'+info.filename]
    if not 100<=len(entries)<=400:raise ValueError('Unexpected annotation count')
    offset=size-length
    lo=min(info.header_offset+offset for info in entries)
    hi=max(info.header_offset+offset+info.compress_size+512 for info in entries)
    if hi-lo>2_000_000:raise ValueError('Annotations not in bounded contiguous block')
    raw=read_range(path,lo,hi-lo)
    result={}
    for info in entries:
        if info.flag_bits&1 or info.file_size>100000 or '..' in Path(info.filename).parts:raise ValueError('Unsafe ZIP entry')
        pos=info.header_offset+offset-lo
        header=struct.unpack_from('<4s5H3I2H',raw,pos)
        if header[0]!=b'PK\x03\x04':raise ValueError('Invalid local header')
        begin=pos+30+header[-2]+header[-1]
        compressed=raw[begin:begin+info.compress_size]
        value=zlib.decompress(compressed,-15) if info.compress_type==8 else compressed if info.compress_type==0 else None
        if value is None or len(value)!=info.file_size or zlib.crc32(value)&0xffffffff!=info.CRC:raise ValueError('Annotation CRC mismatch')
        data=json.loads(value)
        if not isinstance(data,dict):raise ValueError('Invalid annotation schema')
        if 'quad' in data:
            points=np.asarray(data['quad'],dtype=float)
            if points.shape!=(4,2) or not np.isfinite(points).all():raise ValueError('Invalid quad')
        result[info.filename]=data
    return result,dict(path=path,archive_bytes=size,json_count=len(result),bytes_read=len(tail)+len(raw),
        tail_sha256=hashlib.sha256(tail).hexdigest(),annotation_block_sha256=hashlib.sha256(raw).hexdigest(),
        integrity='per-entry CRC32 and block SHA256; whole ZIP MD5 not verified')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='research/data');parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    ftp=FTP('smartengines.com',timeout=40);ftp.login()
    jobs=[]
    for source,directory in [('midv500','/midv-500/dataset'),('midv2019','/midv-500/extra/midv-2019/dataset')]:
        for name in ftp.nlst(directory):
            if re.fullmatch(r'\d{2}_[a-z0-9_]+\.zip',Path(name).name):jobs.append((source,name))
    ftp.quit()
    if len(jobs)!=100:raise ValueError(f'Expected 100 document archives, found {len(jobs)}')
    failures=[];records=[]
    manifest=out/'sources.json'
    previous=json.loads(manifest.read_text(encoding='utf-8'))['records'] if manifest.exists() else []
    cached={(record['source'],record['path']):record for record in previous}
    pending=[]
    for source,path in jobs:
        target=out/f'{source}_{Path(path).stem}.json';record=cached.get((source,path))
        if record and target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==record['normalized_sha256']:
            records.append(record)
        else:pending.append((source,path))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        tasks={pool.submit(archive_annotations,path):(source,path) for source,path in pending}
        for future in as_completed(tasks):
            source,path=tasks[future];name=Path(path).stem;target=out/f'{source}_{name}.json'
            try:
                data,meta=future.result();target.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True),encoding='utf-8')
                records.append(dict(source=source,**meta,normalized_sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
                print(f'[{len(records)}/{len(jobs)}] {source}/{name}: {len(data)} JSON entries',flush=True)
            except Exception as error:
                failures.append(dict(source=source,path=path,error=f'{type(error).__name__}: {error}'))
                print(f'FAILED {source}/{name}: {type(error).__name__}',flush=True)
    (out/'sources.json').write_text(json.dumps(dict(records=records,failures=failures),indent=2),encoding='utf-8')
    if failures:raise SystemExit(f'{len(failures)} annotation archives failed; do not silently reduce benchmark')


if __name__=='__main__':main()
