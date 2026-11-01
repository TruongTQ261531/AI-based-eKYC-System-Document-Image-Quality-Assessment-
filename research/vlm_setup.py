"""Pinned, optional training runtime in ignored cache; never installs into a venv."""
import argparse
import concurrent.futures
import hashlib
import html
import importlib.metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'research/cache/vlm_lora_v1'
OUT = ROOT / 'research/results/vlm_lora_v1'
MODEL_ID = '5CD-AI/Vintern-1B-v3_5'
REVISION = 'b98f263eab246eb5269ade64edbdca8a887dc44d'
PACKAGES = {
    'torch': '2.7.1+cu126', 'torchvision': '0.22.1+cu126',
    'transformers': '4.46.3', 'peft': '0.14.0', 'accelerate': '1.2.1',
    'huggingface-hub': '0.28.1', 'tokenizers': '0.20.3',
    'safetensors': '0.5.3', 'timm': '1.0.12', 'einops': '0.8.0',
    'requests': '2.32.3', 'urllib3': '2.3.0', 'charset-normalizer': '3.4.1',
    'idna': '3.10', 'certifi': '2025.1.31', 'psutil': '6.1.1',
    'regex': '2024.11.6', 'tqdm': '4.67.1', 'colorama': '0.4.6',
}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    tmp.replace(path)


def get(url):
    with urllib.request.urlopen(url, timeout=90) as r:
        return r.read()


def lock():
    path = OUT / 'assets.json'
    if path.exists():
        previous=json.loads(path.read_text(encoding='utf-8'))
        if {r['package']:r['version'] for r in previous['packages']}==PACKAGES: return previous
    records = []
    for name, version in PACKAGES.items():
        if name in ('torch', 'torchvision'):
            page = get(f'https://download.pytorch.org/whl/cu126/{name}/').decode()
            wanted = f'{name}-{version}-cp311-cp311-win_amd64.whl'
            links = [html.unescape(x) for x in re.findall(r'href="([^"]+)"', page)]
            url = next(x for x in links if urllib.parse.unquote(x.split('#')[0]).endswith('/' + wanted))
            digest = urllib.parse.parse_qs(urllib.parse.urlsplit(url).fragment)['sha256'][0]
            url = url.split('#')[0]
        else:
            data = json.loads(get(f'https://pypi.org/pypi/{name}/{version}/json'))
            candidates = [x for x in data['urls'] if x['filename'].endswith('.whl') and (
                x['filename'].endswith('none-any.whl') or
                'win_amd64' in x['filename'] and
                ('cp311-' in x['filename'] or any(f'cp{n}-abi3-' in x['filename'] for n in ('37','38','39','310'))))]
            universal = [x for x in candidates if x['filename'].endswith('none-any.whl')]
            if universal: candidates = universal
            if len(candidates) != 1:
                raise ValueError((name, [x['filename'] for x in candidates]))
            wheel = candidates[0]; wanted = wheel['filename']; url = wheel['url']; digest = wheel['digests']['sha256']
        records.append(dict(package=name, version=version, file=wanted, url=url, sha256=digest))
        print('LOCK', name, version, flush=True)
    data = json.loads(get(f'https://huggingface.co/api/models/{MODEL_ID}/revision/{REVISION}?blobs=true'))
    model = []
    for item in data['siblings']:
        name = item['rfilename']
        if name == '.gitattributes': continue
        model.append(dict(file=name, bytes=item['size'], sha256=item.get('lfs', {}).get('sha256'),
                          git_blob=item.get('blobId'), url=f'https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/{name}'))
    result = dict(model_id=MODEL_ID, revision=REVISION, packages=records, model=model,
                  site_packages_modified=False, new_virtualenv_created=False)
    save(path, result)
    return result


def parallel_tail(row,part):
    """Resume the existing prefix and fetch independently checked HTTP ranges."""
    request=urllib.request.Request(row['url'],headers={'Range':'bytes=0-0'})
    with urllib.request.urlopen(request,timeout=90) as response:
        if response.status!=206 or not response.headers.get('Content-Range'): return False
        total=int(response.headers['Content-Range'].split('/')[-1]);response.read(1)
    start=part.stat().st_size if part.exists() else 0
    if total<64*2**20 or start>=total: return False
    directory=CACHE/'download_segments'/hashlib.sha256(row['url'].encode()).hexdigest()
    directory.mkdir(parents=True,exist_ok=True)
    ranges=[(a,min(a+64*2**20,total)-1) for a in range(start,total,64*2**20)]
    def fetch(bounds):
        a,b=bounds;path=directory/f'{a}_{b}.part'
        for attempt in range(6):
            size=path.stat().st_size if path.exists() else 0
            if size==b-a+1: return path
            try:
                request=urllib.request.Request(row['url'],headers={'Range':f'bytes={a+size}-{b}'})
                with urllib.request.urlopen(request,timeout=120) as response:
                    expected=f'bytes {a+size}-{b}/{total}'
                    if response.status!=206 or response.headers.get('Content-Range')!=expected:
                        raise ValueError('Range response contract mismatch')
                    with path.open('ab') as f:
                        while chunk:=response.read(2*2**20): f.write(chunk)
                if path.stat().st_size!=b-a+1: raise ValueError('Incomplete range')
                return path
            except Exception:
                if attempt==5: raise
                time.sleep(min(2**attempt,20))
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        jobs={pool.submit(fetch,r):r for r in ranges}
        done=start
        for future in concurrent.futures.as_completed(jobs):
            path=future.result();done+=path.stat().st_size
            print('RANGES',part.name,round(done/2**20),'/',round(total/2**20),'MiB',flush=True)
    with part.open('ab') as output:
        for a,b in ranges:
            with (directory/f'{a}_{b}.part').open('rb') as f:
                while chunk:=f.read(4*2**20): output.write(chunk)
    return True


def download(row, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    def valid(path):
        if row.get('bytes') is not None and path.stat().st_size != row['bytes']: return False
        if row.get('sha256'): return sha(path) == row['sha256']
        raw = path.read_bytes()
        return hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest() == row['git_blob']
    if target.exists():
        if not valid(target): raise ValueError(f'Cached hash mismatch: {target.name}')
        return
    part = target.with_suffix(target.suffix + '.part')
    if (row.get('bytes',0)>64*2**20 or row['file'].startswith('torch-')):
        if parallel_tail(row,part):
            if not valid(part): raise ValueError('Parallel download checksum mismatch')
            part.replace(target);print('VERIFIED',target.name,target.stat().st_size,flush=True);return
    for attempt in range(6):
        offset = part.stat().st_size if part.exists() else 0
        try:
            req = urllib.request.Request(row['url'], headers={'Range': f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(req, timeout=120) as response:
                resume = offset and response.status == 206
                done = offset if resume else 0
                with part.open('ab' if resume else 'wb') as f:
                    last = time.monotonic()
                    while chunk := response.read(2 * 1024 * 1024):
                        f.write(chunk); done += len(chunk)
                        if time.monotonic() - last > 20:
                            print('DOWNLOAD', target.name, round(done / 2**20), 'MiB', flush=True); last = time.monotonic()
            if not valid(part): raise ValueError('Downloaded checksum/size mismatch')
            part.replace(target)
            print('VERIFIED', target.name, target.stat().st_size, flush=True)
            return
        except Exception as exc:
            print('RETRY', target.name, attempt + 1, type(exc).__name__, str(exc)[:180], flush=True)
            if attempt == 5: raise
            time.sleep(min(2 ** attempt, 20))


def acquire(kind):
    manifest = lock()
    if kind in ('model', 'all', 'code'):
        for row in manifest['model']:
            if kind == 'code' and row['file'].endswith('.safetensors'): continue
            download(row, CACHE / 'model' / row['file'])
    if kind in ('runtime', 'all', 'libraries'):
        site = CACHE / 'site'; site.mkdir(parents=True, exist_ok=True)
        for row in manifest['packages']:
            if kind=='libraries' and row['package'] in ('torch','torchvision'): continue
            path = CACHE / 'wheels' / row['file']; download(row, path)
            marker = site / (row['package'].replace('-', '_') + '.extracted.json')
            if marker.exists():
                if json.loads(marker.read_text())['sha256'] != row['sha256']: raise ValueError('Runtime extraction changed')
                continue
            with zipfile.ZipFile(path) as wheel:
                for name in wheel.namelist():
                    if not (site / name).resolve().is_relative_to(site.resolve()): raise ValueError('Unsafe wheel path')
                wheel.extractall(site)
            save(marker, dict(sha256=row['sha256'], file=row['file']))
            print('EXTRACTED', row['package'], flush=True)


def environment():
    env = os.environ.copy()
    env.update(PYTHONPATH=str(CACHE / 'site') + os.pathsep + str(ROOT), HF_HOME=str(CACHE / 'hf'),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', PYTHONIOENCODING='utf-8',
               CUBLAS_WORKSPACE_CONFIG=':4096:8')
    return env


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['lock','code','model','runtime','libraries','all','run'])
    parser.add_argument('command', nargs=argparse.REMAINDER); args = parser.parse_args()
    if args.action == 'lock': lock()
    elif args.action == 'run':
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command: raise ValueError('Expected Python arguments after run')
        raise SystemExit(subprocess.call([sys.executable, *command], cwd=ROOT, env=environment()))
    else: acquire(args.action)


if __name__ == '__main__': main()
