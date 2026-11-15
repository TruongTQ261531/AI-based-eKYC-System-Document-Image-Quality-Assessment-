"""Known contingency controls; no synthetic exports become human evidence."""
from copy import deepcopy

import pytest

from research.evidence_contract.task55.agreement import nominal,compare
from research.evidence_contract.tests.test_task55_ifv import phase1


def test_two_coder_known_contingency():
    result=nominal([['a','a'],['a','b'],['b','b'],['b','b']])
    assert result['exact_pairwise_agreement']==.75
    assert result['cohen_kappa']==.5
    assert result['nominal_krippendorff_alpha']==pytest.approx(8/15)


def test_missing_ratings_and_constant_labels_are_not_fabricated_as_reliability():
    result=nominal([['a','a'],['b',None],['b','b']])
    assert result['units_with_multiple_ratings']==2
    assert result['nominal_krippendorff_alpha']==1
    constant=nominal([['a','a'],['a','a']])
    assert constant['exact_pairwise_agreement']==1
    assert constant['cohen_kappa'] is None and constant['nominal_krippendorff_alpha'] is None


def test_duplicate_person_versions_and_single_export_are_not_multiple_raters():
    packet,value=phase1()
    with pytest.raises(ValueError,match='At least two'):compare([value],packet,allow_unit=True)
    with pytest.raises(ValueError,match='one reviewer'):compare([value,deepcopy(value)],packet,allow_unit=True)
    second=deepcopy(value);second['reviewer']['reviewer_id']='other-unit'
    report=compare([value,second],packet,allow_unit=True)
    assert report['declared_reviewer_count']==2
    assert report['distinct_people_independently_verified'] is False
    assert report['independent_gold_created'] is False
    with pytest.raises(ValueError,match='Synthetic'):compare([value,second],packet)
