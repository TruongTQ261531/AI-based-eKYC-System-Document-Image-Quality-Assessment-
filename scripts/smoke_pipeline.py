"""Find a usable real capture, exercise all document stages, then reject photo replay."""
import csv
import random
import torch
from ekyc.config import ROOT, Settings
from ekyc.pipeline import EKYCPipeline
from ekyc.module2_homography import Homography
from ekyc.io import StageError, read_image, write_json

torch.set_num_threads(4)
pipeline = EKYCPipeline()
rows = [r for r in csv.DictReader((ROOT/'data/manifest.csv').open(encoding='utf-8-sig'))
        if r['original_document']=='04_aut_id' and r['label']=='Clean']
random.Random(42).shuffle(rows)
attempts = []
for row in rows[:30]:
    path=ROOT/row['relative_path']
    image=read_image(path)
    q=pipeline.quality.run(image)
    if not q['passed']:
        continue
    try:
        card, geo=Homography().run(image)
        pipeline.faces.extract(card)
    except StageError as error:
        attempts.append(dict(path=row['relative_path'],reason=str(error)))
        continue
    result=pipeline.run(path, ROOT/'outputs/smoke/static_photo.avi')
    write_json(ROOT/'outputs/smoke/pipeline_smoke_report.json', dict(input=row,attempts=attempts,result=result))
    print(result['decision'], result.get('reason'), list(result['stages']), result['run_id'],flush=True)
    break
else:
    write_json(ROOT/'outputs/smoke/pipeline_smoke_report.json',dict(attempts=attempts))
    raise RuntimeError('No usable card in the smoke sample')
