from copy import deepcopy
import pytest

from research.evidence_contract.execution.master_01.reviewer_intake_20261117_r02_phase2.audit_public import verify_table,verify_method


def balanced_table():
    # Independent, hand-calculated 2x2 example: observed=.75, expected=.5, kappa=.5.
    return dict(compared=8,matched=6,disagreed=2,exact_agreement=.75,cohen_kappa=.5,
        kappa_unavailable_reason=None,contingencies=[
            dict(first=a,second=b,count=n) for a,b,n in [('yes','yes',3),('yes','no',1),('no','yes',1),('no','no',3)]])


def test_public_contingency_recalculation_has_hand_calculated_result():
    value=balanced_table();before=deepcopy(value)
    assert sum(verify_table(value).values())==8 and value==before


@pytest.mark.parametrize('key,value',[('matched',7),('compared',9),('cohen_kappa',.8),('exact_agreement',1)])
def test_public_audit_rejects_tampered_agreement(key,value):
    record=balanced_table();record[key]=value
    with pytest.raises(ValueError):verify_table(record)


def test_public_audit_rejects_duplicate_cells():
    record=balanced_table();record['contingencies'].append(deepcopy(record['contingencies'][0]))
    with pytest.raises(ValueError):verify_table(record)


def test_public_audit_rejects_confusion_incompatible_with_label_counts():
    record=dict(confusion=dict(TP=2,FP=0,FN=1,TN=3),status=dict(CONFIRMED_FAULT=2,NO_FAULT=3),
        alarms_by_status=dict(CONFIRMED_FAULT=2),labeled_cases=6)
    with pytest.raises(ValueError):verify_method(record)
