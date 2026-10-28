"""Simple controls that can falsify an exaggerated partial-support claim."""
import gzip
import json
import math
from pathlib import Path

import numpy as np

from ekyc.io import StageError
from ekyc.module2_homography import order_corners
from research.benchmark import digest,save
from research.partial_support import measure
from research.risk_policy import aggregate
from research.support_regions import area,expand_region,frame_polygon


def main():
    samples=[s for s in json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8')) if s['uid'].endswith('_15')]
    for record in json.loads(Path('research/data/midv2020/selection.json').read_text()):
        uid=record['code']+'/'+Path(record['filename']).stem
        samples.append(dict(record,uid='midv2020/'+uid,physical_id=uid,source='midv2020',quality_label='external_photo'))
    predictions={r['uid']:r['prediction'] for r in map(json.loads,Path('research/cache/docaligner/predictions.jsonl').read_text().splitlines())}
    partial=json.loads(Path('research/cache/docaligner/partial_corners.json').read_text())
    rows=[]
    for sample in samples:
        pred=predictions[sample['uid']];points=partial[sample['uid']]['points'] if not pred['detected'] else None
        count=4 if pred['detected'] else sum(p is not None for p in points)
        for method in ('full_frame_three_corner_control','parallelogram_fixed_05','parallelogram_fixed_10'):
            region=pred['original'];detected=pred['detected'];passthrough=False
            if not detected and count==3:
                if method=='full_frame_three_corner_control':passthrough=True
                else:
                    try:
                        missing=points.index(None);completed=list(points)
                        completed[missing]=(np.asarray(points[(missing-1)%4])+np.asarray(points[(missing+1)%4])-np.asarray(points[(missing+2)%4])).tolist()
                        quad=order_corners(completed);fraction=.05 if method.endswith('05') else .10
                        region=expand_region(quad,[fraction*math.sqrt(area(quad))]*4,sample['width'],sample['height']);detected=True
                    except StageError:region=frame_polygon(sample['width'],sample['height'])
            row=measure(sample,region,detected,method,count)
            if passthrough:
                row.update(auto_accept=True,harmful_auto=row['harm'],correct_field_auto=not row['harm'],accepted_utility=row['utility_success'])
            rows.append(row)
    out=Path('research/results/posthoc_controls');summary=[];test=[]
    splits=json.loads(Path('research/results/feasibility_v1/splits.json').read_text())
    for split in splits:
        for method in dict.fromkeys(r['method'] for r in rows):
            subset=[dict(r,seed=split['seed']) for r in rows if r['method']==method and r['source']!='midv2020' and r['physical_id'] in split['test_ids']]
            test.extend(subset);summary.append(dict(seed=split['seed'],method=method,**aggregate(subset)))
    external=[r for r in rows if r['source']=='midv2020']
    save(out/'summary.json',summary);save(out/'external_rows.json',external)
    save(out/'external_summary.json',[dict(method=m,**aggregate([r for r in external if r['method']==m])) for m in dict.fromkeys(r['method'] for r in rows)])
    with (out/'per_image.jsonl.gz').open('wb') as target,gzip.GzipFile(fileobj=target,mode='wb',mtime=0,filename='') as stream:
        for row in test:stream.write((json.dumps(row)+'\n').encode())
    save(out/'run.json',dict(protocol_sha256=digest('research/POSTHOC_CONTROLS.md'),code_sha256=digest(__file__),
        timing='Post-hoc after v3; not confirmatory',new_neural_calls=0,training_runs=0,primary_images=700,external_images=20))
    print('CONTROLS_COMPLETE')


if __name__=='__main__':main()
