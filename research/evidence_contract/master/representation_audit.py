"""Finite, explicit reduction of the frozen decision boundary; not a new oracle.

Projection retains upstream source/reference information. It does not establish
that graph annotations are unnecessary for generation, validity or explanations.
All reader outputs here are injected; source-state enumeration is abstract.
"""
from dataclasses import replace
import itertools
import json
from pathlib import Path

from .. import contracts
from ..fixtures import backup_fixture
from ..source_graph import State
from ..task5 import baselines, planning
from ..task55.data import EC, ROOT, digest, save_new, sha
from .reference_stress import injected, pair_for

OUT = EC / 'execution/master_01/readiness_20261116'
SCENARIOS = ('C1_complete', 'C2_backup', 'C3_keep', 'C4_translate',
             'C1_limited', 'C2_bad_backup', 'C3_lost_context', 'C4_identity', 'C2_reference_poison')


def project(graph, report, before, after):
    """Collect sufficient state at the oracle boundary, without an A verdict."""
    key = baselines.key_for(report)
    field = report.after_graph.field(key) if report.after_graph else None
    original = (report.reference_before_graph or graph).field(key)
    return dict(contract=report.mutation.contract_id, validity=report.status.value,
        output_bound=(before.input_pixel_sha256 == report.before_pixel_sha256
            and after.input_pixel_sha256 == report.after_pixel_sha256
            and before.reader_fingerprint == after.reader_fingerprint and before.output_origin == after.output_origin),
        structure_bound=(report.graph_sha256 == graph.sha256 and report.mutation_sha256 == report.mutation.sha256),
        pixels_bound=(report.before_pixel_sha256 == graph.input_pixel_sha256
                      and (report.after_graph is None or report.after_graph.input_pixel_sha256 == report.after_pixel_sha256)),
        after_graph_present=report.after_graph is not None,
        after_state=field.state().value if field else 'UNKNOWN',
        before_usable=before.json_validity['usable_for_contracts'], after_usable=after.json_validity['usable_for_contracts'],
        before_correct=contracts.assessment(before.fields, original) == 'correct',
        after_correct=bool(field and contracts.assessment(after.fields, field) == 'correct'),
        after_present=bool(after.fields.get(key, '').strip()),
        geometry_allowed=report.mutation.operator in contracts.Policy().geometry_operators,
        limited_candidate_precondition=(set(report.reasons) == {'exhaustive_removal_not_proven_by_annotation_scope'}
            and bool(field and field.realizations) and all(source.state() == State.REMOVED for source in field.realizations)))


def reduced_verdict(summary):
    """Predicate transcription for default policy, no certificate/gold/version quad.

    Equality is conditional on preserved upstream information. This is an
    explanatory reduction, not independently sourced truth or a novel detector.
    """
    s = summary
    contract = s['contract']
    if not s['output_bound'] or not s['structure_bound'] or s['validity'] == 'INVALID_TEST':
        return 'INVALID_TEST'
    if (contract == 'C1' and s['validity'] != 'VALID' and s['after_usable']
            and s['limited_candidate_precondition'] and s['after_present']):
        return 'CANDIDATE_VIOLATION'
    if s['validity'] != 'VALID' or not s['after_graph_present']:
        return 'INCONCLUSIVE'
    if not s['pixels_bound']:
        return 'INVALID_TEST'
    if not s['after_usable'] or contract in ('C3', 'C4') and not s['before_usable']:
        return 'INCONCLUSIVE'
    if contract == 'C1':
        if s['after_state'] != 'REMOVED':
            return 'INCONCLUSIVE'
        return 'CANDIDATE_VIOLATION' if s['after_present'] else 'PASS'
    if s['after_state'] != 'SUPPORTED':
        return 'INCONCLUSIVE'
    if contract == 'C4' and not s['geometry_allowed']:
        return 'INCONCLUSIVE'
    if contract in ('C3', 'C4') and not s['before_correct']:
        return 'INCONCLUSIVE'
    return 'PASS' if s['after_correct'] else 'CANDIDATE_VIOLATION'


def source_state_enumeration():
    """0..3 text sources, four source states, complete/limited/unknown scope."""
    _, graph, key, _ = backup_fixture()
    template = graph.field(key)
    source = template.realizations[0]
    cases = []
    for count in range(4):
        for modes, coverage in itertools.product(itertools.product(('removed', 'unknown', 'matching', 'conflicting'), repeat=count),
                                                 ('complete', 'limited', 'unknown')):
            sources = []
            for index, mode in enumerate(modes):
                components = tuple(replace(component, component_id=f'{index}/{component.component_id}',
                    availability='removed' if mode == 'removed' else 'unknown' if mode == 'unknown' else 'available')
                    for component in source.components)
                sources.append(replace(source, source_id=str(index), components=components,
                    reference_value='OTHER_VALUE' if mode == 'conflicting' else template.reference_value))
            field = replace(template, realizations=tuple(sources), coverage=coverage)
            reduced = ('UNKNOWN' if 'conflicting' in modes else 'SUPPORTED' if 'matching' in modes else
                       'REMOVED' if modes and coverage == 'complete' and all(mode == 'removed' for mode in modes) else 'UNKNOWN')
            actual = field.state().value
            cases.append(dict(source_states=list(modes), coverage=coverage, graph_state=actual,
                              reduced_state=reduced, equivalent=actual == reduced))
    return cases


def case_for(scenario, pair, before_mode, after_mode, *, diagnostic=None):
    graph, report = pair.graph, pair.validation
    key = baselines.key_for(report)
    reference = graph.field(key).reference_value
    def output_for(mode, image):
        value = reference if mode == 'matching' else 'WRONG_VALUE' if mode == 'wrong' else None
        return injected(value, image, key, malformed=mode == 'malformed')
    before, after = output_for(before_mode, pair.original), output_for(after_mode, pair.followup)
    if diagnostic == 'graph_binding':
        report = replace(report, graph_sha256='0' * 64)
    elif diagnostic == 'mutation_binding':
        report = replace(report, mutation_sha256='0' * 64)
    elif diagnostic == 'origin_binding':
        # Metadata corruption probe, not actual inference or an actual-model row.
        after = replace(after, output_origin='actual_model')
    elif diagnostic == 'image_binding':
        after = replace(after, input_pixel_sha256='0' * 64)
    a = baselines.unpack(baselines.proposed(graph, report, before, after))
    flat = baselines.unpack(baselines.flat_contract(graph, report, before, after))
    projection = project(graph, report, before, after)
    reduced = reduced_verdict(projection)
    return dict(scenario=scenario, before_mode=before_mode, after_mode=after_mode,
        diagnostic=diagnostic, contract=report.mutation.contract_id,
        output_origin='injected_boundary_control', model_invoked=False,
        metadata_origin_corrupted=diagnostic == 'origin_binding',
        before_pixel_sha256=pair.validation.before_pixel_sha256,
        after_pixel_sha256=pair.validation.after_pixel_sha256, graph_sha256=graph.sha256,
        mutation_sha256=pair.mutation.sha256, A=a, A_flat=flat, projection=projection,
        reduced_verdict=reduced, reduction_equal=reduced == a['verdict'],
        flat_equal=(a['verdict'], a['alarm']) == (flat['verdict'], flat['alarm']))


def run(folder):
    folder = Path(folder)
    if folder.exists():
        raise FileExistsError('Use a fresh execution directory')
    cases = []
    modes = ('matching', 'wrong', 'empty', 'malformed')
    for scenario in SCENARIOS:
        pair, _ = pair_for(scenario, 42)
        for before_mode, after_mode in itertools.product(modes, repeat=2):
            cases.append(case_for(scenario, pair, before_mode, after_mode))
    incomplete = next(pair for name, pair in planning.diagnostics() if name == 'incomplete_target_erasure')
    for before_mode, after_mode in itertools.product(modes, repeat=2):
        cases.append(case_for('incomplete_target_erasure', incomplete, before_mode, after_mode))
    pair, _ = pair_for('C2_backup', 42)
    for diagnostic in ('graph_binding', 'mutation_binding', 'origin_binding', 'image_binding'):
        cases.append(case_for('binding_diagnostic', pair, 'matching', 'wrong', diagnostic=diagnostic))
    states = source_state_enumeration()
    primary = [case for case in cases if case['scenario'] in SCENARIOS[:4]]
    report = dict(schema='representation-boundary-audit/1', scope='FINITE_DEVELOPMENT_REDUCTION',
        model_calls=0, training_steps=0, human_labels_created=0, confirmatory=False,
        source_enumeration=dict(cases=len(states), equivalent=sum(c['equivalent'] for c in states),
            domain='0..3 text sources, four abstract source states, three coverage states; no image truth claim'),
        oracle_controls=len(cases), primary_controls=len(primary), primary_A_flat_equal=sum(c['flat_equal'] for c in primary),
        all_A_flat_equal=sum(c['flat_equal'] for c in cases), reduced_A_equal=sum(c['reduction_equal'] for c in cases),
        flat_counterexamples=[dict(scenario=c['scenario'], before=c['before_mode'], after=c['after_mode'],
            diagnostic=c['diagnostic'], A=c['A'], A_flat=c['A_flat']) for c in cases if not c['flat_equal']],
        universal_equivalence_claim=False,
        reduction_assumptions=['Default policy; no independent gold/certificate/version quad',
            'All upstream validity, bindings, source states and typed assessment retained',
            'Analyzed fields annotated; finite text/control domains only',
            'Same verdict/alarm boundary, not diagnostic explanation or generation cost'],
        remaining_value_of_graph='Generation, validity, evidence provenance and explanations need separate cost/correctness experiments',
        cases_sha256=digest(cases), states_sha256=digest(states),
        module_sha256=sha(Path(__file__)), plan_sha256=sha(OUT / 'plan.json'),
        frozen_sources_sha256={str(path.relative_to(ROOT)): sha(path) for path in
            (EC / 'source_graph.py', EC / 'contracts.py', EC / 'oracle.py', EC / 'task5/baselines.py')})
    save_new(folder / 'cases.json', cases)
    save_new(folder / 'source_states.json', states)
    save_new(folder / 'results.json', report)
    if report['reduced_A_equal'] != len(cases) or report['source_enumeration']['equivalent'] != len(states):
        raise ValueError('Reduction does not match the finite controls; inspect saved evidence')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = run(parser.parse_args().output)
    print(json.dumps({key: report[key] for key in ('source_enumeration', 'oracle_controls', 'primary_controls',
        'primary_A_flat_equal', 'all_A_flat_equal', 'reduced_A_equal', 'flat_counterexamples')}, ensure_ascii=False, indent=2))
