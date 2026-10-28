from pathlib import Path
import csv
import numpy as np
from PIL import Image
from ekyc.dataset import thumbnail

root = Path(__file__).resolve().parents[1]
rows = [r for r in csv.DictReader((root/'Multilabel.csv').open()) if r['document']=='04_aut_id']
paths = sorted((root/'full_dataset_original/midv500_dataset/04_aut_id/images').glob('*/*.tif'))
vectors = np.load(root/'data/thumbnail_cache/midv500_04.npz')['vectors']
for row in rows:
    t = thumbnail(root/'dataset_224'/row['image_name'])
    d = np.mean((vectors-t)**2, axis=1)
    best = np.argsort(d)[:3]
    if d[best[0]]/d[best[1]] < .5:
        continue
    print(row, [(str(paths[i]),float(d[i])) for i in best], flush=True)
    with Image.open(root/'dataset_224'/row['image_name']) as im:
        target = np.asarray(im.convert('RGB'), dtype=np.float32)
    for i in best:
        with Image.open(paths[i]) as im:
            for method in [Image.Resampling.BILINEAR,Image.Resampling.BICUBIC,Image.Resampling.LANCZOS,Image.Resampling.NEAREST]:
                candidate=np.asarray(im.convert('RGB').resize((224,224),method), dtype=np.float32)
                print(paths[i].name, method, np.mean((target-candidate)**2), flush=True)
