"""Candidate content-preserving support regions; no ground truth at inference."""
import math

import cv2
import numpy as np

from ekyc.module2_homography import _localize,order_corners
from ekyc.io import StageError


def frame_polygon(width,height):
    return np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]])


def area(poly):
    return abs(float(cv2.contourArea(np.asarray(poly,np.float32)))) if poly is not None and len(poly)>=3 else 0.


def intersection(first,second):
    if area(first)<1e-8 or area(second)<1e-8:return np.empty((0,2),np.float32)
    _,poly=cv2.intersectConvexConvex(cv2.convexHull(np.asarray(first,np.float32)),cv2.convexHull(np.asarray(second,np.float32)))
    return poly.reshape(-1,2) if poly is not None else np.empty((0,2),np.float32)


def iou(first,second):
    a=area(intersection(first,second));return a/max(area(first)+area(second)-a,1e-12)


def halfplanes(quad):
    q=order_corners(quad).astype(np.float64)
    edges=np.roll(q,-1,axis=0)-q
    normals=np.column_stack((-edges[:,1],edges[:,0]))
    normals/=np.linalg.norm(normals,axis=1,keepdims=True)
    bounds=np.einsum('ij,ij->i',normals,q)
    return normals,bounds


def expand_region(quad,margins,width,height):
    margins=np.asarray(margins,dtype=float)
    if margins.shape!=(4,) or (margins<0).any() or np.isnan(margins).any():raise ValueError('Four nonnegative margins required')
    frame=frame_polygon(width,height)
    if np.isinf(margins).any():return frame
    normals,bounds=halfplanes(quad);bounds-=margins
    poly=frame.astype(float)
    for normal,bound in zip(normals,bounds):
        clipped=[]
        for p,q in zip(poly,np.roll(poly,-1,axis=0)):
            dp,dq=float(p@normal-bound),float(q@normal-bound)
            if dp>=-1e-7:clipped.append(p)
            if (dp>=0)!=(dq>=0):clipped.append(p+(q-p)*(dp/(dp-dq)))
        if len(clipped)<3:return np.empty((0,2),np.float32)
        poly=np.asarray(clipped)
    return np.asarray(poly,np.float32)


def required_margin(quad,targets,scales):
    points=[np.asarray(p,dtype=float) for p in targets if area(p)>1.]
    if not points:return 0.
    scales=np.asarray(scales,dtype=float)
    if scales.shape!=(4,) or not np.isfinite(scales).all() or (scales<=0).any():raise ValueError('Positive scales required')
    normals,bounds=halfplanes(quad)
    distances=bounds[:,None]-normals@np.concatenate(points).T
    return float((np.maximum(distances,0).max(axis=1)/scales).max())


def conformal_quantile(scores,alpha=.10):
    values=np.sort(np.asarray(scores,dtype=float))
    if not 0<alpha<1 or len(values)==0 or np.isnan(values).any():raise ValueError('Invalid calibration data')
    rank=math.ceil((len(values)+1)*(1-alpha))
    return float(values[rank-1]) if rank<=len(values) else float('inf')


def predict(image):
    """Three independent calls. No annotations, labels, identity or cache input."""
    height,width=image.shape[:2];scale=min(1.,960/max(height,width))
    small=cv2.resize(image,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
    enhanced=cv2.cvtColor(cv2.createCLAHE(2.,(8,8)).apply(gray),cv2.COLOR_GRAY2BGR)
    reduced=cv2.resize(cv2.resize(small,None,fx=.75,fy=.75,interpolation=cv2.INTER_AREA),(small.shape[1],small.shape[0]))
    views=[];errors=[]
    ratio=np.array([width/small.shape[1],height/small.shape[0]],dtype=float)
    for view in (small,enhanced,reduced):
        try:
            points,diagnostic=_localize(view)
            views.append((order_corners(points*ratio),diagnostic))
            errors.append(None)
        except StageError:
            views.append(None);errors.append('no_quad')
    valid=[item for item in views if item is not None]
    frame=frame_polygon(width,height)
    if not valid:
        return dict(original=frame.tolist(),base=frame.tolist(),safe_base=frame.tolist(),
                    scales=[1.]*4,detected=False,original_detected=False,consistent=False,valid_views=0,
                    agreement=0.,errors=errors)
    affinities=np.array([[iou(a[0],b[0]) for b in valid] for a in valid])
    medoid=int(np.argmax(affinities.mean(axis=1)));base,diagnostic=valid[medoid]
    pairwise=affinities[np.triu_indices(len(valid),k=1)]
    agreement=float(np.median(pairwise)) if len(pairwise) else 0.
    consistent=len(valid)>=2 and agreement>=.5
    aligned=[]
    for other,_ in valid:
        aligned.append(min((np.roll(other,k,axis=0) for k in range(4)),key=lambda q:np.linalg.norm(q-base,axis=1).mean()))
    normals,_=halfplanes(base)
    size=math.sqrt(max(area(base),1.))
    supports=diagnostic.get('edge_supports',[0.]*4)
    scales=[]
    for edge in range(4):
        shifts=[abs(float((other[j]-base[j])@normals[edge])) for other in aligned for j in (edge,(edge+1)%4)]
        scales.append(max(1.5,.01*size)+float(np.median(shifts))+.03*size*(1-supports[edge]))
    return dict(original=(views[0][0] if views[0] else frame).tolist(),base=base.tolist(),
                safe_base=(base if consistent else frame).tolist(),scales=scales,detected=True,
                original_detected=views[0] is not None,consistent=consistent,valid_views=len(valid),
                agreement=agreement,errors=errors)
