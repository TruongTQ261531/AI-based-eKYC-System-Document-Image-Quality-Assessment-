import pytest

from research.evidence_contract.oracle_reliability import c2_evidence_audit as audit
from research.evidence_contract.oracle_reliability import policy, semantic_registry, mrz_ablation_v1


def test_synthetic_transition_matrix():
    facts=dict.fromkeys(audit.CONDITIONS,'PASS')
    assert audit.classify('main','backup',facts)[1]
    assert audit.classify('same','same',facts)[0]['distinct_sources']=='FAIL'
    assert audit.classify('main','',facts)[0]['distinct_sources']=='UNKNOWN'
    for condition in facts:
        for state in ('FAIL','UNKNOWN'):
            result,eligible=audit.classify('main','backup',dict(facts,**{condition:state}))
            assert result[condition]==state and not eligible
    facts.pop('primary_removed_after')
    with pytest.raises(ValueError):
        audit.classify('main','backup',facts)


def test_after_removal_independent_of_approval_flags():
    row=dict(candidate_id='synthetic',primary_source_id='main',backup_source_id='backup',
             physical_instance='id', mechanical_comparison='LITERAL_EQUAL_NOT_APPROVED',
             reference_approved=True,semantic_equality_approved=True,backup_supported_after=True)
    result=audit.assess(row,{'id'},{'id'})
    assert result['followup_group']=='image_and_parent_link'
    assert result['conditions']['backup_supported_after']=='UNKNOWN'
    assert result['conditions']['semantic_equality_approved']=='UNKNOWN'
    assert result['conditions']['reference_approved']=='FAIL' and not result['eligible']
    assert not audit.reference_registry.approved_ids()


def test_literal_evidence_limits():
    mrz={'line1':'P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<',
         'line2':'L898902C37UTO7408122F1204159ZE184226B<<<<<10'}
    assert policy.td3_value(mrz,'id_number','identifier')[1]=='mrz_checksum_failed'
    assert policy.td3_value(mrz,'dob','date_iso')[0] is None
    assert semantic_registry.field_for_alias('name') is None
    mrz_ablation_v1.verify_frozen_source()
