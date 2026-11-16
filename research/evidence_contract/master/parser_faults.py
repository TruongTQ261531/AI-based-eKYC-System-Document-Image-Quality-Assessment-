"""Actual historical parser executions on authored OCR tokens, not OCR accuracy.

The two faults were known before this post-fix development experiment. Exact
single-patch reversions localize them; examples/variants are not new defects.
No predictor, human-label generator, or frozen research oracle is modified.
"""
from collections import Counter
from copy import deepcopy
import ast
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
import statistics
import subprocess
import time
from types import ModuleType

from ..task55.data import EC, ROOT, digest, read, save_new, sha

OUT = EC / 'execution/master_01/readiness_20261116'
ARCHIVE = ROOT / 'engineering/application_20261114/source'
BEFORE_COMMIT = '4110f22'
BEFORE_SHA = 'cca292ef3a12a96757bb9b912a261d1dd591f5f8110e72da7c299183f39b9431'
FIXED_SHA = '3f10617d53a5e11b4f2541a3d2ef63504a38c979cb3cc79256b56524317c0e62'
PATCHES = {
    'custom_single_character': (r"custom=re.match(r'^([^:：]{2,60})[:：]\s*(\S.+)$',text)",
                                r"custom=re.match(r'^([^:：]{2,60})[:：]\s*(\S.*)$',text)"),
    'conflicting_scalar_name': ("if key in ('address','hometown','full_name'): fields[key]=' '.join(parts)",
                                "if key in ('address','hometown'): fields[key]=' '.join(parts)"),
}


def load_source(payload, name):
    module = ModuleType(name)
    module.__file__ = name
    exec(compile(payload, name, 'exec'), module.__dict__)
    return module


def subject_sources():
    """Bind historical source to Git, fixed source to the archived application."""
    before = subprocess.check_output(['git', 'show', BEFORE_COMMIT + ':ekyc/document_fields.py'], cwd=ROOT)
    fixed = (ARCHIVE / 'ekyc/document_fields.py').read_bytes()
    if hashlib.sha256(before).hexdigest() != BEFORE_SHA or hashlib.sha256(fixed).hexdigest() != FIXED_SHA:
        raise ValueError('Historical/fixed subject bytes do not match the declared artifacts')
    result = dict(before=before, fixed=fixed)
    text = fixed.decode('utf-8')
    both = text
    for family, (old, new) in PATCHES.items():
        if text.count(new) != 1 or old in text:
            raise ValueError('Patch is not uniquely reversible: ' + family)
        result['revert_' + family] = text.replace(new, old).encode('utf-8')
        both = both.replace(new, old)
    # Comments/line endings may differ, but the two changes must explain all code.
    if ast.dump(ast.parse(both)) != ast.dump(ast.parse(before)):
        raise ValueError('Two reversions do not recover the historical program AST')
    result['revert_both'] = both.encode('utf-8')
    return result


def archived_matrix():
    spec = importlib.util.spec_from_file_location('archived_parser_regression', ARCHIVE / 'scripts/audit_field_extraction.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cases_from_plan(plan):
    factors = plan['experiments']['input_factors']
    cases = []
    def add(kind, texts, *, fields=None, absent=None, items=None, specialized=None, family=None, factors=None):
        cases.append(dict(case_id=f'{kind}/{sum(c["kind"] == kind for c in cases):03d}', kind=kind,
            texts=texts, specialized=specialized or {}, required_fields=fields or {},
            absent_fields=absent or [], required_items=items or {},
            require_empty_fields=not fields and not items, known_fault_family=family,
            factors=factors or {}, input_origin='authored_ocr_tokens'))
    def noise(count):
        return ['TÀI LIỆU THỬ', 'MẪU MINH HỌA'][:count]
    for pair, label, order, guess, count in itertools.product(
            itertools.combinations(factors['names'], 2), factors['name_labels'],
            factors['conflict_orders'], factors['specialized_guess'], factors['noise_rows']):
        left, right = pair if order == 'forward' else pair[::-1]
        add('conflicting_name', noise(count) + [label + ': ' + left, label + ': ' + right],
            absent=['full_name'], specialized={'full_name': left} if guess else {},
            family='conflicting_scalar_name', factors=dict(label=label, order=order, guess=guess, noise=count))
    for label, separator, value, count in itertools.product(factors['custom_labels'], factors['separators'],
                                                           factors['custom_values'], factors['custom_noise_rows']):
        add('single_character', noise(count) + [label + separator + ' ' + value], items={label: value},
            family='custom_single_character', factors=dict(label=label, separator=separator, value=value, noise=count))
    for name, label, count in itertools.product(factors['names'], factors['name_labels'], factors['noise_rows']):
        other = next(value for value in factors['name_labels'] if value != label)
        add('same_name', noise(count) + [label + ': ' + name, other + ': ' + name], fields={'full_name': name})
    for name, label in itertools.product(factors['names'], factors['name_labels']):
        add('split_name', [label + ':', name], fields={'full_name': name})
    for label, separator, value, count in itertools.product(factors['custom_labels'], factors['separators'],
                                                           ['AB', 'Đ7'], factors['custom_noise_rows']):
        add('multi_character', noise(count) + [label + separator + ' ' + value], items={label: value})
    for case in archived_matrix().CASES:
        family = ('conflicting_scalar_name' if case['case'].startswith('conflicting_names') else
                  'custom_single_character' if case['case'] in ('one_character_custom_value', 'fullwidth_colon_custom_value') else None)
        add('original_matrix', case['text'], fields=case['fields'], absent=case['absent'],
            items=case.get('labelled_items'), specialized=case.get('specialized'), family=family,
            factors=dict(original_case=case['case']))
    for case in cases:
        case['input_sha256'] = digest(dict(texts=case['texts'], specialized=case['specialized']))
        case['requirement_sha256'] = digest({key: case[key] for key in
            ('required_fields', 'absent_fields', 'required_items', 'require_empty_fields')})
    return cases


def execute(module, case):
    tokens = [dict(text=text, confidence=.99, source='authored_regression_tokens',
                   box=[[0, n * 25], [600, n * 25], [600, n * 25 + 18], [0, n * 25 + 18]])
              for n, text in enumerate(case['texts'])]
    fields, items, kind = module.observed_information(tokens, dict(case['specialized']))
    labelled = {item['label']: item['value'] for item in items}
    failures = ['field_value:' + key for key, value in case['required_fields'].items() if fields.get(key) != value]
    failures += ['unexpected_field:' + key for key in case['absent_fields'] if key in fields]
    failures += ['labelled_value:' + key for key, value in case['required_items'].items() if labelled.get(key) != value]
    if case['require_empty_fields'] and fields:
        failures.append('unexpected_observed_fields')
    return dict(passed=not failures, failures=failures, fields=fields, labelled_items=labelled, document_type=kind['key'])


def ddmin(items, predicate):
    """Complement-based delta debugging; 1-minimal, not globally smallest."""
    current = list(items)
    if not predicate(current):
        raise ValueError('Initial input does not reproduce the failure')
    n = 2
    while len(current) >= 2:
        size = (len(current) + n - 1) // n
        for start in range(0, len(current), size):
            candidate = current[:start] + current[start + size:]
            if predicate(candidate):
                current = candidate
                n = max(2, n - 1)
                break
        else:
            if n >= len(current):
                break
            n = min(len(current), n * 2)
    return current


def minimize(case, subjects):
    family = case['known_fault_family']
    # The requirement is applicable only while its decisive labelled rows remain.
    required = [text for text in case['texts'] if text not in ('TÀI LIỆU THỬ', 'MẪU MINH HỌA')]
    trace = []
    def predicate(texts):
        if any(text not in texts for text in required):
            trace.append(dict(texts=texts, outcome='UNRESOLVED_REQUIREMENT_PRECONDITION', parser_calls=0))
            return False
        modified = dict(case, texts=texts)
        measured = {name: execute(subjects[name], modified) for name in ('before', 'fixed', 'revert_' + family)}
        reproduces = (not measured['before']['passed'] and measured['fixed']['passed']
                      and not measured['revert_' + family]['passed'])
        trace.append(dict(texts=texts, outcome='FAILURE_REPRODUCED' if reproduces else 'NOT_REPRODUCED',
                          parser_calls=3, measured=measured))
        return reproduces
    minimal = ddmin(case['texts'], predicate)
    if not predicate(minimal):
        raise ValueError('Minimized witness no longer reproduces')
    checks = [predicate(minimal[:i] + minimal[i + 1:]) for i in range(len(minimal))]
    if any(checks):
        raise ValueError('Witness is not 1-minimal')
    return dict(family=family, original_case=case['case_id'], original_rows=len(case['texts']),
        minimal_texts=minimal, specialized=case['specialized'], one_minimal_under_requirement=True,
        granularity='whole OCR text rows; fixed requirement precondition; not character/global minimality',
        parser_calls=sum(row['parser_calls'] for row in trace), trace=trace)


def family_curve(cases, rows, permutations):
    """Development-only finite-pool budget comparison; no power/CI claim."""
    unique = {}
    for case, row in zip(cases, rows):
        identity = case['input_sha256']
        family = case['known_fault_family'] if not row['outputs']['before']['passed'] and row['outputs']['fixed']['passed'] else None
        if identity in unique and unique[identity][1] != family:
            raise ValueError('Duplicate input has conflicting fault-family expectation')
        unique[identity] = (case, family)
    pool = list(unique.values())
    budgets = [value for value in (1, 2, 5, 10, 20, 50, len(pool)) if value <= len(pool)]
    policies = {name: {budget: [] for budget in budgets} for name in ('uniform_random', 'input_kind_round_robin')}
    for seed in range(permutations):
        rng = random.Random(seed)
        random_order = list(range(len(pool)))
        rng.shuffle(random_order)
        groups = {}
        for index, (case, _) in enumerate(pool):
            # Input kind is authored before execution. Family/outcome is not read here.
            groups.setdefault(case['kind'], []).append(index)
        for group in groups.values():
            rng.shuffle(group)
        keys = list(groups)
        rng.shuffle(keys)
        stratified = []
        while any(groups.values()):
            for key in keys:
                if groups[key]:
                    stratified.append(groups[key].pop())
        for name, order in (('uniform_random', random_order), ('input_kind_round_robin', stratified)):
            for budget in budgets:
                policies[name][budget].append(len({pool[index][1] for index in order[:budget]} - {None}))
    return dict(unique_inputs=len(pool), permutations=permutations, independent_fault_families=2,
        caveat='Pool and input kinds were designed after the two defects were known. This is not unbiased discovery performance.',
        budget_unit='one authored token input executed against one subject; no model cost',
        policies={name: {str(budget): dict(mean_families=statistics.mean(values),
                    found_both_fraction=sum(v == 2 for v in values) / len(values),
                    minimum=min(values), maximum=max(values)) for budget, values in counts.items()}
                  for name, counts in policies.items()})


def run(folder):
    folder = Path(folder)
    if folder.exists():
        raise FileExistsError('Use a fresh execution directory')
    plan = read(OUT / 'plan.json')
    sources = subject_sources()
    subjects = {name: load_source(payload, name) for name, payload in sources.items()}
    cases = cases_from_plan(plan)
    rows = [dict(case_id=case['case_id'], outputs={name: execute(module, case) for name, module in subjects.items()}) for case in cases]
    # Any unexpected failure remains visible and stops a success claim.
    unexpected = [row['case_id'] for case, row in zip(cases, rows)
                  if not row['outputs']['fixed']['passed'] or (case['known_fault_family'] is None
                                                              and not all(r['passed'] for r in row['outputs'].values()))]
    faults = {}
    for family in PATCHES:
        selected = [(case, row) for case, row in zip(cases, rows) if case['known_fault_family'] == family]
        other = next(value for value in PATCHES if value != family)
        clean_witness = all(not row['outputs']['before']['passed'] and row['outputs']['fixed']['passed']
            and not row['outputs']['revert_' + family]['passed'] and row['outputs']['revert_' + other]['passed']
            and not row['outputs']['revert_both']['passed'] for _, row in selected)
        faults[family] = dict(authored_variants=len(selected), independent_faults=1, all_fix_revert_witnesses=clean_witness)
    witnesses = [minimize(next(case for case in cases if case['known_fault_family'] == family
                              and case.get('factors', {}).get('noise') == 2 and not case['specialized']), subjects)
                 for family in PATCHES]
    latency = {}
    for name, module in subjects.items():
        samples = []
        for _ in range(plan['budgets']['latency_repeats']):
            started = time.perf_counter_ns()
            for case in cases:
                execute(module, case)
            samples.append((time.perf_counter_ns() - started) / 1e6)
        latency[name] = dict(batch_milliseconds=samples, cases_per_batch=len(cases),
            median_batch_ms=statistics.median(samples), p95_batch_ms=sorted(samples)[int(.95 * (len(samples) - 1))],
            includes='token construction, parser and expected-value comparisons; warm process; sequential subjects',
            excludes='OCR/model loading, annotation, human triage; not an end-to-end performance comparison')
    report = dict(schema='historical-parser-development/1', scope='KNOWN_FAULT_POST_FIX_DEVELOPMENT',
        confirmatory=False, new_faults_discovered=0, historical_fault_families=2,
        human_labels_created=0, model_calls=0, training_steps=0,
        output_origin='actual_parser_execution_on_authored_ocr_tokens',
        requirement_origin='Author-written requirements, selected after known fixes; no external gold',
        frozen_A_evaluated=False, frozen_A_changed=False,
        source_before_commit=BEFORE_COMMIT, sources_sha256={name: hashlib.sha256(value).hexdigest() for name, value in sources.items()},
        module_sha256=sha(Path(__file__)), plan_sha256=sha(OUT / 'plan.json'),
        cases=len(cases), unique_inputs=len({case['input_sha256'] for case in cases}),
        cases_sha256=digest(cases), outputs_sha256=digest(rows),
        method_totals={name: dict(passed=sum(row['outputs'][name]['passed'] for row in rows), total=len(rows)) for name in subjects},
        per_kind={kind: {name: dict(passed=sum(row['outputs'][name]['passed'] for case, row in zip(cases, rows) if case['kind'] == kind),
                                    total=sum(case['kind'] == kind for case in cases)) for name in subjects}
                  for kind in sorted({case['kind'] for case in cases})},
        historical_faults=faults, unexpected_cases=unexpected,
        delta_debugging=witnesses, budget_curves=family_curve(cases, rows, plan['budgets']['budget_curve_permutations']),
        latency=latency, statistical_inference='NONE: two selected fault families, correlated input variants, no unseen holdout',
        parser_executions=dict(matrix=len(cases) * len(subjects),
            delta_debugging=sum(w['parser_calls'] for w in witnesses),
            timing=len(cases) * len(subjects) * plan['budgets']['latency_repeats']))
    report['status'] = ('PASS_KNOWN_FAULT_REPRODUCTION' if not unexpected and all(f['all_fix_revert_witnesses'] for f in faults.values())
                        else 'UNEXPECTED_OUTCOME_REQUIRES_ANALYSIS')
    save_new(folder / 'cases.json', cases)
    save_new(folder / 'outputs.json', rows)
    for name, payload in sources.items():
        path = folder / 'subjects' / (name + '.py')
        path.parent.mkdir(exist_ok=True)
        with path.open('xb') as stream:
            stream.write(payload)
    save_new(folder / 'results.json', report)
    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = run(parser.parse_args().output)
    print(json.dumps({key: result[key] for key in ('status', 'cases', 'unique_inputs', 'method_totals',
        'historical_faults', 'unexpected_cases', 'parser_executions')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] == 'PASS_KNOWN_FAULT_REPRODUCTION' else 1)
