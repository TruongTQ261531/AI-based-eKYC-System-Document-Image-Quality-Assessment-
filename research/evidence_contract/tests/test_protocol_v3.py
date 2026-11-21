import pytest

from research.evidence_contract.oracle_reliability.protocol_v3 import analyze


def case(key, cluster, truth, checked, asserted):
    return dict(case_id=str(key), physical_id=str(cluster), truth=truth,
                checked_v2=checked, mrz_metadata_asserted=asserted)


def test_deferral_missingness_and_small_clusters():
    rows = [case(1,1,True,'UNKNOWN','FAULT'), case(2,1,False,'NO_FAULT','FAULT'),
            case(3,2,None,'INVALID_TEST','NO_FAULT'), case(4,2,True,'FAULT','FAULT')]
    result = analyze(rows)
    assert list(result['estimates'].values()) == [.5, .5, 1.]
    assert result['missing_truth'] == 1 and result['lower95'] is None
    assert result['by_arm']['checked_v2']['base']['FAR_all_labeled_nonfaults']['value'] == 0
    assert result['by_arm']['mrz_metadata_asserted']['base']['FAR_all_labeled_nonfaults']['value'] == 1
    assert result['missing_truth_bounds']['checked_sensitivity']['minimum'] == 1/3
    assert result['missing_truth_bounds']['paired_far_difference']['minimum'] == .5
    assert analyze([])['estimates']['asserted_minus_checked_far'] is None
    with pytest.raises(ValueError):
        analyze(rows + rows)


def test_cluster_replay_and_scope():
    rows = [case(2*i, i, False, 'UNKNOWN' if i % 4 == 0 else 'NO_FAULT', 'FAULT' if i % 3 else 'NO_FAULT')
            for i in range(40)]
    rows += [case(2*i+1, i, True, 'UNKNOWN' if i % 4 == 0 else 'FAULT', 'FAULT') for i in range(40)]
    result = analyze(rows)
    assert result == analyze(reversed(rows))
    assert result['status'] == 'DESIGN_CRITERIA_UNMET'
    assert result['physical_ids'] == 40 and result['lower95']['checked_all_fault_sensitivity'] < .80
