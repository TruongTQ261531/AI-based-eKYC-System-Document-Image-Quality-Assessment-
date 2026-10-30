import copy

import numpy as np
import pytest

from research.audit_e2e import verify_public_rows,result_key
from research.e2e_analysis import paired_bootstrap


def row(uid,identity,policy,correct,*,repeat=1,stratum='three_corners'):
    return dict(uid=uid,physical_id=identity,repeat=repeat,source='midv500',
                policy=policy,engine='easyocr_en',selection_stratum=stratum,
                timing={'total_wall':1.},score={'fields':[{'exact':value,'cer':1.-value} for value in correct]})


def test_id_bootstrap_does_not_weight_longer_documents_as_more_ids():
    rows=[row('a',1,'raw_fullframe',[0]*10),row('a',1,'three_support',[1]*10),
          row('b',2,'raw_fullframe',[0]),row('b',2,'three_support',[0]),
          row('a',1,'three_support',[0]*10,repeat=2)]
    result=paired_bootstrap(rows,'three_support','easyocr_en','field_exact',{1,2},np.random.default_rng(0))
    assert result['physical_ids']==2
    assert result['mean_paired_delta']==pytest.approx(.5)


def test_mechanism_bootstrap_uses_requested_control_and_stratum():
    rows=[row('a',1,'three_fullframe',[0]),row('a',1,'three_support',[1]),
          row('b',1,'three_fullframe',[1],stratum='four_corner_control'),
          row('b',1,'three_support',[0],stratum='four_corner_control')]
    result=paired_bootstrap(rows,'three_support','easyocr_en','field_exact',{1},np.random.default_rng(0),
                            reference='three_fullframe',stratum='three_corners')
    assert result['mean_paired_delta']==1. and result['ci95']==[1.,1.]


def test_public_audit_rejects_changed_value_and_duplicate_key():
    original=row('a',1,'raw_fullframe',[0]);expected={result_key(original):original}
    verify_public_rows([original],expected)
    changed=copy.deepcopy(original);changed['score']['fields'][0]['exact']=1
    with pytest.raises(ValueError,match='differs'):
        verify_public_rows([changed],expected)
    with pytest.raises(ValueError,match='duplicate'):
        verify_public_rows([original,original],expected)
