"""Standard-library verifier for saved constructed controls, not their truth.

Usage: python -I -B reference_stress_verify.py <folder-with-cases-and-results>
Checks hashes, injected origin, bindings, deduplication and arithmetic. It does
not reconstruct pixels, run methods, verify readability or create human gold.
"""
import hashlib
import json
from pathlib import Path

METHODS = {'A_frozen', 'A_change_union', 'A_dual', 'B3', 'A_flat', 'A_bound_dual', 'B3_bound'}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def arithmetic(cases):
    result = {endpoint: {} for endpoint in ('pointwise', 'relation')}
    for endpoint in result:
        for name in METHODS:
            counts = dict(TP=0, FP=0, FN=0, TN=0)
            known = decided = unknown_alarms = abstained_faults = 0
            for case in cases:
                truth = case['expected'][endpoint]
                check = case['methods'][name][endpoint]
                if truth is None:
                    unknown_alarms += check['alarm']
                else:
                    known += 1
                    if truth is True:
                        counts['TP' if check['alarm'] else 'FN'] += 1
                    else:
                        counts['FP' if check['alarm'] else 'TN'] += 1
                    is_decided = check['verdict'] in {'PASS', 'CANDIDATE_VIOLATION'}
                    decided += is_decided
                    abstained_faults += truth and not is_decided
            result[endpoint][name] = dict(confusion=counts, labeled_control_rows=known,
                decision_coverage=dict(numerator=decided, denominator=known),
                alarms_on_unassessed=unknown_alarms, abstentions_on_known_faults=abstained_faults)
    return result


def verify(folder):
    folder = Path(folder)
    cases = json.loads((folder / 'cases.json').read_text(encoding='utf-8'))
    report = json.loads((folder / 'results.json').read_text(encoding='utf-8'))
    if (report['scope'] != 'CONSTRUCTED_CONTROL_DEVELOPMENT_ONLY' or report['confirmatory'] is not False
            or report['external_reference_approved'] is not False
            or any(type(report[key]) is not int or report[key] != 0 for key in
                   ('model_calls', 'training_steps', 'human_labels_created', 'new_external_reviewers', 'natural_model_faults'))):
        raise ValueError('Unsupported evidence scope or fabricated real/human count')
    if (digest(cases) != report['cases_sha256'] or len(cases) != report['control_executions']
            or len({case['control_id'] for case in cases}) != len(cases)):
        raise ValueError('Case count or digest mismatch')
    unique = {}
    for case in cases:
        if (case['output_origin'] != 'oracle_unit_injected' or case['real_model_error'] is not False
                or case['human_readability_verified'] is not False or set(case['methods']) != METHODS
                or set(case['expected']) != {'pointwise', 'relation', 'format'}
                or type(case['expected']['format']) is not bool
                or any(value is not None and type(value) is not bool for value in case['expected'].values())):
            raise ValueError('A case is not a declared constructed control')
        reference = case['reference']
        if (digest({key: value for key, value in reference.items() if key != 'reference_id'}) != reference['reference_id']
                or reference['scope'] != 'constructed_control' or reference['field_key'] != case['checked_key']
                or reference['before']['pixel_sha256'] != case['before_pixel_sha256']
                or reference['after']['pixel_sha256'] != case['after_pixel_sha256']):
            raise ValueError('Reference content/key/image binding mismatch')
        identity = digest(dict(before_pixel=case['before_pixel_sha256'], after_pixel=case['after_pixel_sha256'],
            graph=case['graph_sha256'], contract=case['contract'], key=case['checked_key'],
            before_raw=case['before_injected_text'], after_raw=case['after_injected_text'],
            reference_before=reference['before'], reference_after=reference['after'], value_kind=reference['value_kind']))
        if identity != case['comparison_identity']:
            raise ValueError('Comparison identity mismatch')
        for endpoints in [*case['methods'].values(), {'format': case['format_lane']}]:
            for check in endpoints.values():
                if (check['verdict'] not in {'PASS', 'CANDIDATE_VIOLATION', 'INCONCLUSIVE', 'INVALID_TEST'}
                        or type(check['alarm']) is not bool or check['alarm'] != (check['verdict'] == 'CANDIDATE_VIOLATION')):
                    raise ValueError('Alarm and verdict mismatch')
        if identity in unique and (case['expected'] != unique[identity]['expected'] or case['methods'] != unique[identity]['methods']):
            raise ValueError('Duplicate comparison has inconsistent results')
        unique[identity] = case
    # JSON hashes also distinguish false from 0 and 0.0 from integer counts.
    if (digest(report['all_executions']) != digest(arithmetic(cases))
            or digest(report['deduplicated']) != digest(arithmetic(list(unique.values())))
            or report['unique_injected_comparisons'] != len(unique)
            or report['unique_pixel_pairs'] != len({(c['before_pixel_sha256'], c['after_pixel_sha256']) for c in cases})):
        raise ValueError('Counts or deduplication arithmetic mismatch')
    if set(report['by_scenario']) != {case['scenario'] for case in cases}:
        raise ValueError('A scenario is missing from the report')
    for scenario, expected in report['by_scenario'].items():
        if digest(expected) != digest(arithmetic([case for case in cases if case['scenario'] == scenario])):
            raise ValueError('Scenario arithmetic mismatch')
    formats = dict(detected=sum(c['format_lane']['alarm'] and c['expected']['format'] for c in cases),
                   injected=sum(c['expected']['format'] for c in cases),
                   false_alarms=sum(c['format_lane']['alarm'] and not c['expected']['format'] for c in cases))
    if digest(formats) != digest(report['format_lane']):
        raise ValueError('Format arithmetic mismatch')
    equal = all(c['methods']['A_bound_dual']['pointwise'] == c['methods']['B3_bound']['pointwise'] for c in cases)
    if report['bound_field_matches_equal_information_baseline'] is not equal:
        raise ValueError('Equal-information field agreement mismatch')
    return dict(status='PASS_CONSTRUCTED_CONTROL_INTEGRITY_AND_ARITHMETIC', control_executions=len(cases),
                unique_injected_comparisons=len(unique), pixels_reconstructed=False,
                method_decisions_reexecuted=False, human_gold_created=False, model_calls=0)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.folder), indent=2))
