"""GT is restricted to this post-inference spatial transcription evaluator."""
import math
import unicodedata

import cv2
import numpy as np

from research.ocr_diagnostic import normalized,edit_distance
from research.support_regions import area,intersection,frame_polygon


def eligible(value):
    value=normalized(value)
    return (1<=len(value)<=128 and any(c.isalnum() for c in value) and
            all(not c.isalpha() or 'LATIN' in unicodedata.name(c,'') for c in value))


def target_fields(sample):
    frame=frame_polygon(sample['width'],sample['height']);targets=[];counts=dict(partial=0,non_latin_or_invalid=0)
    for field in sample['fields']:
        if not eligible(field['text']) or area(field['quad'])<=1:
            counts['non_latin_or_invalid']+=1;continue
        if area(intersection(field['quad'],frame))/area(field['quad'])<.995:
            counts['partial']+=1;continue
        targets.append(field)
    return targets,counts


def score(sample,predictions,routed):
    targets,excluded=target_fields(sample)
    assignments=[[] for _ in targets];unassigned=0
    for pred in predictions:
        quad=np.asarray(pred['box'],np.float32);a=area(quad)
        choices=[]
        for index,field in enumerate(targets):
            overlap=area(intersection(quad,field['quad']))
            coverage=overlap/max(a,1e-8);iou=overlap/max(a+area(field['quad'])-overlap,1e-8)
            if coverage>=.5 and iou>=.01:choices.append((coverage,iou,index))
        if choices:assignments[max(choices)[2]].append(pred)
        else:unassigned+=1
    rows=[]
    for field,items in zip(targets,assignments):
        # Evaluation-only reading order. These corners never enter OCR inference.
        transform=cv2.getPerspectiveTransform(np.float32(field['quad']),np.float32([[0,0],[1000,0],[1000,100],[0,100]]))
        def position(pred):
            center=np.asarray(pred['box'],np.float32).mean(axis=0)
            x,y=cv2.perspectiveTransform(center.reshape(1,1,2),transform)[0,0]
            return (round(float(y)/40),float(x))
        text=normalized(' '.join(item['text'] for item in sorted(items,key=position))) if routed else ''
        truth=normalized(field['text']);distance=edit_distance(truth,text)
        rows.append(dict(field_key=field['key'],truth_length=len(truth),prediction_length=len(text),
            edit_distance=distance,cer=distance/len(truth),exact=distance==0,
            detected=bool(items) and routed,digits_only=truth.isdigit()))
    confident=[float(p['confidence']) for p in predictions if normalized(p['text'])]
    visible_corners=sum(0<=x<sample['width'] and 0<=y<sample['height'] for x,y in sample['gt'])
    return dict(fields=rows,eligible_fields=len(rows),excluded_fields=excluded,
        unassigned_predictions=unassigned,all_targets_exact=bool(rows) and all(r['exact'] for r in rows),
        median_confidence=float(np.median(confident)) if confident else 0.,
        any_text=bool(confident),gt_visible_corners=int(visible_corners))


def aggregate(rows):
    fields=[field for row in rows for field in row['score']['fields']]
    routed=[r for r in rows if r['routed']];routed_fields=[f for r in routed for f in r['score']['fields']]
    digits=[f for f in fields if f['digits_only']]
    def mean(values):return float(np.mean(values)) if len(values) else None
    def micro(values):return sum(f['edit_distance'] for f in values)/sum(f['truth_length'] for f in values) if values else None
    return dict(images=len(rows),eligible_fields=len(fields),field_exact=mean([f['exact'] for f in fields]),
        macro_cer=mean([f['cer'] for f in fields]),micro_cer=micro(fields),
        detection_coverage=mean([f['detected'] for f in fields]),digit_field_exact=mean([f['exact'] for f in digits]),
        routed_fraction=len(routed)/len(rows),conditional_field_exact=mean([f['exact'] for f in routed_fields]),
        geometry_review_fraction=mean([not r['routed'] for r in rows]),
        no_text_fraction=mean([r['routed'] and not r['score']['any_text'] for r in rows]),
        all_targets_exact_fraction=mean([r['score']['all_targets_exact'] for r in rows if r['score']['eligible_fields']]),
        no_evaluable_target_images=sum(not r['score']['eligible_fields'] for r in rows),
        mean_wall_seconds=mean([r['timing']['total_wall'] for r in rows]),
        median_wall_seconds=float(np.median([r['timing']['total_wall'] for r in rows])),
        p95_wall_seconds=float(np.quantile([r['timing']['total_wall'] for r in rows],.95)),
        mean_cpu_seconds=mean([r['timing']['total_cpu'] for r in rows]),
        unassigned_predictions=sum(r['score']['unassigned_predictions'] for r in rows))
