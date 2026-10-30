"""Secondary conservative geometric visible-substring score on authored cards."""
import cv2
import numpy as np

from research.e2e_eval import eligible
from research.ocr_diagnostic import normalized,edit_distance
from research.support_regions import area,intersection,frame_polygon


def score_visible(sample,predictions):
    targets=[];unscorable=0;frame=frame_polygon(sample['width'],sample['height'])
    for field in sample['fields']:
        truth=normalized(field.get('visible_reference',field['text']))
        polygon=intersection(field['quad'],frame)
        if not eligible(truth) or area(polygon)<=1:unscorable+=1;continue
        targets.append((field,truth,polygon,[]))
    for pred in predictions:
        q=np.asarray(pred['box'],np.float32);size=area(q);choices=[]
        for i,(field,truth,polygon,assigned) in enumerate(targets):
            overlap=area(intersection(q,polygon));coverage=overlap/max(size,1e-8)
            iou=overlap/max(size+area(polygon)-overlap,1e-8)
            if coverage>=.5 and iou>=.01:choices.append((coverage,iou,i))
        if choices:targets[max(choices)[2]][3].append(pred)
    result=[]
    for field,truth,polygon,assigned in targets:
        H=cv2.getPerspectiveTransform(np.float32(field['quad']),np.float32([[0,0],[1000,0],[1000,100],[0,100]]))
        def position(pred):
            center=np.asarray(pred['box'],np.float32).mean(axis=0)
            x,y=cv2.perspectiveTransform(center.reshape(1,1,2),H)[0,0]
            return round(float(y)/40),float(x)
        prediction=normalized(' '.join(p['text'] for p in sorted(assigned,key=position)))
        distance=edit_distance(truth,prediction)
        result.append(dict(field_key=field['key'],reference_length=len(truth),edit_distance=distance,
            exact=distance==0,partial=field['geometric_visibility']<.995,detected=bool(assigned)))
    return dict(fields=result,unscorable_fields=unscorable,
        visibility_measure='Font-advance bounding rectangle proxy, not human legibility')
