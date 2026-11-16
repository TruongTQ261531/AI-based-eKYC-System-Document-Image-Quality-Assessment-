import pytest

from research.evidence_contract.oracle_reliability import semantic_registry as s
from research.evidence_contract.oracle_reliability.corpus_audit import canonical_id, exposure_state
from research.evidence_contract.oracle_reliability.c2_inventory import eligibility


def test_aliases_do_not_invent_component_mapping():
    assert s.field_for_alias(' SEX ') == 'gender'
    assert s.field_for_alias('birth_date') == 'dob'
    for key in ('name', 'surname', 'number', 'residence_line0', 'mrz_line0'):
        assert s.field_for_alias(key) is None
    assert not s.proposal('id_number')['human_approved']


def test_canonicalization_keeps_identity_and_date_precision():
    assert s.normalize('O01', 'id_number') != s.normalize('001', 'id_number')
    assert s.normalize('ĐẶNG  VĂN', 'full_name') == s.normalize('đặng văn', 'full_name')
    assert s.normalize('1974-08-12', 'dob') != s.normalize('740812', 'dob', source='mrz_td3', precision='date_yymmdd')
    assert s.normalize('000229', 'dob', source='mrz_td3', precision='date_yymmdd') is None
    assert s.normalize('NAME', 'full_name', source='mrz_td3') is None


def test_lineage_numeric_aliases_and_absent_logs_never_certify_unseen():
    assert canonical_id('midv2020/alb_id/1') == canonical_id('midv2020/alb_id/01')
    assert canonical_id('midv2020/alb_id/101') is None
    assert canonical_id('midv500/alb_id/01') is None
    assert exposure_state([]) == 'EXPOSURE_UNKNOWN'
    assert exposure_state(['SYNTHETIC_WITNESS']) == 'EXPOSED_CONFIRMED'


@pytest.mark.parametrize('missing', ['primary_supported_before','primary_removed_after','backup_supported_before',
    'backup_supported_after','semantic_equality_approved','provenance_verified','reference_approved'])
def test_c2_requires_each_distinct_verified_transition(missing):
    fields = ['primary_supported_before','primary_removed_after','backup_supported_before','backup_supported_after',
              'semantic_equality_approved','provenance_verified','reference_approved']
    candidate = dict.fromkeys(fields, True)
    candidate.update(primary_source_id='SYNTHETIC_MAIN', backup_source_id='SYNTHETIC_BACKUP')
    assert eligibility(candidate)['eligible']
    candidate[missing] = None
    assert not eligibility(candidate)['eligible']
    candidate[missing] = 'true'
    assert not eligibility(candidate)['eligible']
    candidate[missing] = True; candidate['backup_source_id'] = candidate['primary_source_id']
    assert not eligibility(candidate)['eligible']
    candidate['backup_source_id'] = None
    assert not eligibility(candidate)['eligible']
