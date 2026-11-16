from copy import deepcopy
import json
import pytest

from research.evidence_contract.oracle_reliability import reporting_v2 as r
from research.evidence_contract.oracle_reliability.verify_reporting_v2 import verify
from research.evidence_contract.reviewer_tools.strict import sha_bytes


def cell(state,truth,count=1):
    return dict(dataset='SYNTHETIC',partition='development',contract='C2',cluster='symbolic',
        method='SYNTHETIC',endpoint='pointwise',state=state,truth=truth,count=count,reason='SYNTHETIC')


@pytest.mark.parametrize('cells', [[],[cell('UNKNOWN',True,2)], [cell('INVALID_TEST',None,3)],
    [cell('FAULT',True,4)], [cell('NO_FAULT',False,3)],
    [cell('STRUCTURAL_ERROR',True),cell('FAULT',None),cell('UNKNOWN',False),cell('NO_FAULT',True)]])
def test_zero_denominator_and_partial_truth_accounting(cells):
    result=r.summarize(cells);base=result['base'];rates=result['rates']
    for rate in list(rates.values())+[base[k] for k in ('decision_coverage_all','decision_coverage_labeled',
        'sensitivity_all_labeled_faults','FAR_all_labeled_nonfaults','selective_risk')]:
        if rate['denominator']==0:assert rate['value'] is None
    assert rates['combined_deferral']['numerator']+base['decision_coverage_all']['numerator']==base['rows']
    assert result['unresolved_truth_rows']==sum(c['count'] for c in cells if c['truth'] is None)


def test_abstention_is_non_alarm_but_never_correct_decision():
    result=r.summarize([cell('UNKNOWN',False),cell('UNKNOWN',True),cell('INVALID_TEST',False)])
    assert result['base']['alarm_detection_confusion']==dict(TP=0,FP=0,FN=1,TN=2)
    assert result['base']['selective_risk']['value'] is None
    assert result['rates']['abstention_unknown']['value']==2/3
    assert result['rates']['invalid_test']['value']==1/3


@pytest.mark.parametrize('bad',[dict(count=True),dict(count=0),dict(count=-1),dict(truth=1),dict(truth='false'),dict(state='OK')])
def test_bad_cells_rejected(bad):
    value=cell('UNKNOWN',None);value.update(bad)
    with pytest.raises(ValueError):r.summarize([value])


def test_independent_verifier_detects_metric_tampering(tmp_path):
    cells=[cell('UNKNOWN',True),cell('NO_FAULT',False),cell('FAULT',None)];raw=json.dumps(cells).encode()
    source=tmp_path/'cells.json';source.write_bytes(raw);target=tmp_path/'report.json'
    result=dict(input_sha256=sha_bytes(raw),source_cells=3,metric_groups=3,groups=r.report(cells),
        confirmatory=False,new_observations=0,model_calls=0,training_runs=0,labels_changed=0)
    target.write_text(json.dumps(result));assert verify(source,target)['status']=='PASS'
    broken=deepcopy(result);broken['groups'][0]['metrics']['base']['selective_risk']['value']=0.7
    target.write_text(json.dumps(broken))
    with pytest.raises(ValueError,match='Accounting'):verify(source,target)
