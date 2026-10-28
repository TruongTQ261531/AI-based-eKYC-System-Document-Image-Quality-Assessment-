"""Explicit, local-only OCR/PAD model setup. Never invoked by an API request."""
import hashlib
import json
import urllib.request

from ekyc.config import ROOT

SCAN_REV = '700b8c73e450668780af7b96d65ab88afc288e86'
VIET_REV = 'fe8c3a7fc714aec57ab81cec844eb3adf0c1636c'
ASSETS = {
    'scanocr/yolo_v11_best.onnx': (
        f'https://huggingface.co/phgrouptechs/scanocr-identity-vi/resolve/{SCAN_REV}/yolo_v11_best.onnx',
        '8303bd7f8d80cbb0ae7f2fa34398ecb09ce0fc09ce2423894dab755190a0d6e2'),
    'scanocr/dataset_yolo.yaml': (
        f'https://huggingface.co/phgrouptechs/scanocr-identity-vi/resolve/{SCAN_REV}/dataset_yolo.yaml',
        '5cf123fc38b1cce839dd465b60de5bdaddd3a55289e408ef5fdcf27e46649db6'),
    'scanocr/base.yml': (f'https://raw.githubusercontent.com/pbcquoc/vietocr/{VIET_REV}/config/base.yml',
        '9c8283fadb950f06f5d3400475f80d5355700ff315c9c48b7875e6ea66647d1c'),
    'scanocr/vgg-transformer.yml': (
        f'https://raw.githubusercontent.com/pbcquoc/vietocr/{VIET_REV}/config/vgg-transformer.yml',
        '0df9feee197754c7381871e5dfd07c6f3e292a4853eece6f1af240923e57c907'),
    'scanocr/vgg_transformer.pth': ('https://vocr.vn/data/vietocr/vgg_transformer.pth',
        '380512193a8b6cbf6fad80deacdc9b6939d10d473d199892fc6408d13775ea59'),
    'pad/MiniFASNetV2.onnx': (
        'https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV2.onnx',
        'b32929adc2d9c34b9486f8c4c7bc97c1b69bc0ea9befefc380e4faae4e463907'),
    'pad/MiniFASNetV1SE.onnx': (
        'https://github.com/yakhyo/face-anti-spoofing/releases/download/weights/MiniFASNetV1SE.onnx',
        'ebab7f90c7833fbccd46d3a555410e78d969db5438e169b6524be444862b3676'),
}


def main():
    manifest = ROOT/'models/identity_model_sources.json'
    prior = {r['file']: r['sha256'] for r in json.loads(manifest.read_text())} if manifest.exists() else {}
    records = []
    for name, (url, expected) in ASSETS.items():
        target = ROOT/'models'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        expected = expected or prior.get(name)
        if not target.is_file():
            print(f'Downloading {name}', flush=True)
            partial = target.with_suffix(target.suffix+'.download')
            with urllib.request.urlopen(url, timeout=60) as response, partial.open('wb') as out:
                while chunk := response.read(1024*1024):
                    out.write(chunk)
            with partial.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            if expected and digest != expected:
                raise ValueError(f'Checksum mismatch: {name}')
            partial.replace(target)
        with target.open('rb') as source:
            digest = hashlib.file_digest(source, 'sha256').hexdigest()
        if expected and digest != expected:
            raise ValueError(f'Checksum mismatch: {name}')
        records.append(dict(file=name, url=url, sha256=digest, bytes=target.stat().st_size))
        print(f'Ready {name}: {target.stat().st_size} bytes', flush=True)
    manifest.write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
