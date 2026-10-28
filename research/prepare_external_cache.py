"""Prepare pinned small author metadata blocks; optionally fetch public weights."""
import argparse
import hashlib
import ssl
import urllib.request
from pathlib import Path

import certifi

from research.fetch_annotations import read_range
from research.neural_baseline import MODEL_SHA

BLOCKS=(('head.bin','photo.tar',1048576,'890af18896149074d82d70d371297bb35d8c928cd80ddc0036bb14d7b8f13a67'),
        ('template_head.bin','templates.tar',5242880,'75dd3432dc70ced7642db64bedf5f8e7385664425f62dc80ef7b289a135133ad'))


def checked_write(path,value,expected):
    if hashlib.sha256(value).hexdigest()!=expected:raise ValueError(f'Source hash mismatch: {path.name}')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--include-model',action='store_true');args=parser.parse_args()
    for name,archive,count,expected in BLOCKS:
        path=Path('research/data/midv2020')/name
        value=path.read_bytes() if path.exists() else read_range('/midv-2020/dataset/'+archive,0,count)
        checked_write(path,value,expected);print('Verified',name,flush=True)
    if args.include_model:
        path=Path('research/cache/docaligner/fastvit_sa24.onnx')
        if path.exists():value=path.read_bytes()
        else:
            url='https://drive.usercontent.google.com/download?id=14vUH77v6yGg7zFctUgcT6BzV5Iisg4Dl&export=download&confirm=t'
            with urllib.request.urlopen(url,context=ssl.create_default_context(cafile=certifi.where()),timeout=60) as response:
                value=response.read(83084931)
        if len(value)!=83084930:raise ValueError('Unexpected author model size')
        checked_write(path,value,MODEL_SHA);print('Verified DocAligner model',flush=True)


if __name__=='__main__':main()
