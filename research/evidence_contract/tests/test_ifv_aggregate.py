"""Integrity/privacy checks on a unit-controlled aggregate-only candidate."""
from copy import deepcopy
import json

import pytest

from research.evidence_contract.master.ifv_analysis import analyze
from research.evidence_contract.paper.verify_ifv_aggregate import checksum,validate_report,verify
from research.evidence_contract.tests.test_ifv_analysis import panel


def test_aggregate_keeps_unknowns_and_does_not_claim_human_replication():
    report,_=analyze(*panel())
    result=validate_report(report)
    assert result['status']=='PASS_AGGREGATE_CONSISTENCY'
    assert result['human_review_reproduced'] is False


def test_aggregate_rejects_changed_counts_and_private_content():
    report,_=analyze(*panel())
    wrong=deepcopy(report)
    wrong['original']['pointwise']['overall']['A']['confusion']['TP']+=1
    with pytest.raises(ValueError,match='Confusion counts'):
        validate_report(wrong)
    report['output_note']='UNIT PRIVATE NOTE'
    with pytest.raises(ValueError,match='Private review content'):
        validate_report(report)


def test_package_hash_guard_rejects_modified_copy(tmp_path):
    report,_=analyze(*panel())
    data=tmp_path/'analysis.json';data.write_text(json.dumps(report),encoding='utf-8')
    (tmp_path/'MANIFEST.json').write_text(json.dumps({'files':{'analysis.json':checksum(data)}}),encoding='utf-8')
    assert verify(tmp_path)['primary']==1
    data.write_text(data.read_text(encoding='utf-8')+' ',encoding='utf-8')
    with pytest.raises(ValueError,match='hash mismatch'):
        verify(tmp_path)
