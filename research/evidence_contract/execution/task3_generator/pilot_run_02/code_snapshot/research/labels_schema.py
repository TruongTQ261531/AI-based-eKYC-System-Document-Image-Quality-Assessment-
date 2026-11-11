"""Keep author text, geometry, actual ink visibility and human legibility distinct."""
import math
import unicodedata
import cv2
import numpy as np

READABILITY=('unassessed','readable','partial','unreadable','not_present','language_unknown','uncertain')

def polygon(value):
    q=np.asarray(value,dtype=np.float64)
    if q.ndim!=2 or q.shape[1]!=2 or len(q)<3 or not np.isfinite(q).all():raise ValueError('Invalid finite polygon')
    if abs(cv2.contourArea(q.astype(np.float32)))<.01:raise ValueError('Degenerate text polygon')
    if not cv2.isContourConvex(q.astype(np.float32)):raise ValueError('Non-convex polygon')
    return q

def in_frame(quad,width,height):
    q=polygon(quad).astype(np.float32)
    frame=np.float32([[0,0],[width,0],[width,height],[0,height]])
    amount,visible=cv2.intersectConvexConvex(q,frame)
    ratio=max(0.,min(1.,float(amount)/abs(cv2.contourArea(q))))
    state='out_of_frame' if ratio<=1e-8 else 'in_frame' if ratio>=1-1e-6 else 'partial_frame'
    return dict(status=state,area_fraction=ratio,clipped_polygon=[] if visible is None else visible.reshape(-1,2).tolist(),
                occlusion='unassessed',basis='geometry_only_not_legibility')

def script_for(text):
    counts={}
    for c in text:
        if not c.isalpha():continue
        name=unicodedata.name(c,'UNKNOWN')
        group=next((s for s in ('LATIN','CYRILLIC','GREEK','ARABIC','HEBREW','THAI','HANGUL','HIRAGANA','KATAKANA','CJK') if s in name),'OTHER')
        counts[group]=counts.get(group,0)+1
    return sorted(counts) or ['NON_ALPHABETIC']

def field(raw_key,text,quad,width,height,*,origin,annotation_ref,semantic_key=None,extra=None):
    if not isinstance(text,str) or not isinstance(raw_key,str) or not raw_key:raise ValueError('Author string and native key required')
    result=dict(raw_key=raw_key,semantic_key=semantic_key,reference_text=text,reference_source='author_or_renderer_not_OCR',
        polygon=polygon(quad).tolist(),coordinate_frame='image_pixels',geometry_origin=origin,
        annotation_ref=annotation_ref,frame_visibility=in_frame(quad,width,height),
        readability=dict(status='unassessed',basis='no_independent_human_review',observed_transcript=None),
        scripts=script_for(text),empty_author_reference=not bool(text.strip()))
    if extra:result.update(extra)
    validate_field(result,width,height)
    return result

def validate_field(value,width,height):
    if not isinstance(value.get('reference_text'),str):raise ValueError('Missing author transcript')
    polygon(value['polygon'])
    if value['readability']['status'] not in READABILITY:raise ValueError('Invalid readability label')
    if value['geometry_origin'] not in ('author_template','author_template_projection','renderer_ink','review_proposal'):
        raise ValueError('Geometry origin must be explicit')
    fraction=value['frame_visibility']['area_fraction']
    if not math.isfinite(fraction) or not 0<=fraction<=1:raise ValueError('Invalid visible fraction')
    # Clean/Blur and OCR agreement are never independent human judgments.
    if value['readability']['status']!='unassessed' and value['readability'].get('basis')!='human_submission':
        raise ValueError('Readability requires an explicit human submission')
    if width<=0 or height<=0:raise ValueError('Invalid image dimensions')

def validate_review(value):
    if not isinstance(value,dict):raise ValueError('Review object required')
    if set(value)-{'reviewer','languages','independent','items','notes'}:raise ValueError('Unexpected review fields')
    reviewer=value.get('reviewer','')
    if not isinstance(reviewer,str) or not 1<=len(reviewer.strip())<=40:raise ValueError('Reviewer code required')
    languages=value.get('languages')
    if not isinstance(languages,list) or not languages or len(languages)>20 or any(not isinstance(s,str) or not 1<=len(s)<=40 for s in languages):
        raise ValueError('Reading languages required')
    if type(value.get('independent')) is not bool:raise ValueError('Independence self-declaration required')
    if not isinstance(value.get('items'),list) or not 1<=len(value['items'])<=100:raise ValueError('Field assessments required')
    seen=set()
    for item in value['items']:
        if set(item)-{'field_id','status','text','polygon'}:raise ValueError('Unexpected field assessment')
        if not isinstance(item.get('field_id'),str) or item['field_id'] in seen:raise ValueError('Duplicate or missing field ID')
        seen.add(item['field_id'])
        if item.get('status') not in READABILITY[1:]:raise ValueError('Assess readability explicitly')
        text=item.get('text','')
        if not isinstance(text,str) or len(text)>2000:raise ValueError('Invalid observed transcription')
        if item['status'] in ('readable','partial') and not text.strip():raise ValueError('Observed transcription required')
        if item['status'] in ('not_present','unreadable','language_unknown') and text.strip():raise ValueError('Do not infer missing text')
        if 'polygon' in item:polygon(item['polygon'])
    if not isinstance(value.get('notes',''),str) or len(value.get('notes',''))>4000:raise ValueError('Notes too long')
    return value
