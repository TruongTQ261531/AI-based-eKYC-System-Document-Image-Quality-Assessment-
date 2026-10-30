import numpy as np

from research.recovery_layout_stress import card
from research.recovery_data import load_samples
from research.recovery_audit import repeat_checks


def test_spatial_supplements_keep_annotations_inside_their_actual_card():
    old_ids={s['physical_id'] for s in load_samples()}
    for layout in ('two_column','portrait'):
        image,fields=card(layout,0)
        h,w=image.shape[:2]
        assert (h>w)==(layout=='portrait')
        assert f'extra_specimen/{layout}/00' not in old_ids
        assert len({f['key'] for f in fields})==5
        for field in fields:
            for quad in [field['quad']]+[c['quad'] for c in field['characters']]:
                points=np.asarray(quad)
                assert np.all(points>=0)
                assert np.all(points[:,0]<w) and np.all(points[:,1]<h)
    _,fields=card('two_column',0)
    left=fields[0]['quad'];right=fields[1]['quad']
    assert abs(left[0][1]-right[0][1])<25
    assert right[0][0]>left[0][0]+300


def test_repeat_audit_reports_instability_without_treating_repeats_as_new_ids():
    def item(uid,repeat,prediction,correct):
        return dict(uid=uid,repeat=repeat,method='raw',prediction_sha256=prediction,score={'exact':correct})
    rows=[item('a',1,'x',1),item('a',2,'x',1),item('b',1,'y',0),item('b',2,'z',1)]
    result=repeat_checks(rows)
    assert result['repeated_image_method_groups']==2
    assert result['canonical_prediction_mismatches']==result['score_mismatches']==1
