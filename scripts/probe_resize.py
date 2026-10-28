import cv2
import numpy as np
from pathlib import Path

root=Path(__file__).resolve().parents[1]
target=cv2.imread(str(root/'dataset_224/img_00204.jpg'))
for filename in ['KA04_01.tif','KA04_02.tif','KA04_03.tif']:
    image=cv2.imread(str(root/'full_dataset_original/midv500_dataset/04_aut_id/images/KA'/filename))
    for method in [cv2.INTER_AREA,cv2.INTER_LINEAR,cv2.INTER_CUBIC,cv2.INTER_LANCZOS4]:
        candidate=cv2.resize(image,(224,224),interpolation=method)
        _,encoded=cv2.imencode('.jpg',candidate)
        decoded=cv2.imdecode(encoded,cv2.IMREAD_COLOR)
        print(filename,method,float(np.mean((candidate.astype(float)-target)**2)),float(np.mean((decoded.astype(float)-target)**2)),flush=True)
