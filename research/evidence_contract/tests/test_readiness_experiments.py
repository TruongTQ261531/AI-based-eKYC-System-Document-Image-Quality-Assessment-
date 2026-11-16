"""Integrity checks for actual-program evidence, not tests of frozen A changes."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from research.evidence_contract.master import parser_faults as parser
from research.evidence_contract.master import readiness_verify as replay
from research.evidence_contract.master import representation_audit as representation
from research.evidence_contract.task55.data import read

RUN = parser.OUT / 'parser_run_01'


def test_exact_subject_reversions_reproduce_only_the_associated_fault():
    sources = parser.subject_sources()
    subjects = {name: parser.load_source(source, name) for name, source in sources.items()}
    cases = parser.cases_from_plan(read(parser.OUT / 'plan.json'))
    for family in parser.PATCHES:
        case = next(case for case in cases if case['known_fault_family'] == family)
        assert not parser.execute(subjects['before'], case)['passed']
        assert parser.execute(subjects['fixed'], case)['passed']
        assert not parser.execute(subjects['revert_' + family], case)['passed']
        other = next(value for value in parser.PATCHES if value != family)
        assert parser.execute(subjects['revert_' + other], case)['passed']


def test_delta_debugging_keeps_the_failure_and_is_one_minimal():
    predicate = lambda values: {2, 7} <= set(values)
    result = parser.ddmin(list(range(10)), predicate)
    assert predicate(result)
    assert all(not predicate(result[:i] + result[i + 1:]) for i in range(len(result)))


def test_delta_debugging_rejects_nonreproducing_input():
    with pytest.raises(ValueError, match='does not reproduce'):
        parser.ddmin([1, 2], lambda values: 9 in values)


def test_public_replay_checks_all_actual_outputs():
    result = replay.verify(RUN)
    assert result['cases'] == 118 and result['actual_replay_parser_calls'] == 596
    assert result['historical_fault_families'] == 2 and result['new_faults_discovered'] == 0


@pytest.mark.parametrize('change', ['invent_output', 'alter_subject', 'inflate_faults', 'claim_model_calls', 'false_integer'])
def test_replay_rejects_corrupted_or_inflated_evidence(tmp_path, change):
    copy = tmp_path / 'artifact'
    shutil.copytree(RUN, copy)
    path = copy / 'results.json'
    report = read(path)
    if change == 'invent_output':
        output = read(copy / 'outputs.json')
        output[0]['outputs']['before']['fields'] = {'full_name': 'FABRICATED'}
        (copy / 'outputs.json').write_text(json.dumps(output), encoding='utf-8')
        report['outputs_sha256'] = replay.digest(output)
    elif change == 'alter_subject':
        with (copy / 'subjects/revert_custom_single_character.py').open('ab') as stream:
            stream.write(b'\n# unapproved subject alteration\n')
    elif change == 'inflate_faults':
        report['historical_fault_families'] = 76
    elif change == 'claim_model_calls':
        report['model_calls'] = 118
    else:
        report['method_totals']['before']['total'] = 118.0
    path.write_text(json.dumps(report), encoding='utf-8')
    with pytest.raises(ValueError):
        replay.verify(copy)


def summary():
    return dict(contract='C2', validity='VALID', output_bound=True, structure_bound=True, pixels_bound=True,
        after_graph_present=True, after_state='SUPPORTED', before_usable=True, after_usable=True,
        before_correct=False, after_correct=False, after_present=True, geometry_allowed=True,
        limited_candidate_precondition=False)


def test_projection_keeps_pointwise_vs_relation_conditioning_explicit():
    data = summary()
    assert representation.reduced_verdict(data) == 'CANDIDATE_VIOLATION'
    data['contract'] = 'C3'
    assert representation.reduced_verdict(data) == 'INCONCLUSIVE'


def test_limited_removal_is_unverified_candidate_and_does_not_bypass_binding():
    data = dict(summary(), contract='C1', validity='INCONCLUSIVE', limited_candidate_precondition=True)
    assert representation.reduced_verdict(data) == 'CANDIDATE_VIOLATION'
    data['structure_bound'] = False
    assert representation.reduced_verdict(data) == 'INVALID_TEST'


def test_projection_does_not_promote_malformed_or_unknown_sources():
    assert representation.reduced_verdict(dict(summary(), after_usable=False)) == 'INCONCLUSIVE'
    assert representation.reduced_verdict(dict(summary(), after_state='UNKNOWN')) == 'INCONCLUSIVE'


def test_projection_rejects_unsupported_geometry():
    assert representation.reduced_verdict(dict(summary(), contract='C4', geometry_allowed=False,
                                              before_correct=True)) == 'INCONCLUSIVE'


def test_abstract_state_enumeration_preserves_conflicts_and_unknowns():
    cases = representation.source_state_enumeration()
    assert len(cases) == 255 and all(case['equivalent'] for case in cases)
    assert all(case['graph_state'] == 'UNKNOWN' for case in cases if 'conflicting' in case['source_states'])
    assert all(case['graph_state'] == 'UNKNOWN' for case in cases if not case['source_states'])


def test_artifact_folder_cannot_overwrite_previous_execution():
    with pytest.raises(FileExistsError):
        parser.run(RUN)
    with pytest.raises(FileExistsError):
        representation.run(parser.OUT / 'representation_run_01')
