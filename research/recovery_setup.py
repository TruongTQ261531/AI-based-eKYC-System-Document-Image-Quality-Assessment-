"""Recreate optional assets/data in the existing environment, never pip install."""
import argparse
import hashlib
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import certifi

from research.benchmark import save
from research.external_midv2020 import metadata,index_directories,acquire_class
from research.recovery_assets import CACHE,WHEEL_SHA,LATIN_SHA,manifest

ASSETS=(
 ('rapidocr-1.4.4.whl','https://files.pythonhosted.org/packages/ba/12/1e5497183bdbe782dbb91bad1d0d2297dba4d2831b2652657f7517bfc6df/rapidocr_onnxruntime-1.4.4-py3-none-any.whl',WHEEL_SHA,16_000_000),
 ('capybara-1.0.1.whl','https://files.pythonhosted.org/packages/51/0b/0fe4ea2ba3675fd0bb946d9d0179759b72695cca48babd07b7cff134c959/capybara_docsaid-1.0.1-py3-none-any.whl','0872a0c21c128e66f4efc595d36bafca6b22a01c462c5329ce59d387c961ad06',200_000),
 ('latin_PP-OCRv5_rec_mobile.onnx','https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.9.2/onnx/PP-OCRv5/rec/latin_PP-OCRv5_rec_mobile.onnx',LATIN_SHA,10_000_000),
 ('lcnet100.onnx','https://drive.usercontent.google.com/download?id=1IlbLPkCv-TdaBLOPh_4J97P1_KHYYJ7a&export=download&confirm=t','f4117b786e3a18470f3865c93f3c2bd69d9b998edd60f385574a5c665e79594e',6_000_000),
 ('docaligner_heatmap_reg_infer.py','https://raw.githubusercontent.com/DocsaidLab/DocAligner/3275b0f07f8e99d8c01cb0774dea2549be1416b6/docaligner/heatmap_reg/infer.py','cb333575ccde501bc731a73de21f4fd05a96247550e45fea969e79d6cc1e4672',100_000),
 ('fonts/NotoSans-Regular.ttf','https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf','b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5',1_000_000),
 ('fonts/NotoSerif-Regular.ttf','https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSerif/NotoSerif-Regular.ttf','c8f669ceb2c9c60ccf55198b305e08a997ffca79a38cc7eeb551e643cbe66505',1_000_000))


def fetch_asset(name,url,expected,limit):
    path=CACHE/name
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Existing asset mismatch: '+name)
        return
    with urllib.request.urlopen(url,context=ssl.create_default_context(cafile=certifi.where()),timeout=60) as response:
        value=response.read(limit+1)
    if len(value)>limit or hashlib.sha256(value).hexdigest()!=expected:raise ValueError('Downloaded asset mismatch: '+name)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',action='store_true');args=parser.parse_args()
    for asset in ASSETS:fetch_asset(*asset);print('VERIFIED',asset[0],flush=True)
    save('research/results/recovery_v4/assets_recreated.json',manifest())
    if args.data:
        # Reuse the existing bounded head-block acquisition and frozen FastViT
        # source. Import main only to pass its explicit model-download flag.
        import subprocess,sys
        subprocess.run([sys.executable,'-m','research.prepare_external_cache','--include-model'],check=True)
        old=Path('research/data/midv2020/selection.json')
        if not old.exists():
            photos,ps=metadata('photo');templates,ts=metadata('templates')
            pd=index_directories('photo',photos,ps);td=index_directories('templates',templates,ts)
            jobs=[(c,photos[c],templates[c],pd[c],td[c]) for c in sorted(photos)]
            with ThreadPoolExecutor(3) as pool:records=[r for group in pool.map(acquire_class,jobs) for r in group]
            save(old,records)
        subprocess.run([sys.executable,'-m','research.recovery_acquire'],check=True)
        subprocess.run([sys.executable,'-m','research.recovery_data'],check=True)
    print('SETUP_COMPLETE; existing environment unchanged',flush=True)


if __name__=='__main__':main()
