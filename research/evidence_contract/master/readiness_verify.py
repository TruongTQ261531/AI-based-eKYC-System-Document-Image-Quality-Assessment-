"""Standard-library replay of the public historical-parser development artifact.

Run: python -I -B readiness_verify.py <parser_run_folder>
Executes only the two pinned source snapshots and their exact patch reversions.
Verifies saved outputs/counts and patch causality. It does not validate authored
requirements independently, reproduce neural inference, or certify EASE readiness.
"""
import ast
import hashlib
import json
from pathlib import Path
from types import ModuleType

BEFORE_SHA = 'cca292ef3a12a96757bb9b912a261d1dd591f5f8110e72da7c299183f39b9431'
FIXED_SHA = '3f10617d53a5e11b4f2541a3d2ef63504a38c979cb3cc79256b56524317c0e62'
PATCHES = {
    'custom_single_character': (r"custom=re.match(r'^([^:：]{2,60})[:：]\s*(\S.+)$',text)",
                                r"custom=re.match(r'^([^:：]{2,60})[:：]\s*(\S.*)$',text)"),
    'conflicting_scalar_name': ("if key in ('address','hometown','full_name'): fields[key]=' '.join(parts)",
                                "if key in ('address','hometown'): fields[key]=' '.join(parts)"),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def execute(module, case):
    lines = [dict(text=text, confidence=.99, source='authored_regression_tokens',
        box=[[0, i * 25], [600, i * 25], [600, i * 25 + 18], [0, i * 25 + 18]]) for i, text in enumerate(case['texts'])]
    fields, items, kind = module.observed_information(lines, dict(case['specialized']))
    labelled = {item['label']: item['value'] for item in items}
    failures = []
    for key, expected in case['required_fields'].items():
        if fields.get(key) != expected:
            failures.append('field_value:' + key)
    for key in case['absent_fields']:
        if key in fields:
            failures.append('unexpected_field:' + key)
    for label, expected in case['required_items'].items():
        if labelled.get(label) != expected:
            failures.append('labelled_value:' + label)
    if case['require_empty_fields'] and fields:
        failures.append('unexpected_observed_fields')
    return dict(passed=not failures, failures=failures, fields=fields, labelled_items=labelled, document_type=kind['key'])


def verify(folder):
    folder = Path(folder)
    read = lambda name: json.loads((folder / name).read_text(encoding='utf-8'))
    report, cases, outputs = read('results.json'), read('cases.json'), read('outputs.json')
    if (report['scope'] != 'KNOWN_FAULT_POST_FIX_DEVELOPMENT' or report['confirmatory'] is not False
            or report['frozen_A_evaluated'] is not False or report['frozen_A_changed'] is not False
            or report['output_origin'] != 'actual_parser_execution_on_authored_ocr_tokens'
            or any(type(report[key]) is not int or report[key] != 0 for key in
                   ('new_faults_discovered', 'human_labels_created', 'model_calls', 'training_steps'))):
        raise ValueError('Unsupported scope or claimed human/model/new-fault evidence')
    if (len(cases) != 118 or len(outputs) != len(cases) or len({case['case_id'] for case in cases}) != len(cases)
            or digest(cases) != report['cases_sha256'] or digest(outputs) != report['outputs_sha256']
            or report['cases'] != len(cases) or report['unique_inputs'] != len({case['input_sha256'] for case in cases})):
        raise ValueError('Case/output manifest or count differs')
    methods = {'before', 'fixed', 'revert_custom_single_character', 'revert_conflicting_scalar_name', 'revert_both'}
    if set(report['sources_sha256']) != methods:
        raise ValueError('Missing/unexpected subject')
    payloads = {name: (folder / 'subjects' / (name + '.py')).read_bytes() for name in methods}
    if (hashlib.sha256(payloads['before']).hexdigest() != BEFORE_SHA
            or hashlib.sha256(payloads['fixed']).hexdigest() != FIXED_SHA):
        raise ValueError('Pinned subject source mismatch')
    text = payloads['fixed'].decode('utf-8')
    both = text
    for family, (old, new) in PATCHES.items():
        if text.count(new) != 1 or payloads['revert_' + family] != text.replace(new, old).encode('utf-8'):
            raise ValueError('Individual reversion differs from the declared patch')
        both = both.replace(new, old)
    if (payloads['revert_both'] != both.encode('utf-8')
            or ast.dump(ast.parse(both)) != ast.dump(ast.parse(payloads['before']))):
        raise ValueError('Combined reversion differs from the historical program')
    modules = {}
    for name, payload in payloads.items():
        if hashlib.sha256(payload).hexdigest() != report['sources_sha256'][name]:
            raise ValueError('Subject/report hash mismatch')
        module = ModuleType(name)
        exec(compile(payload, name, 'exec'), module.__dict__)
        modules[name] = module
    calls = 0
    totals = {name: dict(passed=0, total=len(cases)) for name in methods}
    for case, row in zip(cases, outputs):
        if (row['case_id'] != case['case_id'] or set(row['outputs']) != methods
                or case['input_origin'] != 'authored_ocr_tokens' or type(case['require_empty_fields']) is not bool
                or case['known_fault_family'] not in {None, *PATCHES}
                or case['input_sha256'] != digest(dict(texts=case['texts'], specialized=case['specialized']))
                or case['requirement_sha256'] != digest({key: case[key] for key in
                    ('required_fields', 'absent_fields', 'required_items', 'require_empty_fields')})):
            raise ValueError('Case bindings or declared requirement mismatch')
        for name, module in modules.items():
            measured = execute(module, case)
            calls += 1
            if digest(measured) != digest(row['outputs'][name]):
                raise ValueError('Saved output does not replay: ' + case['case_id'] + '/' + name)
            totals[name]['passed'] += measured['passed']
    if digest(totals) != digest(report['method_totals']):
        raise ValueError('Method aggregate mismatch')
    for kind in {case['kind'] for case in cases}:
        selected = [row for case, row in zip(cases, outputs) if case['kind'] == kind]
        measured = {name: dict(passed=sum(row['outputs'][name]['passed'] for row in selected), total=len(selected)) for name in methods}
        if digest(measured) != digest(report['per_kind'][kind]):
            raise ValueError('Kind aggregate mismatch')
    expected_faults = {}
    for family in PATCHES:
        other = next(value for value in PATCHES if value != family)
        selected = [row for case, row in zip(cases, outputs) if case['known_fault_family'] == family]
        valid = all(not row['outputs']['before']['passed'] and row['outputs']['fixed']['passed']
            and not row['outputs']['revert_' + family]['passed'] and row['outputs']['revert_' + other]['passed']
            and not row['outputs']['revert_both']['passed'] for row in selected)
        expected_faults[family] = dict(authored_variants=len(selected), independent_faults=1, all_fix_revert_witnesses=valid)
    if (digest(expected_faults) != digest(report['historical_faults']) or report['historical_fault_families'] != 2
            or report['unexpected_cases'] != [] or report['status'] != 'PASS_KNOWN_FAULT_REPRODUCTION'):
        raise ValueError('Fault attribution/status mismatch')
    for witness in report['delta_debugging']:
        case = next(case for case in cases if case['case_id'] == witness['original_case'])
        required = [text for text in case['texts'] if text not in ('TÀI LIỆU THỬ', 'MẪU MINH HỌA')]
        minimal = witness['minimal_texts']
        if (witness['family'] != case['known_fault_family'] or witness['specialized'] != case['specialized']
                or witness['one_minimal_under_requirement'] is not True
                or any(text not in minimal for text in required)
                or any(all(text in minimal[:i] + minimal[i+1:] for text in required) for i in range(len(minimal)))):
            raise ValueError('Invalid constrained 1-minimal witness')
        measured = {name: execute(modules[name], dict(case, texts=minimal)) for name in
                    ('before', 'fixed', 'revert_' + witness['family'])}
        calls += 3
        if measured['before']['passed'] or not measured['fixed']['passed'] or measured['revert_' + witness['family']]['passed']:
            raise ValueError('Minimized failure does not replay')
    return dict(status='PASS_PINNED_PROGRAM_REPLAY', cases=len(cases), subjects=len(methods),
        actual_replay_parser_calls=calls, historical_fault_families=2, new_faults_discovered=0,
        model_calls=0, human_reference_validated=False,
        timing_reproduced=False, budget_curve_independently_replayed=False,
        limitation='Checks actual parser outputs and attribution against authored requirements; not unseen-fault discovery or A superiority')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    print(json.dumps(verify(parser.parse_args().folder), indent=2))
