"""Verified optional upstream code/models, without modifying site-packages."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'cache/upstream'
WHEEL_SHA='971d7d5f223a7a808662229df1ef69893809d8457d834e6373d3854bc1782cbf'
LATIN_SHA='b20bd37c168a570f583afbc8cd7925603890efbcdc000a59e22c269d160b5f5a'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare():
    wheel=CACHE/'rapidocr-1.4.4.whl'
    if sha(wheel)!=WHEEL_SHA:raise ValueError('RapidOCR wheel SHA256 mismatch')
    target=CACHE/'rapid144';target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(wheel) as archive:
        for item in archive.infolist():
            if item.is_dir():continue
            path=(target/item.filename).resolve()
            if not path.is_relative_to(target.resolve()):raise ValueError('Unsafe wheel path')
            if item.file_size>20_000_000:raise ValueError('Unexpected wheel member size')
            value=archive.read(item)
            if not path.exists() or hashlib.sha256(path.read_bytes()).digest()!=hashlib.sha256(value).digest():
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    sys.path.insert(0,str(target)) if str(target) not in sys.path else None
    return target


def manifest():
    target=prepare();files={str(p.relative_to(target)).replace('\\','/'):sha(p) for p in target.rglob('*')
                             if p.is_file() and p.suffix in ('.py','.yaml','.onnx')}
    latin=CACHE/'latin_PP-OCRv5_rec_mobile.onnx'
    if sha(latin)!=LATIN_SHA:raise ValueError('Pinned Latin recognizer SHA256 mismatch')
    return dict(rapidocr_version='1.4.4',wheel_sha256=WHEEL_SHA,files_sha256=files,
        author_source_sha256={name:sha(CACHE/name) for name in ('docaligner_heatmap_reg_infer.py','capybara-1.0.1.whl')},
        latin_model_sha256=sha(latin),latin_model_bytes=latin.stat().st_size,
        latin_model_source='https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/rec/latin_PP-OCRv5_rec_mobile.onnx',
        installed_dependencies=False,source='Official PyPI wheel; official RapidAI model registry',
        upstream_code_unmodified=True)


if __name__=='__main__':
    prepare();from rapidocr_onnxruntime import RapidOCR
    import cv2,numpy as np,time
    from PIL import Image,ImageDraw,ImageFont
    import onnxruntime as ort
    p=CACHE/'latin_PP-OCRv5_rec_mobile.onnx'
    session=ort.InferenceSession(str(p),providers=['CPUExecutionProvider'])
    print('LATIN_IO',[(i.name,i.shape) for i in session.get_inputs()])
    image=Image.new('RGB',(900,400),'white');draw=ImageDraw.Draw(image)
    draw.text((40,60),'FULL NAME: NGUYEN THI MAI',font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',34),fill='black')
    draw.text((40,140),'ID NUMBER: 000012345678',font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',34),fill='black')
    engine=RapidOCR(rec_model_path=str(p.resolve()),intra_op_num_threads=2,inter_op_num_threads=1,
                    det_limit_type='max',det_limit_side_len=960)
    started=time.perf_counter();result,_=engine(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR))
    print('SYNTHETIC_SMOKE',result,'wall',time.perf_counter()-started)
    out=ROOT/'results/recovery_v4';out.mkdir(parents=True,exist_ok=True)
    (out/'assets.json').write_text(json.dumps(manifest(),indent=2),encoding='utf-8')
