"""Image-only prediction and two/four visual tiles. No annotation input."""
import time
import cv2
import numpy as np
from PIL import Image,ImageOps
from research.v2_common import ROOT,sha

PROFILES=('raw2','raw4','rect2','rect4')

class Views:
    def __init__(self): self.session=None
    def prepare(self,image,profile):
        if profile not in PROFILES: raise ValueError('Unknown preprocessing')
        start=time.perf_counter();mode='raw'
        image=ImageOps.exif_transpose(image).convert('RGB')
        if profile.startswith('rect'):
            from research.neural_baseline import MODEL_SHA
            from research.recovery_upstream import decode_native
            from research.recovery_runtime import make_view
            from ekyc.module2_homography import order_corners
            from ekyc.io import StageError
            if self.session is None:
                import onnxruntime as ort
                path=ROOT/'research/cache/docaligner/fastvit_sa24.onnx'
                if sha(path)!=MODEL_SHA: raise ValueError('Localizer checksum mismatch')
                options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
                self.session=ort.InferenceSession(str(path),options,providers=['CPUExecutionProvider'])
            bgr=cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR);h,w=bgr.shape[:2]
            tensor=cv2.resize(bgr,(256,256)).transpose(2,0,1)[None].astype(np.float32)/255.
            heat=self.session.run(['heatmap'],{'img':np.ascontiguousarray(tensor)})[0]
            if not np.isfinite(heat).all():raise ValueError('Nonfinite corner prediction')
            points=decode_native(heat,h,w);quad=None
            if all(p is not None for p in points):
                try:quad=order_corners(points).tolist()
                except StageError:pass
            view,_,mode,_=make_view(bgr,dict(points=points,quad=quad),'completion')
            image=Image.fromarray(cv2.cvtColor(view,cv2.COLOR_BGR2RGB))
        return image,dict(preprocessing_seconds=time.perf_counter()-start,view_mode=mode,profile=profile,
                          processed_dimensions=list(image.size))

def pixels(image,profile):
    import torch
    n=4 if profile.endswith('4') else 2;size=(896,896 if n==4 else 448)
    canvas=ImageOps.pad(image,size,method=Image.Resampling.BICUBIC,color='white',centering=(.5,.5))
    array=np.stack([np.asarray(canvas.crop((x,y,x+448,y+448))).copy() for y in range(0,size[1],448) for x in (0,448)])
    tensor=torch.from_numpy(array).permute(0,3,1,2).float()/255
    return (tensor-torch.tensor([.485,.456,.406])[None,:,None,None])/torch.tensor([.229,.224,.225])[None,:,None,None]
