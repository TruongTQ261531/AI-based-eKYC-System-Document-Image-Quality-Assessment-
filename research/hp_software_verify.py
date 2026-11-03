"""Verify saved software-test evidence and local health; does not run models."""
import datetime
import json
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

from research.hp_common import ROOT, CACHE, OUT, read, save, sha, signature, preserve


def suite(name):
    value = ET.parse(CACHE / name).getroot().find('testsuite')
    result = {k: int(value.attrib[k]) for k in ('tests', 'failures', 'errors', 'skipped')}
    if result['failures'] or result['errors']:
        raise ValueError('Failed software checks: ' + name)
    return result


def log(name):
    return (CACHE / name).read_text(encoding='utf-8-sig')


def node(name):
    text = log(name)
    value = {k: int(re.search(r'\b' + k + r'\s+(\d+)', text)[1])
             for k in ('tests', 'pass', 'fail', 'cancelled', 'skipped')}
    if value['fail'] or value['cancelled'] or value['skipped'] or value['pass'] != value['tests']:
        raise ValueError('Incomplete frontend checks: ' + name)
    return value


def verify():
    audit = read(OUT / 'audit.json')
    if read(CACHE / 'workflow.json')['stage'] != 'complete' or audit['status'] != 'passed':
        raise ValueError('Completed study audit required')
    if audit['signature'] != signature():
        raise ValueError('Study contract changed')
    frozen = preserve()
    main = suite('final_regression.xml')
    optional = suite('optional_training_tests.xml')
    match = re.search(r'(\d+) passed, (\d+) skipped, (\d+) warning, (\d+) subtests passed',
                      log('final_regression.log'))
    if not match:
        raise ValueError('Main pytest summary missing')
    passed, skipped, warnings, subtests = map(int, match.groups())
    if main['tests'] != passed + skipped + subtests or main['skipped'] != skipped:
        raise ValueError('Main JUnit/summary mismatch')
    if optional['tests'] != skipped or optional['skipped']:
        raise ValueError('Optional training checks did not cover all skipped checks')
    if not re.search(r'\b' + str(optional['tests']) + r' passed\b', log('optional_training_tests.log')):
        raise ValueError('Optional pytest summary missing')
    primary = node('frontend_primary.log')
    variant = node('frontend_source_variant.log')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    services = {}
    evidence = ['final_regression.xml', 'final_regression.log',
                'optional_training_tests.xml', 'optional_training_tests.log',
                'frontend_primary.log', 'frontend_source_variant.log']
    for port in (8000, 8003):
        with opener.open(f'http://127.0.0.1:{port}/api/health', timeout=15) as response:
            if response.status != 200:
                raise ValueError('Local service not healthy')
            payload = response.read()
        name = f'final_health_{port}.json'
        (CACHE / name).write_bytes(payload)
        evidence.append(name)
        services[port] = json.loads(payload)
    if services[8000].get('status') != 'ready' or services[8000].get('api_version') != '3.2.0':
        raise ValueError('Mentor service differs')
    if services[8003].get('app_id') != 'source_visibility_v3' or not services[8003].get('ready'):
        raise ValueError('Existing research service not restored')
    if services[8003].get('model') != 'partial_42':
        raise ValueError('Existing development-selected web model changed')
    record = dict(
        verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        signature=signature(), study_audit_sha256=sha(OUT / 'audit.json'),
        verifier_source_sha256=sha(ROOT / 'research/hp_software_verify.py'),
        tested_base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
        python_main_passed=passed, python_main_skipped_optional_training=skipped,
        optional_training_overlay_passed=optional['tests'],
        combined_unique_python_checks_passed=passed + optional['tests'],
        subtests_passed=subtests, main_junit=main, optional_junit=optional,
        main_warning_count=warnings,
        existing_warning='StarletteDeprecationWarning: httpx TestClient integration',
        new_dependencies_installed=False, frontend_primary=primary, frontend_source_variant=variant,
        frontend_behavior_checks_passed=primary['pass'] + variant['pass'],
        services=dict(mentor=dict(url='http://127.0.0.1:8000/', status=services[8000]['status'],
                                  api_version=services[8000]['api_version']),
                      research=dict(url='http://127.0.0.1:8003/', ready=services[8003]['ready'],
                                    app_id=services[8003]['app_id'], model=services[8003]['model'],
                                    recommended=services[8003]['recommended'],
                                    health_progress_scope='Existing V3 study, not new hard-pair runs')),
        new_hard_pair_model_promoted=False, physical_camera_validation=False,
        human_legibility_annotations=0, frozen_V1_files=frozen[0], frozen_V4_files=frozen[1],
        evidence=[dict(file=(CACHE / name).relative_to(ROOT).as_posix(), sha256=sha(CACHE / name))
                  for name in evidence])
    save(OUT / 'software_verification.json', record)
    print('HP_SOFTWARE_VERIFIED', record['combined_unique_python_checks_passed'], subtests,
          record['frontend_behavior_checks_passed'], flush=True)


if __name__ == '__main__':
    verify()
