from pathlib import Path
import csv
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parents[1]
rows = list(csv.DictReader((root / 'Multilabel.csv').open()))
for index in [0, 299, 300, 14999, 15000, 18000, 20999]:
    row = rows[index]
    doc = row['document']
    if doc.startswith('doc_'):
        number = int(doc[4:])
        candidates = sorted((root/'full_dataset_original/midv2019_dataset').glob(f'*/*{number:02d}_*.tif'))
    else:
        candidates = sorted((root/'full_dataset_original/midv500_dataset'/doc/'images').glob('*/*.tif'))
    def thumb(path):
        with Image.open(path) as im:
            return np.asarray(im.convert('RGB').resize((32,32)), dtype=np.float32)
    target = thumb(root/'dataset_224'/row['image_name'])
    scored = sorted((float(np.mean((thumb(p)-target)**2)), str(p.relative_to(root))) for p in candidates)
    print(index, row, scored[:3], flush=True)
