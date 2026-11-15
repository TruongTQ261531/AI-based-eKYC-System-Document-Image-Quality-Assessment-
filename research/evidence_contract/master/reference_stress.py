"""Constructed controls for reference poisoning, validity and endpoint coverage.

Every output is explicitly injected. Fixed fixture strings and pixel probes are
used instead of method verdicts for control expectations. The pixel audit shares
the pristine renderer's inventory; this is not independent human evidence.
"""
from collections import Counter
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .. import generator
from ..fixtures import backup_fixture, shared_context_fixture
from ..normalized_output import ReaderSpec, NativeOutput, canonical, normalize
from ..source_graph import digest, pixel_sha256
from ..task5 import baselines
from ..task55.data import EC, read, save_new, sha
from .a_variants import lanes
from .faults import probe
from . import reference_policy as bound

OUT = EC / 'execution/master_01/reference_stress_20261116'
VALUES = dict(id_number='DEMO12345', school='RESEARCH SCHOOL', category='CATEGORY ONE', category_code='DEMO CODE')
EXPECTED_SOURCE = dict(C1_complete='REMOVED', C1_limited='SUPPORTED', C2_backup='SUPPORTED',
                       C2_bad_backup='UNKNOWN', C3_keep='SUPPORTED', C3_lost_context='UNKNOWN',
                       C4_translate='SUPPORTED', C4_identity='SUPPORTED', C2_reference_poison='SUPPORTED')
SPEC = ReaderSpec('constructed-reference-control', 'injected-control/1', 'a' * 64,
                  canonical(dict(predictor='none')), 'b' * 64, canonical(dict(runtime='control_only')),
                  output_origin='oracle_unit_injected')


def pair_for(scenario, seed):
    if scenario == 'C3_lost_context':
        image, graph, target, retained = shared_context_fixture()
        audit = graph
        kind = 'pair_a_mask'
    else:
        image, graph, target, retained = backup_fixture(limited=scenario == 'C1_limited', bad_checksum=scenario == 'C2_bad_backup')
        audit = backup_fixture()[1] if scenario == 'C1_limited' else graph
        if scenario == 'C2_reference_poison':
            graph = replace(graph, fields=tuple(
                replace(field, reference_value='POISONED_REFERENCE', realizations=tuple(
                    replace(source, reference_value='POISONED_REFERENCE') for source in field.realizations))
                if field.key == target else field for field in graph.fields))
        kind = ('all_sources_mask' if scenario.startswith('C1_') else 'single_source_mask' if scenario.startswith('C2_')
                else 'pair_a_mask' if scenario == 'C3_keep' else 'geometry_translate' if scenario == 'C4_translate' else 'full')
        if scenario.startswith('C4_'):
            target = retained
    mutation = generator.plan(graph, kind, target_key=target,
                              retained_key=retained if kind == 'pair_a_mask' else None, seed=seed)
    return generator.generate(image, graph, mutation), audit


def measured_translation(before, after):
    """Find an exact whole-image translation from pixels, without reading H."""
    height, width = before.shape[:2]
    dy_max, dx_max = after.shape[0] - height, after.shape[1] - width
    if not (0 <= dx_max <= 40 and 0 <= dy_max <= 40):
        raise ValueError('Control translation outside declared search budget')
    anchor = before[15:65, 20:800]
    matches = []
    for dy in range(dy_max + 1):
        for dx in range(dx_max + 1):
            if (np.array_equal(anchor, after[15 + dy:65 + dy, 20 + dx:800 + dx])
                    and np.array_equal(before, after[dy:dy + height, dx:dx + width])):
                matches.append((dx, dy))
    if len(matches) != 1:
        raise ValueError('Pixel translation not uniquely verified')
    return matches[0]


def inventory_frame(pair, inventory, key, *, after, bad_checksum=False):
    observed = pair.followup if after else pair.original
    dx, dy = measured_translation(pair.original, observed) if after and pair.mutation.operator == 'translate_pad' else (0, 0)
    sources, probes = [], {}
    for source in inventory.field(key).realizations:
        components = {component.component_id: probe(pair.original, observed, component, dx, dy, (35, 38, 42))
                      for component in source.components if component.required}
        values = [components[c.component_id] for c in source.components if c.required and c.role == 'value']
        state = ('REMOVED' if values and all(value == 'erased' for value in values)
                 else 'SUPPORTED' if components and all(value == 'preserved' for value in components.values()) else 'UNKNOWN')
        conditions = dict(semantic_link=True, integrity=state in {'REMOVED', 'SUPPORTED'})
        if source.kind == 'mrz':
            conditions.update(format_valid=True, field_checksum=not bad_checksum, composite_checksum=not bad_checksum)
        sources.append(dict(source_id=source.source_id, semantic_key=key, kind=source.kind, state=state,
                            value=VALUES[key], conditions=conditions))
        probes[source.source_id] = components
    return dict(pixel_sha256=pixel_sha256(observed), inventory_complete=True, sources=sources), probes, (dx, dy)


def reference_for(pair, audit, scenario):
    key = baselines.key_for(pair.validation)
    context = bound.PairContext(pair.mutation.contract_id, key, pixel_sha256(pair.original), pixel_sha256(pair.followup),
                                pair.mutation.sha256, pair.validation.status.value, pair.mutation.operator)
    before, first_probes, _ = inventory_frame(pair, audit, key, after=False, bad_checksum=scenario == 'C2_bad_backup')
    after, second_probes, offset = inventory_frame(pair, audit, key, after=True, bad_checksum=scenario == 'C2_bad_backup')
    payload = dict(schema=bound.SCHEMA, policy=bound.POLICY, scope='constructed_control', field_key=key,
                   value_kind='identifier' if key == 'id_number' else 'text',
                   provenance='Fixed fictional strings and pixel-slice checker; shared pristine renderer inventory; no independent reviewer or human readability claim',
                   mutation_sha256=context.mutation_sha256, before=before, after=after)
    reference = bound.seal_reference(payload)
    resolved = bound.resolve(after, payload['value_kind'])
    if resolved['state'] != EXPECTED_SOURCE[scenario]:
        raise ValueError('Pixel audit does not match the declared control scenario: ' + scenario)
    return reference, context, dict(before=first_probes, after=second_probes, measured_offset=list(offset))


def injected(value, image, key, *, malformed=False):
    raw = '{"' + key + '":' if malformed else json.dumps({key: value} if value is not None else {}, ensure_ascii=False)
    native = NativeOutput(raw, 0., 0., dict(origin='constructed control; no predictor invoked'))
    return normalize(SPEC, native, input_file_sha256=hashlib.sha256(generator.png_bytes(image)).hexdigest(),
                     input_pixel_sha256=pixel_sha256(image), cache_key=digest(['control', raw, pixel_sha256(image)]),
                     call_id=digest(['injected', raw, pixel_sha256(image)]))


def control_case(scenario, seed, mode, pair, reference, context, probes):
    before_mode, after_mode = mode.split('_')
    def value(which, *, after):
        if which == 'empty': return None
        if which == 'wrong': return 'MISMATCH_VALUE'
        if which == 'malformed': return None
        return None if after and EXPECTED_SOURCE[scenario] == 'REMOVED' else VALUES[context.key]
    before = injected(value(before_mode, after=False), pair.original, context.key)
    after = injected(value(after_mode, after=True), pair.followup, context.key, malformed=after_mode == 'malformed')
    checks = dict(A=baselines.unpack(baselines.proposed(pair.graph, pair.validation, before, after)),
                  B2=baselines.unpack(baselines.b2(pair.validation, before, after)),
                  B3=baselines.unpack(baselines.visible_reference(pair.graph, pair.validation, before, after)),
                  A_flat=baselines.unpack(baselines.flat_contract(pair.graph, pair.validation, before, after)))
    methods = {name: row for name, row in lanes(dict(checks=checks, validity=context.validity)).items()
               if name != 'A_reference_gate'}
    result = bound.evaluate(reference, context, before, after)
    methods['A_bound_dual'] = {key: result[key] for key in ('pointwise', 'relation')}
    methods['B3_bound'] = dict(pointwise=result['pointwise'], relation=result['pointwise'])
    field_fault = None
    if context.validity == 'VALID' and after_mode != 'malformed' and EXPECTED_SOURCE[scenario] != 'UNKNOWN':
        field_fault = after_mode == 'wrong' if EXPECTED_SOURCE[scenario] == 'REMOVED' else after_mode != 'correct'
    relation_fault = field_fault if context.contract in {'C1', 'C2'} or before_mode == 'correct' else None
    expected = dict(pointwise=field_fault, relation=relation_fault, format=after_mode == 'malformed')
    for endpoint in ('pointwise', 'relation'):
        if expected[endpoint] is not None and result[endpoint]['alarm'] != expected[endpoint]:
            raise ValueError('Bound control disagrees with the predeclared expectation')
    if result['format']['alarm'] != expected['format']:
        raise ValueError('Format lane disagrees with the injected structure')
    identity = digest(dict(before_pixel=context.before_pixel_sha256, after_pixel=context.after_pixel_sha256,
                           graph=pair.graph.sha256, contract=context.contract, key=context.key,
                           before_raw=before.raw_text, after_raw=after.raw_text,
                           reference_before=reference['before'], reference_after=reference['after'],
                           value_kind=reference['value_kind']))
    return dict(control_id=f'{scenario}/{seed}/{mode}', comparison_identity=identity, scenario=scenario,
                seed=seed, mode=mode, contract=context.contract, checked_key=context.key,
                validity=context.validity, expected=expected, methods=methods, format_lane=result['format'],
                before_pixel_sha256=context.before_pixel_sha256, after_pixel_sha256=context.after_pixel_sha256,
                graph_sha256=pair.graph.sha256, reference=reference, pixel_probes=probes,
                before_injected_text=before.raw_text, after_injected_text=after.raw_text,
                output_origin='oracle_unit_injected', reference_accepted=result['reference_accepted'],
                human_readability_verified=False, real_model_error=False)


def summarize(cases, methods):
    summary = {}
    for endpoint in ('pointwise', 'relation'):
        summary[endpoint] = {}
        for name in methods:
            counts = Counter(dict(TP=0, FP=0, FN=0, TN=0))
            unknown_alarms = decided = known = abstained_faults = 0
            for case in cases:
                truth = case['expected'][endpoint]
                decision = case['methods'][name][endpoint]
                if truth is None:
                    unknown_alarms += decision['alarm']
                    continue
                known += 1
                counts[('TP' if decision['alarm'] else 'FN') if truth else ('FP' if decision['alarm'] else 'TN')] += 1
                decided += decision['verdict'] in {'PASS', 'CANDIDATE_VIOLATION'}
                abstained_faults += truth and decision['verdict'] not in {'PASS', 'CANDIDATE_VIOLATION'}
            summary[endpoint][name] = dict(confusion=dict(counts), labeled_control_rows=known,
                decision_coverage=dict(numerator=decided, denominator=known), alarms_on_unassessed=unknown_alarms,
                abstentions_on_known_faults=abstained_faults)
    return summary


def run(plan_path, destination):
    plan = read(plan_path)
    if (plan['scope'] != 'CONSTRUCTED_CONTROL_DEVELOPMENT_ONLY' or plan['model_call_budget'] != 0
            or plan['planned_control_executions'] != 252):
        raise ValueError('Use the declared zero-model constructed-control plan')
    destination = Path(destination).resolve()
    if not destination.is_relative_to(OUT.resolve()) or destination.exists():
        raise ValueError('Use a fresh destination within this development checkpoint')
    start = time.perf_counter()
    cases = []
    for scenario in plan['scenarios']:
        for seed in plan['seeds']:
            pair, audit = pair_for(scenario, seed)
            reference, context, probes = reference_for(pair, audit, scenario)
            for mode in plan['output_modes']:
                cases.append(control_case(scenario, seed, mode, pair, reference, context, probes))
    if len(cases) != plan['planned_control_executions']:
        raise ValueError('The executed schedule differs from the declared plan')
    unique = {}
    for case in cases:
        identity = case['comparison_identity']
        if identity in unique and (unique[identity]['expected'] != case['expected'] or unique[identity]['methods'] != case['methods']):
            raise ValueError('Duplicate comparison has inconsistent judgments')
        unique[identity] = case
    report = dict(schema='constructed-reference-stress/1', scope=plan['scope'], plan_sha256=sha(plan_path),
                  source_sha256=sha(__file__), policy_source_sha256=sha(Path(bound.__file__)),
                  control_executions=len(cases), unique_injected_comparisons=len(unique),
                  unique_pixel_pairs=len({(c['before_pixel_sha256'], c['after_pixel_sha256']) for c in cases}),
                  model_calls=0, training_steps=0, human_labels_created=0, new_external_reviewers=0,
                  natural_model_faults=0, confirmatory=False, external_reference_approved=False,
                  note='Constructed expectations only. Pixel checker shares pristine fixture inventory. Equal-information B3_bound receives the same sealed reference; no graph superiority claim.',
                  all_executions=summarize(cases, plan['methods']), deduplicated=summarize(list(unique.values()), plan['methods']),
                  by_scenario={scenario:summarize([c for c in cases if c['scenario'] == scenario], plan['methods']) for scenario in plan['scenarios']},
                  bound_field_matches_equal_information_baseline=all(c['methods']['A_bound_dual']['pointwise'] == c['methods']['B3_bound']['pointwise'] for c in cases),
                  format_lane=dict(detected=sum(c['format_lane']['alarm'] and c['expected']['format'] for c in cases),
                                   injected=sum(c['expected']['format'] for c in cases),
                                   false_alarms=sum(c['format_lane']['alarm'] and not c['expected']['format'] for c in cases)),
                  cases_sha256=digest(cases), wall_seconds=time.perf_counter() - start)
    save_new(destination / 'cases.json', cases)
    save_new(destination / 'results.json', report)
    lines = ['# Constructed reference stress — development only', '', report['note'], '',
             f"{len(cases)} scheduled injected executions; {len(unique)} unique comparison identities; {report['unique_pixel_pairs']} unique pixel pairs.", '',
             '| Panel | Endpoint | Method | TP/FP/FN/TN | Decision coverage | Alarms on unassessed |',
             '|---|---|---|---|---|---|']
    for panel in ('all_executions', 'deduplicated'):
        for endpoint, methods in report[panel].items():
            for name, data in methods.items():
                counts = '/'.join(str(data['confusion'][key]) for key in ('TP', 'FP', 'FN', 'TN'))
                coverage = data['decision_coverage']
                lines.append(f"| {panel} | {endpoint} | {name} | {counts} | {coverage['numerator']}/{coverage['denominator']} | {data['alarms_on_unassessed']} |")
    lines += ['', 'No population estimate, human readability, independent adjudication or new real-model fault evidence is implied.', '']
    (destination / 'results.md').write_text('\n'.join(lines), encoding='utf-8')
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, default=OUT / 'plan.json')
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.plan, args.destination)
    print(json.dumps({key: report[key] for key in ('scope', 'control_executions', 'unique_injected_comparisons', 'unique_pixel_pairs', 'format_lane', 'model_calls', 'wall_seconds')}, indent=2))
