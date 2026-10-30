"""Prediction-only document transforms, CRAFT detection and two frozen readers."""
import hashlib
import math
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import torch
from PIL import Image

from ekyc.io import StageError
from ekyc.module2_homography import order_corners
from ekyc.scanocr import VietnameseRecognizer
from research.neural_baseline import MODEL_SHA
from research.partial_support import decode_partial,observed_support
from research.support_regions import area,intersection,frame_polygon,halfplanes

POLICIES=('raw_fullframe','neural_strict','three_fullframe','three_support','three_support_bbox','three_parallelogram05')


def tick():return time.perf_counter(),time.process_time()
def elapsed(start):return dict(wall=time.perf_counter()-start[0],cpu=time.process_time()-start[1])


def expand_quad(quad,fraction=.05):
    normals,bounds=halfplanes(quad);bounds-=fraction*math.sqrt(area(quad))
    return order_corners([np.linalg.solve(np.stack([normals[i-1],normals[i]]),[bounds[i-1],bounds[i]]) for i in range(4)])


def warp_document(image,quad):
    quad=order_corners(quad)
    width=max(np.linalg.norm(quad[1]-quad[0]),np.linalg.norm(quad[2]-quad[3]))
    height=max(np.linalg.norm(quad[3]-quad[0]),np.linalg.norm(quad[2]-quad[1]))
    scale=min(1.,1600/max(width,height));width=max(2,round(width*scale));height=max(2,round(height*scale))
    transform=cv2.getPerspectiveTransform(quad,np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]]))
    output=cv2.warpPerspective(image,transform,(width,height),borderMode=cv2.BORDER_CONSTANT,borderValue=(255,255,255))
    return output,np.linalg.inv(transform)


def crop_support(image,polygon,mask=True):
    height,width=image.shape[:2];polygon=np.asarray(polygon,np.float32)
    lo=np.maximum(np.floor(polygon.min(axis=0)).astype(int),[0,0])
    hi=np.minimum(np.ceil(polygon.max(axis=0)).astype(int)+1,[width,height])
    x1,y1=lo;x2,y2=hi
    if x2-x1<2 or y2-y1<2:raise StageError('Empty support bbox')
    output=image[y1:y2,x1:x2].copy()
    if mask:
        inside=np.zeros(output.shape[:2],np.uint8)
        cv2.fillConvexPoly(inside,np.rint(polygon-[x1,y1]).astype(np.int32),255)
        output[inside==0]=255
    return output,np.array([[1.,0.,x1],[0.,1.,y1],[0.,0.,1.]])


def policy_image(image,localization,policy):
    if policy=='raw_fullframe':return image,np.eye(3),'raw'
    height,width=image.shape[:2];frame=frame_polygon(width,height);limit=.95*area(frame)
    if localization['quad'] is not None:
        quad=np.float32(localization['quad'])
        if area(intersection(quad,frame))>limit:raise StageError('Region exceeds fixed area gate')
        output,transform=warp_document(image,quad);return output,transform,'four_corner_warp'
    points=localization['points']
    if policy=='neural_strict' or sum(p is not None for p in points)!=3:raise StageError('Insufficient observed corners')
    if policy=='three_fullframe':return image,np.eye(3),'three_corner_fullframe'
    if policy=='three_parallelogram05':
        missing=points.index(None);completed=list(points)
        completed[missing]=(np.asarray(points[(missing-1)%4])+np.asarray(points[(missing+1)%4])-np.asarray(points[(missing+2)%4])).tolist()
        quad=expand_quad(order_corners(completed))
        if area(intersection(quad,frame))>limit:raise StageError('Region exceeds fixed area gate')
        output,transform=warp_document(image,quad);return output,transform,'completed_expanded_warp'
    polygon=observed_support(points,width,height)
    if area(polygon)>limit:raise StageError('Region exceeds fixed area gate')
    output,transform=crop_support(image,polygon,mask=policy=='three_support')
    return output,transform,'support_masked' if policy=='three_support' else 'support_bbox'


class BatchedVietOCR:
    """Same-width batches; per-sequence EOS keeps confidence comparable to single."""
    def __init__(self,directory):self.reader=VietnameseRecognizer(directory)

    def _translate(self,tensor):
        model=self.reader.model;batch=len(tensor);sums=torch.zeros(batch);counts=torch.zeros(batch)
        done=torch.zeros(batch,dtype=torch.bool);tokens=torch.ones((1,batch),dtype=torch.long)
        with torch.inference_mode():
            memory=model.transformer.forward_encoder(model.cnn(tensor))
            for _ in range(129):
                output,memory=model.transformer.forward_decoder(tokens,memory)
                probability=torch.softmax(output[:,-1,:],dim=-1)
                values,indices=torch.topk(probability,5);values=values[:,0];indices=indices[:,0]
                useful=(~done)&(indices>3)&(values>0)
                sums+=torch.where(useful,values,0);counts+=useful
                nxt=torch.where(done,2,indices);tokens=torch.cat([tokens,nxt[None]],dim=0)
                done|=indices==2
                if bool(done.all()):break
        confidence=torch.where(counts>0,sums/torch.clamp(counts,min=1),0)
        return [(self.reader.vocab.decode(row).strip(),float(c)) for row,c in zip(tokens.T.tolist(),confidence)]

    def predict_many(self,images):
        from vietocr.tool.translate import process_input
        config=self.reader.config['dataset'];groups=defaultdict(list);result=[None]*len(images)
        for index,image in enumerate(images):
            pil=Image.fromarray(image).convert('RGB')
            tensor=process_input(pil,config['image_height'],config['image_min_width'],config['image_max_width'])
            groups[tensor.shape[-1]].append((index,tensor))
        for group in groups.values():
            for offset in range(0,len(group),8):
                chunk=group[offset:offset+8];answers=self._translate(torch.cat([t for _,t in chunk]))
                for (index,_),answer in zip(chunk,answers):result[index]=answer
        return result

    def parity_check(self):
        samples=[]
        for text,width in [('TEST 123',300),('ABC',150),('2026/10/30',330),('DATA 00001',300)]:
            image=np.full((48,width),255,np.uint8)
            cv2.putText(image,text,(3,33),cv2.FONT_HERSHEY_SIMPLEX,.8,0,2)
            samples.extend([image,np.rot90(image,2).copy()])
        expected=[self.reader.predict(cv2.cvtColor(im,cv2.COLOR_GRAY2BGR)) for im in samples]
        actual=self.predict_many(samples)
        mismatches=sum(a[0]!=b[0] for a,b in zip(actual,expected))
        error=max(abs(a[1]-b[1]) for a,b in zip(actual,expected))
        if mismatches or error>1e-4:raise ValueError(f'Batched VietOCR parity failed: {mismatches}, {error}')
        return dict(synthetic_lines=len(samples),text_mismatches=mismatches,max_confidence_difference=error,tolerance=1e-4)


class Engine:
    def __init__(self,models):
        import easyocr
        torch.set_num_threads(2);cv2.setNumThreads(1)
        started=tick()
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        self.localizer=ort.InferenceSession('research/cache/docaligner/fastvit_sa24.onnx',options,
                                           providers=['CPUExecutionProvider'])
        self.english=easyocr.Reader(['en'],gpu=False,model_storage_directory=str(models/'easyocr'),download_enabled=False,verbose=False)
        self.vietnamese=BatchedVietOCR(models/'scanocr');self.loading=elapsed(started)
        started=tick();self.parity=self.vietnamese.parity_check()
        blank=np.full((64,320),255,np.uint8);cv2.putText(blank,'TEST123',(4,45),cv2.FONT_HERSHEY_SIMPLEX,1,0,2)
        self.english.recognize(blank,horizontal_list=[[0,320,0,64]],free_list=[],rotation_info=[180],batch_size=16,detail=1,reformat=False)
        self.warmup=elapsed(started)

    def locate(self,image):
        started=tick();height,width=image.shape[:2]
        tensor=cv2.resize(image,(256,256),interpolation=cv2.INTER_LINEAR).transpose(2,0,1)[None].astype(np.float32)/255.
        heatmap=self.localizer.run(['heatmap'],{'img':np.ascontiguousarray(tensor)})[0]
        if not np.isfinite(heatmap).all():raise ValueError('Nonfinite localizer output')
        points=decode_partial(heatmap,height,width);quad=None
        if all(p is not None for p in points):
            try:quad=order_corners(points).tolist()
            except StageError:pass
        return dict(points=points,quad=quad),elapsed(started)

    def ocr(self,image):
        from easyocr.utils import get_image_list
        started=tick()
        horizontal,free=self.english.detect(image,canvas_size=1280,mag_ratio=1.,text_threshold=.55,
            low_text=.3,link_threshold=.3,min_size=6,width_ths=.35,add_margin=.06)
        boxes=[np.float32([[x1,y1],[x2,y1],[x2,y2],[x1,y2]]) for x1,x2,y1,y2 in horizontal[0] if x2>x1 and y2>y1]
        boxes.extend(np.float32(box) for box in free[0])
        boxes=sorted(boxes,key=lambda q:(float(q[:,1].min()),float(q[:,0].min())))
        truncated=max(0,len(boxes)-80);boxes=boxes[:80]
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY);detection=elapsed(started)
        if not boxes:
            return dict(predictions={'easyocr_en':[],'vietocr':[]},detection=detection,
                recognition={k:dict(wall=0.,cpu=0.) for k in ('easyocr_en','vietocr')},truncated_regions=truncated)
        started=tick()
        recognized=self.english.recognize(gray,horizontal_list=[],free_list=[q.tolist() for q in boxes],
            decoder='greedy',batch_size=16,workers=0,detail=1,rotation_info=[180],paragraph=False,reformat=False)
        english_time=elapsed(started)
        english=[dict(box=np.asarray(box,float).tolist(),text=str(text),confidence=float(conf) if np.isfinite(conf) else 0.) for box,text,conf in recognized]
        started=tick();cropped,_=get_image_list([],boxes,gray,model_height=64,sort_output=True)
        images=[im for _,im in cropped];rotated=[np.rot90(im,2).copy() for im in images]
        answers=self.vietnamese.predict_many(images+rotated)
        vietnamese=[]
        for index,(box,_) in enumerate(cropped):
            text,confidence=max((answers[index],answers[index+len(images)]),key=lambda item:item[1])
            vietnamese.append(dict(box=np.asarray(box,float).tolist(),text=text,confidence=float(confidence)))
        vi_time=elapsed(started)
        return dict(predictions={'easyocr_en':english,'vietocr':vietnamese},detection=detection,
            recognition={'easyocr_en':english_time,'vietocr':vi_time},truncated_regions=truncated)


def to_source(predictions,transform):
    output=[]
    for pred in predictions:
        box=cv2.perspectiveTransform(np.float32(pred['box'])[None],np.asarray(transform,float))[0]
        if not np.isfinite(box).all():raise ValueError('Nonfinite inverse text box')
        output.append(dict(pred,box=box.astype(float).tolist()))
    return output


def raster_hash(image):
    return hashlib.sha256(str(image.shape).encode()+image.tobytes()).hexdigest()
