"""Post-review diagnostic controls. No actual human observations are created."""
from copy import deepcopy

import pytest

from research.evidence_contract.master import ifv_analysis as audit
from research.evidence_contract.master.ifv_report import METHODS
from research.evidence_contract.tests.test_task55_ifv import phase2


def test_literal_flags_do_not_collapse_letter_o_into_zero():
    case,item=phase2()
    case['before_evidence']['observed_transcript']='DEMO12345'
    case['before_output']['value']='DEM012345'
    assert 'before_correct_disagrees_with_phase1_transcript' in audit.coherence_flags(case,item)
    case['before_output']['value']='  demo12345  '
    assert not audit.coherence_flags(case,item)
    assert audit.literal_text('NGUYE\u0302\u0303N')==audit.literal_text('NGUYỄN')


def test_omission_flag_retains_original_judgment_and_guard_result():
    case,item=phase2()
    item['after_reading']='readable_omission'
    original=deepcopy(item)
    assert audit.coherence_flags(case,item)==['after_nonempty_output_marked_omission']
    assert audit.ifv.labels_for(case,item)==('INCONCLUSIVE','INCONCLUSIVE')
    assert item==original


def test_c2_and_original_error_have_different_inconclusive_explanations():
    case,item=phase2('C2')
    assert audit.gate_reasons(case,item)=={
        'pointwise':['backup_source_not_verified'], 'relation':['backup_source_not_verified']}
    case,item=phase2('C3')
    item['before_reading']='wrong_value'
    result=audit.gate_reasons(case,item)
    assert result['pointwise']==[]
    assert result['relation']==['original_reading_not_correct']


def test_unusable_structure_does_not_trigger_literal_text_comparison():
    case,item=phase2()
    case['after_output']['structured_output_usable']=False
    item['after_reading']='readable_omission'
    assert not audit.coherence_flags(case,item)
    assert audit.gate_reasons(case,item)['pointwise']==['followup_structure_unusable']


def links_for(cases):
    return {case['case_id']:dict(row=dict(stratum='primary',contract_id=case['contract'],
        physical_id_sha256='one-fixture-id',checks={m:dict(alarm=True,verdict='CANDIDATE_VIOLATION') for m in METHODS}))
        for case in cases}


def test_all_alarm_accounting_keeps_unknowns_outside_conditional_precision():
    cases=[]
    for i in range(3):
        case,_=phase2();case['case_id']='unit-'+str(i);cases.append(case)
    labels={'unit-0':dict(pointwise='CONFIRMED_FAULT'),
            'unit-1':dict(pointwise='INCONCLUSIVE')}
    result=audit.alarm_accounting(links_for(cases),labels,'pointwise','A')
    assert result['total_alarms']==3 and result['unresolved_alarms']==2
    assert result['conditional_precision']['value']==1
    assert result['verified_fault_fraction_of_all_alarms']['value']==1/3
    assert result['status_counts']['UNREVIEWED']==1


def panel():
    case,item=phase2()
    case['before_output']['value']='DIFFERENT_FROM_PHASE1'
    packet=dict(cases=[case],phase1_snapshot='unit-snapshot',packet_id='unit-packet')
    export=dict(mode='unit_injected',items=[item])
    labels={case['case_id']:dict(pointwise='CONFIRMED_FAULT',relation='CONFIRMED_FAULT')}
    return packet,export,links_for([case]),labels


def test_sensitivity_does_not_modify_labels_or_drop_selected_cases():
    packet,export,links,labels=panel()
    original=deepcopy((packet,export,links,labels))
    result,details=audit.analyze(packet,export,links,labels)
    assert (packet,export,links,labels)==original
    assert result['original']['pointwise']['overall']['A']['confusion']['TP']==1
    sensitivity=result['sensitivity']['results']['pointwise']
    assert sensitivity['primary_cases']==1
    assert sensitivity['overall']['A']['status']=={'INCONCLUSIVE':1}
    assert result['human_answers_changed']==0 and len(details)==1
    assert result['method_agreement']['A_vs_flat']==1
    text=audit.markdown(result)
    assert 'hậu kiểm' in text and 'không thay bảng chính' in text


def test_diagnostic_rejects_relabeling_and_incomplete_frame():
    packet,export,links,labels=panel()
    with pytest.raises(ValueError,match='entire sealed'):
        audit.analyze(packet,dict(export,items=[]),links,labels)
    labels['CASE-unit']['relation']='NO_FAULT'
    with pytest.raises(ValueError,match='relabeled'):
        audit.analyze(packet,export,links,labels)


def test_postreview_entry_rejects_unsealed_submission(tmp_path):
    with pytest.raises(ValueError,match='sealed copy'):
        audit.from_sealed(tmp_path/'observations.json')
