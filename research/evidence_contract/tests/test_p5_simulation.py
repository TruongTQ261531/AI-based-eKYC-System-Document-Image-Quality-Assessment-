from dataclasses import replace
import random

import numpy as np
import pytest

from research.evidence_contract.oracle_reliability import p5_simulation as sim
from research.evidence_contract.oracle_reliability import protocol_v3 as v3


BASE = sim.Assumptions(200, 4, .2, .9, .2, .07, .91, .2, 1.)


def test_seed_and_dependence_preserve_marginals():
    def sample(rho):
        return sim.sample_ids(np.random.default_rng(47), replace(BASE, icc=rho), .10, 600)
    iid, copied = sample(0), sample(1)
    np.testing.assert_array_equal(iid, sample(0))
    assert np.all(copied % 4 == 0)
    assert copied[:,:,1].var() / iid[:,:,1].var() == pytest.approx(4, rel=.04)
    for a in (iid,copied):
        totals = a.sum(axis=(0,1))
        expected = BASE.targets(.1)
        np.testing.assert_allclose((totals[0]/(600*800),totals[2]/totals[1],totals[4]/totals[3]),
                                   expected, atol=.005)


def test_missing_truth_and_invalid_inputs():
    a = replace(BASE, truth_availability=0)
    result = sim.operating_point(a,.1,10,7,'example')
    assert result['short_clusters'] == 10 and result['insufficient']['rate'] == 1
    assert result['bootstrap_draws'] == 0 and result['issued'] == 0
    assert all(x['rate'] is None for x in result['coverage_if_issued'].values())
    with pytest.raises(ValueError):
        sim.sample_ids(np.random.default_rng(1),BASE,.25,1)
    with pytest.raises(ValueError):
        sim.sample_ids(np.random.default_rng(1),replace(BASE,abstention=.99),.1,1)
    mnar = replace(BASE, miss_truth_multiplier=.35)
    inputs = sim.sample_ids(np.random.default_rng(21),mnar,.10,300)
    totals = inputs.sum(axis=(0,1))
    assert totals[2]/totals[1] == pytest.approx(mnar.targets(.1)[1],abs=.003)


def test_batched_bootstrap_matches_unmodified_v3_on_same_frame():
    rng = random.Random(975)
    rows = []
    vectors = []
    for i in range(50):
        vector = np.zeros(5, dtype=int)
        for j in range(4):
            truth = (True,False,None,False)[j]
            checked = rng.choice(['FAULT','NO_FAULT','UNKNOWN','INVALID_TEST'])
            asserted = rng.choice(['FAULT','NO_FAULT'])
            rows.append(dict(physical_id=f'id{i:03}',case_id=f'{i}_{j}',truth=truth,
                             checked_v2=checked,mrz_metadata_asserted=asserted))
            vector += (checked in ('FAULT','NO_FAULT'),truth is True,truth is True and checked=='FAULT',
                       truth is False, (int(asserted=='FAULT')-int(checked=='FAULT')) if truth is False else 0)
        vectors.append(vector)
    lower, constant, bad = sim.bootstrap(np.array([vectors]),4)
    actual = v3.analyze(rows)
    np.testing.assert_array_equal(lower[0],list(actual['lower95'].values()))
    assert not constant.any() and not bad.any()


def test_full_coverage_guard_and_undefined_draws():
    full = sim.operating_point(replace(BASE, abstention=0),.18,8,49,'full')
    assert full['degenerate_by_metric']['decision_coverage'] == 8
    assert full['issued'] == full['joint_pass']['k'] == 0
    assert full['pass_if_only_coverage_degeneracy_waived']['k'] > 0
    v = np.zeros((1,50,5),dtype=int)
    v[:,:,0] = 4
    v[:,:,3] = 4
    v[:,0,1:3] = 1
    v[:,0,3] = 3
    _, _, bad = sim.bootstrap(v,4)
    assert 0 < bad[0] < v3.REPLICATES


def test_null_boundary_and_regression_seed():
    # Exact equality at 5pp fails v3; data availability can shift the sensitivity target.
    points = list(sim.profile_grid(replace(BASE, miss_truth_multiplier=.35),{'effects':[.1]}))
    assert points[0][2] == v3.FAR_MARGIN
    for label,a,e in points[1:3]:
        assert min(a.targets(e)[0:2]) == pytest.approx(.7999)
    a = replace(BASE, ids=40, cases=2)
    assert sim.operating_point(a,.1,7,221,'test') == sim.operating_point(a,.1,7,221,'test')
