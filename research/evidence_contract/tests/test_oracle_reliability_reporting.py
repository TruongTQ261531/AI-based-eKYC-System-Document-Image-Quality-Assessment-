"""Denominator guards: deferral and missing truth are not correct predictions."""
from copy import deepcopy
import json

import pytest

from research.evidence_contract.oracle_reliability.reporting import summarize
from research.evidence_contract.oracle_reliability.verify import recalculate,verify
from research.evidence_contract.oracle_reliability.run import control_rows
from research.evidence_contract.oracle_reliability.reporting import cells_from_rows,report
from research.evidence_contract.task55.data import sha,save_new


def test_risk_excludes_deferrals_but_sensitivity_counts_missed_faults():
    cells=[dict(state=s,truth=t,count=1,reason='unit') for s,t in [
        ('FAULT',True),('FAULT',False),('UNKNOWN',True),('NO_FAULT',False),('FAULT',None)]]
    actual=summarize(cells)
    assert actual==recalculate(cells)
    assert actual['alarm_detection_confusion']==dict(TP=1,FP=1,FN=1,TN=1)
    assert actual['selective_risk']['value']==1/3
    assert actual['decision_coverage_all']['value']==4/5
    assert actual['decision_coverage_labeled']['value']==3/4
    assert actual['sensitivity_all_labeled_faults']['value']==1/2
    assert actual['alarm_accounting']['unresolved']==1
    assert actual['abstained_labeled_faults']==1


def test_no_decisions_is_na_risk_not_zero_error():
    cells=[dict(state='UNKNOWN',truth=t,count=1,reason='no_approval') for t in (True,False,None)]
    actual=summarize(cells)
    assert actual['selective_risk']['value'] is None
    assert actual['sensitivity_all_labeled_faults']['value']==0
    assert actual['decision_coverage_all']['value']==0
    assert summarize([])['selective_risk']['value'] is None


@pytest.mark.parametrize('tamper',['file_hash','report_arithmetic','cells_vs_outputs','duplicate_identity'])
def test_standalone_verifier_rejects_corruption(tmp_path,tamper):
    controls,rows=control_rows();cells=cells_from_rows(rows)
    result=dict(model_calls=0,training_runs=0,confirmatory=False,control_cases=len(controls),results=report(cells))
    if tamper=='report_arithmetic':result['results']['symbolic_controls']['development']['all']['B_tier1']['pointwise']['rows']+=1
    if tamper=='cells_vs_outputs':cells[0]['count']+=1;result['results']=report(cells)
    if tamper=='duplicate_identity':controls[1]['comparison_id']=controls[0]['comparison_id']
    for name,value in [('control_cases.json',controls),('aggregate_cells.json',cells),('results.json',result)]:save_new(tmp_path/name,value)
    save_new(tmp_path/'manifest.json',dict(files={name:sha(tmp_path/name) for name in ('control_cases.json','aggregate_cells.json','results.json')}))
    if tamper=='file_hash':(tmp_path/'results.json').write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError):verify(tmp_path)
