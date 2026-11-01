"""Prepare a blinded human-review packet; never fabricate human annotations."""
import random
import shutil
from research.v3_common import *

PACKET=CACHE/'human_review_v1'
WEB=ROOT/'research/v3_review_web'

def make():
    rows=load('test');selected=[];rng=random.Random(20261103)
    for source in ('authored','midv2020'):
        ids=sorted({r['physical_id'] for r in rows if r['source']==source});rng.shuffle(ids)
        for i,pid in enumerate(ids):
            kind=('full','field_clip','value_mask')[i%3]
            selected.append(next(r for r in rows if r['physical_id']==pid and r['capture']==kind))
    rng.shuffle(selected);items=[];mapping=[]
    for i,row in enumerate(selected,1):
        name=f'case_{i:03}.png';path=PACKET/'images'/name;path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists() and sha(path)!=row['input_sha256']:raise ValueError('Existing blinded packet differs')
        shutil.copyfile(ROOT/row['path'],path)
        items.append(dict(id=f'case_{i:03}',file=name,image_sha256=sha(path)))
        mapping.append(dict(id=f'case_{i:03}',uid=row['uid'],physical_id=row['physical_id'],source=row['source'],capture=row['capture']))
    assert len(items)==48 and len({r['physical_id'] for r in mapping})==48
    spec=dict(version=1,items=items,keys=list(KEYS),contains_reference_values=False,contains_model_outputs=False)
    save(PACKET/'index.json',spec);save(PACKET/'private_mapping.json',mapping)
    save(OUT/'human_review_packet.json',dict(items=48,physical_identities=48,one_view_per_identity=True,
        source_counts={s:sum(r['source']==s for r in mapping) for s in ('authored','midv2020')},
        capture_counts={c:sum(r['capture']==c for r in mapping) for c in ('full','field_clip','value_mask')},
        public_packet_index_sha256=sha(PACKET/'index.json'),model_outputs_included=False,reference_values_included=False,
        actual_human_annotations_received=0,primary_benchmark_references_changed=False,
        purpose='Independent supplementary human review, not model selection or replacement of the preregistered test'))
    print('BLINDED_REVIEW_PACKET_READY',len(items))

if __name__=='__main__':make()
