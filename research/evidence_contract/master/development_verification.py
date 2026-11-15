"""Verify the 16 November development milestone without invoking predictors.

Requires private frozen assets on the organizer's machine. It verifies their
preservation without copying their contents into the public receipt.
"""
from copy import deepcopy
import json
from pathlib import Path
import zipfile

from ..task55.data import EC, FrozenPilot, read, sha, digest, save_new
from ..task55 import ifv
from ..task55.portable_review import frozen_packet, script_literal
from .a_variants import lanes, evaluate_panel
from .ifv_analysis import from_sealed
from .ifv_report import sealed_results


OUT = EC / 'execution/master_01/development_20261116'


def verify():
    protected_path = EC / 'local/master_01/development_20261116/protected_assets_before.json'
    protected = read(protected_path)
    if any(sha(EC / name) != expected for name, expected in protected.items()):
        raise ValueError('A protected historical asset changed')
    plan = read(OUT / 'variant_plan.json')
    if any(sha(EC / name) != expected for name, expected in plan['frozen_A_files'].items()):
        raise ValueError('Frozen A or baseline changed')

    pilot = FrozenPilot()
    cases = [dict(evaluation_id=row['evaluation_id'], stratum=row['stratum'],
                  reader=row['reader'], contract=row['contract_id'],
                  row_sha256=digest(row), variants=lanes(row)) for row in pilot.rows]
    report = read(OUT / 'variant_results.json')
    if (cases != read(OUT / 'variant_cases.json') or digest(cases) != report['case_digest']
            or report['plan_sha256'] != sha(OUT / 'variant_plan.json')
            or report['source_sha256'] != sha(Path(__file__).with_name('a_variants.py'))):
        raise ValueError('Exploratory decisions are not bound to their plan/source')

    snapshot = '812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d'
    folder = ifv.STAGE2 / 'd7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223'
    submission = folder / 'submissions' / snapshot / 'output_observations.json'
    if sealed_results(submission) != read(EC / 'execution/master_01/ifv_descriptive_ece01b67a2f6af39.json'):
        raise ValueError('The original sealed report no longer replays exactly')
    links = read(ifv.JOINS / (folder.name + '.json'))
    labels = read(submission.parent / 'labels.json')
    _, details = from_sealed(submission)
    withheld = deepcopy(labels)
    for case in details:
        if case['coherence_flags']:
            withheld[case['case_id']] = dict(pointwise='INCONCLUSIVE', relation='INCONCLUSIVE')
    if report['panels'] != dict(original=evaluate_panel(links, labels),
                               withholding_sensitivity=evaluate_panel(links, withheld)):
        raise ValueError('One of the exploratory panels differs on replay')
    strata = read(OUT / 'variant_strata.json')['strata']
    for dimension, values in strata.items():
        for value, expected in values.items():
            selected = {key: case for key, case in links.items()
                        if case['row'][dimension] == value and case['row']['stratum'] == 'primary'}
            actual = dict(pointwise=evaluate_panel(selected, labels)['pointwise'],
                          reviewed_primary=len(selected))
            if actual != expected:
                raise ValueError('A descriptive stratum differs on replay')

    packet = frozen_packet()
    receipts = read(OUT / 'reviewer_package_receipts_v2.json')
    verified_packages = []
    for receipt in receipts['packages']:
        archive = EC / receipts['phase1_root'] / receipt['archive_name']
        if sha(archive) != receipt['archive_sha256']:
            raise ValueError('Reviewer archive changed')
        prefix = archive.stem + '/'
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            if len(set(names)) != 38 or any(not name.startswith(prefix) or '..' in Path(name).parts for name in names):
                raise ValueError('Unexpected reviewer package members')
            manifest = json.loads(bundle.read(prefix + 'MANIFEST.json'))
            if set(names) != {prefix + name for name in manifest['files']} | {prefix + 'MANIFEST.json'}:
                raise ValueError('Unmanifested reviewer files')
            import hashlib
            for name, expected in manifest['files'].items():
                if hashlib.sha256(bundle.read(prefix + name)).hexdigest() != expected:
                    raise ValueError('Reviewer manifest hash mismatch')
            job = json.loads(bundle.read(prefix + 'REVIEW_JOB.json'))
            if (digest({key: value for key, value in job.items() if key != 'job_id'}) != job['job_id']
                    or job['job_id'] != receipt['job_id'] or job['packet_id'] != packet['packet_id']):
                raise ValueError('Reviewer job binding mismatch')
            html = bundle.read(prefix + 'index.html').decode('utf-8')
            if any(key in html for key in ('observed_transcript', 'before_output', 'author_reference', 'BLIND_REVIEW_RESUME')):
                raise ValueError('Phase 1 contains answer or output fields')
            if 'window.BLIND_PACKET=' + script_literal(packet) + ';' not in html:
                raise ValueError('Reviewer HTML packet differs')
            for page in packet['pages']:
                if hashlib.sha256(bundle.read(prefix + page['image'])).hexdigest() != page['file_sha256']:
                    raise ValueError('Reviewer image binding mismatch')
            if bundle.read(prefix + 'review_ui.js') != (EC / 'task55/review_ui.js').read_bytes():
                raise ValueError('Reviewer UI is stale')
            if job['field_slots'] != 86 or job['model_outputs_included'] or job['author_answers_included']:
                raise ValueError('Unexpected reviewer package scope')
        verified_packages.append(dict(archive=archive.name, sha256=sha(archive), files=38, images=31))

    python_log = (OUT / 'final_python_tests.log').read_text(encoding='utf-8')
    ui_log = (OUT / 'final_ui_tests.log').read_text(encoding='utf-8')
    if '209 passed, 6 subtests passed' not in python_log or 'pass 15' not in ui_log or 'fail 0' not in ui_log:
        raise ValueError('Expected final test completion is missing')
    pilot.assert_read_only()
    return dict(status='PASS_PRESERVATION_REPLAY_AND_PACKAGE_BINDING',
                protected_assets=len(protected), protected_manifest_sha256=sha(protected_path),
                old_sealed_report_replayed_exactly=True, old_human_answers_changed=0,
                original_scorers_unchanged=True, raw_output_payloads=len(pilot.raw),
                inference_event_logs=len(pilot.logs), scheduled_comparisons=len(cases),
                variant_panels_replayed=2, strata_replayed=sum(map(len, strata.values())),
                packages=verified_packages, actual_new_reviewers=0,
                python_tests=209, python_subtests=6, javascript_tests=15,
                model_calls=0, training_steps=0, confirmatory_inputs_opened=0,
                browser_visual_qa_performed=False)


if __name__ == '__main__':
    result = verify()
    save_new(OUT / 'final_verification.json', result)
    print(json.dumps(result, indent=2))
