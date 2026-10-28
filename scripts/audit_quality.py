"""Compare quality policies on a fixed diagnostic sample, not a benchmark."""
import csv
import json
import random
from collections import Counter

import cv2
import numpy as np
import torch

from ekyc.config import ROOT, Settings
from ekyc.io import read_image, write_json
from ekyc.module1_quality import QualityAssessment


def main():
    torch.set_num_threads(4)
    rows=list(csv.DictReader((ROOT/'data/manifest.csv').open(encoding='utf-8-sig')))
    rng=random.Random(2026)
    selected=[]
    for label in ('Clean','Blur','Cropped','Dark','Distorted'):
        selected += rng.sample([r for r in rows if r['label']==label and r['split']=='val' and r['is_reference']=='0'],20)
    selected += [r for r in rows if r['is_reference']=='1']
    model=QualityAssessment(Settings().quality_model)
    records=[]
    for i,row in enumerate(selected,1):
        image=read_image(ROOT/row['relative_path'])
        result=model.run(image)
        gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        scale=min(1,960/max(gray.shape))
        gray=cv2.resize(gray,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
        records.append(dict(image=row['image_name'],label=row['label'],reference=row['is_reference']=='1',
            predicted=result['label'],clean=result['clean_confidence'],max_score=max(result['probabilities'].values()),
            old_pass=result['label']=='Clean' and result['clean_confidence']>=.6,new_pass=result['passed'],
            reason=result['reason'],mean=float(gray.mean()),p90=float(np.percentile(gray,90)),
            sharpness=float(cv2.Laplacian(gray,cv2.CV_64F).var())))
        if i%25==0: print(f'{i}/{len(selected)}',flush=True)
    summary={}
    for key,population in [('labeled_clean',[r for r in records if r['label']=='Clean' and not r['reference']]),
                           ('extra_clean',[r for r in records if r['reference']]),
                           ('labeled_defects',[r for r in records if r['label']!='Clean'])]:
        summary[key]=dict(count=len(population),old_pass=sum(r['old_pass'] for r in population),
                         new_pass=sum(r['new_pass'] for r in population),predictions=dict(Counter(r['predicted'] for r in population)))
    write_json(ROOT/'outputs/quality_audit.json',dict(summary=summary,records=records,
        note='Diagnostic sample only; existing checkpoint training overlap unknown. Passing Module 1 is not accepting a card.'))
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__': main()
