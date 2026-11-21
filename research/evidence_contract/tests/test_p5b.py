from collections import Counter
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.optimize import brentq
from scipy.stats import t

from research.evidence_contract.oracle_reliability import p5b_simulation as sim
from research.evidence_contract.oracle_reliability import protocol_v3 as v3
from research.evidence_contract.oracle_reliability import protocol_v4_candidate as v4
from research.evidence_contract.oracle_reliability.d4_controls import cases, inputs
from research.evidence_contract.oracle_reliability.mrz_ablation_v1 import compare_pair

ROOT = Path(__file__).resolve().parents[1]
DESIGN = json.loads((ROOT/'execution/master_01/p5b_calibration_20261121/design.json').read_bytes())
BASE = DESIGN['defaults']


def test_transition_audit_matches_engine_both_tiers():
    for tier, expected in [(1,[23,5,31,5,6,2]),(2,[8,2,49,5,6,2])]:
        pairs = Counter()
        for c in cases():
            arms = compare_pair(*inputs(c),minimum_grade=tier)['arms']
            pairs[tuple(arms[k]['pointwise']['state'] for k in v3.ARMS)] += 1
        assert pairs == dict(zip([('FAULT','FAULT'),('NO_FAULT','NO_FAULT'),('UNKNOWN','UNKNOWN'),
                                  ('INVALID_TEST','INVALID_TEST'),('UNKNOWN','FAULT'),('UNKNOWN','NO_FAULT')],expected))


def test_probability_tables_and_missing_truth_bound():
    for name, override in DESIGN['scenarios'].items():
        a = BASE | override
        if a.get('expect_rejection'):
            with pytest.raises(ValueError,match='Infeasible joint'):
                sim.population(a)
            continue
        cells = sim.population(a)
        assert sum(c.probability for c in cells) == pytest.approx(1)
        cov, sens, effect = sim.estimands(cells)
        assert cov == pytest.approx(a['coverage'])
        if not a['truth']:
            assert sens is effect is None
            continue
        assert effect == pytest.approx(a['effect'])
        s = a['sensitivity']
        assert sens == pytest.approx(s/(s+(1-s)*a['miss_multiplier']))
        if a['family'] != 'stress':
            assert all(c.checked == c.asserted or c.checked == sim.U for c in cells)
            known_nonfault = sum(c.probability for c in cells if c.known and not c.fault)
            assert effect * known_nonfault <= 1-cov+1e-12


def test_template_dependence_and_rng_replay():
    a = BASE | dict(template_size=5,template_copy=1,sizes=[1,2,3,4])
    def draw():
        return sim.sample(np.random.default_rng(345),a,sim.population(a),2)
    frame=draw()
    np.testing.assert_array_equal(frame,draw())
    rates=frame/frame[:,:,:1]
    rates=rates.reshape(2,40,5,6)
    np.testing.assert_array_equal(rates,np.broadcast_to(rates[:,:,:1],rates.shape))
    assert not np.array_equal(rates[0],rates[1])


def test_v3_matches_frozen_entrypoint_with_unequal_sizes():
    rows=[]
    counts=[]
    for i in range(65):
        items=[]
        for j in range(1+i%4):
            fault=(i+j)%2==0
            checked=['FAULT','NO_FAULT','UNKNOWN'][(i*3+j+i//4)%3]
            asserted='FAULT' if (i+j)%5==0 else checked
            known=(i+j)%11!=0
            cell=sim.Cell(fault,checked,asserted,known,1)
            items.append(cell.counts())
            rows.append(dict(case_id=f'{i}-{j}',physical_id=f'{i:03}',truth=fault if known else None,
                             checked_v2=checked,mrz_metadata_asserted=asserted))
        counts.append(np.sum(items,axis=0))
    old=v3.analyze(rows)
    new,status=v4.infer(np.array([counts]),'v3')
    assert status[0]=='issued'
    np.testing.assert_array_equal(new[0],list(old['lower95'].values()))


def test_score_against_direct_student_inversion_and_hoeffding_ranges():
    a=BASE | dict(sizes=[1,2,3,4])
    data=sim.sample(np.random.default_rng(19),a,sim.population(a),1)
    bounds,status=v4.infer(data,'cluster_t',True)
    assert status[0]=='issued'
    conservative,status=v4.infer(data,'bounded',True)
    for j,(xi,yi) in enumerate(zip(v4.NUM,v4.DEN)):
        x,y=data[0,:,xi],data[0,:,yi]
        def residual(r):
            z=x-r*y
            return z.sum()-t.ppf(.95,len(x)-1)*np.sqrt(len(x))*z.std(ddof=1)
        root=brentq(residual,-2,x.sum()/y.sum())
        assert bounds[0,j]==pytest.approx(max(0,root))
        penalty=np.sqrt(np.log(20)/2*np.sum(data[0,:,0]**2))
        assert conservative[0,j]==pytest.approx(max(0,(x.sum()-penalty)/y.sum()))


def test_zero_denominators_constant_and_sparse_contrast():
    z=np.tile([4,4,2,2,2,0],(1,60,1))
    for method in sim.METHODS:
        bounds,status=v4.infer(z,method,True)
        if method=='bounded':
            assert status[0]=='issued' and 0 < bounds[0,0] < 1 and bounds[0,2]==0
        else:
            assert 'constant' in status[0] and np.isnan(bounds).all()
        missing=z.copy()
        missing[:,:,2:4]=0
        bounds,status=v4.infer(missing,method,True)
        assert status[0]=='sparse_units' and np.isnan(bounds).all()
    assert v4.passes(np.array([[.8,.8,.05],[.8,.8,.05001]])).tolist()==[[True,True,False],[True,True,True]]


def test_template_capacity_squares_and_small_integer_input():
    # Twenty cases in a template exceed the square range of an int8.
    group=np.tile([20,20,8,8,12,0],(1,40,1)).astype(np.int8)
    bounds,status=v4.infer(group,'bounded',True)
    assert status[0]=='issued'
    assert bounds[0,0]==pytest.approx(1-np.sqrt(np.log(20)/80))
    with pytest.raises(ValueError):
        v4.infer(group,'v3')
