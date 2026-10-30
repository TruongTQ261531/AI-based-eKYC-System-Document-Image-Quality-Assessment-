import copy
from pathlib import Path

import numpy as np
import pytest

from research.recovery_data import capture,mark_visibility,render_card
from research.recovery_runtime import RecoveryEngine,features,POLICIES
from research.recovery_selection import fit_regressor,predict,cascade_decision,combined_cost
from research.recovery_study import process_lock,panel,semantic_score


def test_partial_capture_marks_lost_content_without_modifying_truth():
    image,fields,_,_=render_card(0,0);original=copy.deepcopy(fields)
    pixels,out,gt,_=capture(image,fields,[[0,0],[999,0],[999,639],[0,639]],'specimen/test','field_clip')
    sample=mark_visibility(dict(fields=out,gt=gt,width=pixels.shape[1],height=pixels.shape[0]))
    field=next(f for f in sample['fields'] if f['key']=='full_name')
    assert field['geometric_visibility']<.995
    assert field['visible_reference']!=field['text']
    assert fields==original


def test_numeric_regressors_roundtrip_and_learn_different_structures():
    x=np.array([[1.,v] for v in np.linspace(-1,1,30)]);y=np.array([v[1]>.2 for v in x],float)
    for kind,strength in [('ridge',.1),('stumps',24)]:
        model=fit_regressor(x,y,kind,strength)
        assert np.isfinite(predict(model,x)).all()
        assert predict(model,[1.,.8])>predict(model,[1.,-.8])


def test_cascade_uses_completion_features_and_never_test_targets():
    model=dict(regressor={'kind':'stumps','base':.25,'stumps':[]},
               expected_fallback_wall={'raw':0.,'bbox':500.,'contour':500.,'lcnet':500.})
    assert cascade_decision(model,[1.,.5])=='raw'
    model['regressor']['base']=0.
    assert cascade_decision(model,[1.,.5]) is None


def test_online_cascade_executes_at_most_two_ocr_calls(monkeypatch):
    import research.recovery_runtime as runtime
    engine=object.__new__(RecoveryEngine);calls=[]
    engine.locate=lambda image,key='fastvit':dict(points=[[1,1],[18,1],[18,8],[1,8]],quad=[[1,1],[18,1],[18,8],[1,8]])
    def ocr(image,reader):
        calls.append(1)
        return dict(predictions=[dict(box=[[1,1],[17,1],[17,8],[1,8]],text='Full name: TEST',confidence=.9)],wall=.01,cpu=.01)
    engine.ocr=ocr
    monkeypatch.setattr(runtime,'make_view',lambda image,loc,policy,**kw:(np.full((10,20,3),10 if policy=='completion' else 20,np.uint8),np.eye(3),policy,True))
    reg=dict(regressor={'kind':'stumps','base':.3,'stumps':[]},expected_fallback_wall={'raw':0.,'bbox':500.,'contour':500.,'lcnet':500.})
    locked={'selectors':{'rapid_latin_v5':{'primary_method':'cascade_stumps','models':{'cascade_stumps':reg}}},
            'review_thresholds':{'rapid_latin_v5':{'cascade_stumps':.5}}}
    result=engine.online(np.zeros((10,20,3),np.uint8),locked)
    assert len(calls)==result['ocr_executions']==2
    assert result['selected_policy']=='raw' and not result['identity_approved']


def test_process_lock_rejects_concurrent_owner_and_releases(tmp_path):
    path=tmp_path/'process.lock'
    with process_lock(path):
        with pytest.raises(RuntimeError,match='owns'):
            with process_lock(path):pass
    with process_lock(path):pass


def test_semantic_score_uses_keys_without_oracle_spatial_assignment():
    s=dict(width=200,height=100,fields=[dict(key='full_name',text='TEST PERSON',quad=[[10,10],[190,10],[190,40],[10,40]])])
    assert semantic_score(s,{'full_name':'TEST PERSON'})['exact']==1
    assert semantic_score(s,{'wrong_key':'TEST PERSON'})['exact']==0


def test_cost_counts_shared_ocr_once_and_separate_localizers():
    def row(policy,hsh):return dict(policy=policy,raster_sha256=hsh,ocr_wall=2.,transform_wall=.1,
        semantic_map_wall=.1,localize_wall=.3,probe_wall=0.)
    rows={'completion':row('completion','same'),'bbox':row('bbox','same'),'lcnet':row('lcnet','new')}
    assert combined_cost(rows,('completion','bbox','lcnet'))==pytest.approx(5.2)


def test_native_decoder_preserves_upstream_equal_peak_ambiguity():
    from research.recovery_upstream import decode_native
    heat=np.zeros((1,4,32,32),np.float32)
    heat[:,:,3:8,3:8]=1.;heat[:,0,20:25,20:25]=1.
    result=decode_native(heat,32,32)
    assert result[0] is None
    assert all(p is not None for p in result[1:])
