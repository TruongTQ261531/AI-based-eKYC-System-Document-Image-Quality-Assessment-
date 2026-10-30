"""Prediction-only views and independent RapidOCR baselines for research/web."""
import copy
import math
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from ekyc.document_fields import observed_information
from ekyc.io import StageError
from ekyc.module2_homography import order_corners
from research.e2e_pipeline import policy_image,warp_document,to_source,raster_hash
from research.neural_baseline import MODEL_SHA
from research.partial_support import decode_partial
from research.recovery_upstream import decode_native
from research.recovery_assets import prepare,CACHE,sha

POLICIES=('raw','strict','completion','bbox','contour','text_deskew','lcnet')
READERS=('rapid_v4','rapid_latin_v5')
LCNET_SHA='f4117b786e3a18470f3865c93f3c2bd69d9b998edd60f385574a5c665e79594e'
FEATURE_NAMES=('bias','log_width','log_height','aspect','corner_fraction','view_area_ratio','mean_confidence',
               'min_confidence','low_confidence_fraction','log_regions','log_characters','edge_fraction',
               'text_area_fraction','mean_line_aspect','empty_fraction','routed')+tuple('policy_'+p for p in POLICIES)


def semantic(predictions):
    fields,items,kind=observed_information(predictions,{})
    # Extend only the explicitly printed generic label, never expected values.
    if 'id_number' not in fields:
        from ekyc.document_fields import fold,text_rows
        import re
        rows=text_rows(predictions)
        for i,text in enumerate(rows):
            match=re.search(r'\bso\s+giay\s+to\s*[:.]?',fold(text))
            if match:
                candidate=text[match.end():].strip(' :')
                if not candidate and i+1<len(rows):candidate=rows[i+1].strip()
                if candidate:fields['id_number']=candidate
    return fields


def contour_view(image):
    scale=min(1.,960/max(image.shape[:2]));small=cv2.resize(image,None,fx=scale,fy=scale)
    gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY);edges=cv2.Canny(cv2.GaussianBlur(gray,(5,5),0),40,130)
    contours,_=cv2.findContours(edges,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    for c in sorted(contours,key=cv2.contourArea,reverse=True)[:30]:
        q=cv2.approxPolyDP(c,.025*cv2.arcLength(c,True),True)
        if len(q)!=4 or cv2.contourArea(q)<.08*gray.size:continue
        try:return (*warp_document(image,order_corners(q.reshape(4,2)/scale)),'contour_warp',True)
        except (StageError,np.linalg.LinAlgError):continue
    return image,np.eye(3),'raw_fallback',True


def text_deskew(image,raw_predictions):
    angles=[];weights=[]
    for p in raw_predictions:
        q=np.asarray(p['box']);edge=q[1]-q[0];angle=math.degrees(math.atan2(edge[1],edge[0]))
        if abs(angle)<=35 and np.linalg.norm(edge)>20:
            angles.append(angle);weights.append(np.linalg.norm(edge))
    if len(angles)<2:return image,np.eye(3),'raw_fallback',True
    order=np.argsort(angles);a=np.array(angles)[order];w=np.array(weights)[order]
    angle=float(a[np.searchsorted(np.cumsum(w),sum(w)/2)])
    if abs(angle)<.5:return image,np.eye(3),'raw_fallback',True
    h,wi=image.shape[:2];M=cv2.getRotationMatrix2D((wi/2,h/2),angle,1.)
    c,s=abs(M[0,0]),abs(M[0,1]);nw,nh=math.ceil(wi*c+h*s),math.ceil(h*c+wi*s)
    M[0,2]+=nw/2-wi/2;M[1,2]+=nh/2-h/2
    out=cv2.warpAffine(image,M,(nw,nh),borderValue=(255,255,255))
    H=np.vstack([M,[0,0,1]])
    return out,np.linalg.inv(H),'predicted_text_deskew',True


def make_view(image,location,policy,raw_predictions=None,lcnet=None):
    if policy=='raw':return image,np.eye(3),'raw',True
    if policy=='contour':return contour_view(image)
    if policy=='text_deskew':return text_deskew(image,raw_predictions or [])
    loc=lcnet if policy=='lcnet' else location
    old={'strict':'neural_strict','completion':'three_parallelogram05','bbox':'three_support_bbox','lcnet':'neural_strict'}[policy]
    try:
        pixels,inverse,mode=policy_image(image,loc,old);return pixels,inverse,mode,True
    except (StageError,np.linalg.LinAlgError):
        if policy=='strict':return None,None,'review',False
        return image,np.eye(3),'raw_fallback',True


def features(predictions,shape,original_shape,corner_count,policy,routed):
    h,w=shape;oh,ow=original_shape;conf=[p['confidence'] for p in predictions];characters=sum(len(p['text']) for p in predictions)
    edge=0;areas=[];aspects=[]
    for p in predictions:
        q=np.asarray(p['box']);x1,y1=q.min(axis=0);x2,y2=q.max(axis=0)
        edge+=bool(x1<.025*w or x2>.975*w or y1<.025*h or y2>.975*h)
        areas.append(max(0,(x2-x1)*(y2-y1)));aspects.append((x2-x1)/max(1,y2-y1))
    n=max(1,len(predictions))
    return [1.,math.log1p(w)/8,math.log1p(h)/8,w/max(h,1)/3,corner_count/4,w*h/max(ow*oh,1),
            float(np.mean(conf)) if conf else 0.,min(conf,default=0.),sum(c<.7 for c in conf)/n,
            math.log1p(len(predictions))/5,math.log1p(characters)/8,edge/n,sum(areas)/max(w*h,1),
            float(np.mean(aspects))/20 if aspects else 0.,sum(not p['text'].strip() for p in predictions)/n,float(routed)]+[float(policy==p) for p in POLICIES]


class RecoveryEngine:
    def __init__(self):
        cv2.setNumThreads(1);prepare();from rapidocr_onnxruntime import RapidOCR
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        self.sessions={}
        for key,path,expected in [('fastvit',Path('research/cache/docaligner/fastvit_sa24.onnx'),MODEL_SHA),
                                  ('lcnet',CACHE/'lcnet100.onnx',LCNET_SHA)]:
            if sha(path)!=expected:raise ValueError('Localizer source hash mismatch')
            self.sessions[key]=ort.InferenceSession(str(path),options,providers=['CPUExecutionProvider'])
        cfg=dict(intra_op_num_threads=2,inter_op_num_threads=1,det_limit_type='max',det_limit_side_len=960)
        self.readers={'rapid_v4':RapidOCR(**cfg),'rapid_latin_v5':RapidOCR(**cfg,rec_model_path=str((CACHE/'latin_PP-OCRv5_rec_mobile.onnx').resolve()))}

    def locate(self,image,key='fastvit'):
        h,w=image.shape[:2];tensor=cv2.resize(image,(256,256)).transpose(2,0,1)[None].astype(np.float32)/255
        heatmap=self.sessions[key].run(['heatmap'],{'img':np.ascontiguousarray(tensor)})[0]
        if not np.isfinite(heatmap).all():raise ValueError('Nonfinite heatmap')
        points=decode_native(heatmap,h,w);quad=None
        if all(p is not None for p in points):
            try:quad=order_corners(points).tolist()
            except StageError:pass
        return dict(points=points,quad=quad)

    def ocr(self,image,reader):
        wall=time.perf_counter();cpu=time.process_time();result,stages=self.readers[reader](image)
        predictions=[dict(box=np.asarray(q,float).tolist(),text=str(text),confidence=float(conf)) for q,text,conf in result or []]
        if any(not np.isfinite(p['confidence']) for p in predictions):raise ValueError('Nonfinite OCR confidence')
        return dict(predictions=predictions,wall=time.perf_counter()-wall,cpu=time.process_time()-cpu,native_stages=stages)

    def views(self,image,*,policy_order=None,readers=READERS):
        # The predictor takes pixels only. No annotation, ID, language, layout
        # or expected document field enters localization/OCR/semantic parsing.
        wall=time.perf_counter();cpu=time.process_time();loc=self.locate(image)
        local=dict(wall=time.perf_counter()-wall,cpu=time.process_time()-cpu)
        wall=time.perf_counter();cpu=time.process_time();lc=self.locate(image,'lcnet')
        ltime=dict(wall=time.perf_counter()-wall,cpu=time.process_time()-cpu)
        count=sum(p is not None for p in loc['points']);memo={};rows=[];raw={}
        # Deskew depends on the raw OCR probe. Charge that probe explicitly.
        requested=list(policy_order or POLICIES)
        order=['raw']+[p for p in requested if p!='raw']
        for policy in order:
            for reader in readers:
                tw=time.perf_counter();tc=time.process_time()
                pixels,inverse,mode,routed=make_view(image,loc,policy,raw.get(reader,[]),lc)
                transform=dict(wall=time.perf_counter()-tw,cpu=time.process_time()-tc)
                if routed:
                    rhash=raster_hash(pixels);key=(reader,rhash);reused=key in memo
                    if not reused:memo[key]=self.ocr(pixels,reader)
                    answer=memo[key];pred=answer['predictions']
                else:rhash=None;reused=False;pred=[];answer=dict(wall=0.,cpu=0.,native_stages=None)
                if policy=='raw':raw[reader]=pred
                probe=next((r for r in rows if r['policy']=='raw' and r['engine']==reader),None)
                extra=probe['ocr_wall'] if policy=='text_deskew' and rhash!=probe['raster_sha256'] else 0.
                extra_cpu=probe['ocr_cpu'] if extra else 0.
                used=(dict(wall=0.,cpu=0.) if policy in ('raw','contour','text_deskew') else ltime if policy=='lcnet' else local)
                mapping_wall=time.perf_counter();mapping_cpu=time.process_time()
                source=to_source(pred,inverse) if routed else []
                sem=semantic(pred)
                mw=time.perf_counter()-mapping_wall;mc=time.process_time()-mapping_cpu
                shape=pixels.shape[:2] if routed else image.shape[:2]
                rows.append(dict(policy=policy,engine=reader,routed=routed,transform_mode=mode,raster_sha256=rhash,
                    ocr_reused_within_case=reused,observed_corners=count,shape=list(shape),
                    features=features(pred,shape,image.shape[:2],count,policy,routed),
                    total_wall=used['wall']+transform['wall']+answer['wall']+extra+mw,
                    total_cpu=used['cpu']+transform['cpu']+answer['cpu']+extra_cpu+mc,
                    ocr_wall=answer['wall'],ocr_cpu=answer['cpu'],probe_wall=extra,
                    localize_wall=used['wall'],localize_cpu=used['cpu'],transform_wall=transform['wall'],transform_cpu=transform['cpu'],
                    semantic_map_wall=mw,semantic_map_cpu=mc,
                    _private_predictions=source,_private_semantic=sem))
        return rows,dict(localizer_calls=2,unique_ocr_executions=len(memo))

    def online(self,image,locked,reader='rapid_latin_v5'):
        """Actually execute one completion and at most one OCR fallback."""
        from research.recovery_selection import cascade_decision
        started=time.perf_counter();cpu=time.process_time();loc=self.locate(image)
        count=sum(p is not None for p in loc['points']);localizer_calls=1;ocr_calls=0;memo={}
        def run(policy):
            nonlocal localizer_calls,ocr_calls
            lc=None
            if policy=='lcnet':lc=self.locate(image,'lcnet');localizer_calls+=1
            pixels,inverse,mode,routed=make_view(image,loc,policy,lcnet=lc)
            hsh=raster_hash(pixels)
            if hsh not in memo:memo[hsh]=self.ocr(pixels,reader);ocr_calls+=1
            pred=memo[hsh]['predictions'];feat=features(pred,pixels.shape[:2],image.shape[:2],count,policy,routed)
            return dict(policy=policy,pixels=pixels,predictions=pred,inverse=inverse,mode=mode,features=feat,raster=hsh)
        first=run('completion');selected=first
        settings=locked['selectors'][reader];method=settings['primary_method']
        fallback=cascade_decision(settings['models'][method],first['features'])
        if fallback:selected=run(fallback)
        threshold=locked['review_thresholds'][reader][method]
        predictions=to_source(selected['predictions'],selected['inverse']);fields=semantic(selected['predictions'])
        review=not predictions or selected['features'][6]<threshold
        warnings=[]
        if count<3:warnings.append('Chưa định vị đủ góc giấy tờ; kiểm tra ảnh và thông tin trước khi xác nhận.')
        if selected['features'][11]>.15:warnings.append('Có vùng chữ sát mép ảnh; hãy chụp lại nếu thông tin bị cắt.')
        if review:warnings.append('OCR chưa đủ tin cậy theo ngưỡng thực nghiệm; hãy kiểm tra hoặc chụp lại.')
        return dict(fields=fields,predictions=predictions,selected_policy=selected['policy'],primary_method=method,
            reader=reader,review_recommended=review,warnings=warnings,observed_corners=count,
            actual_wall_seconds=time.perf_counter()-started,actual_cpu_seconds=time.process_time()-cpu,
            ocr_executions=ocr_calls,localizer_calls=localizer_calls,_private_preview=selected['pixels'],
            liveness_evaluated=False,identity_approved=False)
