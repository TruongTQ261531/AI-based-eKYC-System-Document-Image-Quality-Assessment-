"""Validate issued ZIP + export, or quarantine exact bytes. Never creates labels.

The organizer supplies the expected ZIP hash and assigned reviewer separately.
Issued phase-2 exports lack a reviewer field: binding uses their unique sealed
phase-1 snapshot. This cannot authenticate the person operating someone else's ZIP.
"""
import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

from .strict import bound, canonical, digest, exact, loads, need, sha_bytes, sha_value, text, timestamp
from ..task55.data import EC, save_new
from ..task55 import review, ifv

PHASE1_TOP = {'schema', 'packet_id', 'packet_purpose', 'mode', 'export_kind', 'exported_at',
              'reviewer', 'review_state', 'items', 'no_model_outputs_shown_by_packet', 'no_expected_values_shown_by_packet'}
ITEM1 = {'slot_id', 'image_id', 'image_sha256', 'field_key', 'touched', 'availability', 'readability',
         'semantic_key_confirmed', 'observed_transcript', 'sources', 'notes', 'prior_exposure', 'entry_complete'}
SOURCE = {'kind', 'location', 'availability', 'readability', 'observed_text', 'mrz_line_1', 'mrz_line_2'}
ITEM2 = {'case_id', 'test_validity', 'absence_check', 'reason', 'first_reveal_at', 'before_reading', 'after_reading', 'output_note'}


def package(path, expected_sha, expected_reviewer):
    raw = Path(path).read_bytes()
    need(sha_bytes(raw) == sha_value(expected_sha), 'Issued ZIP hash mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)) and len(names) <= 2000, 'Duplicate/oversized ZIP')
        need(sum(x.file_size for x in archive.infolist()) <= 50000000, 'ZIP size limit')
        for name in names:
            parts = PurePosixPath(name).parts
            need(not name.startswith('/') and '..' not in parts and '\\' not in name and ':' not in name,
                 'Unsafe ZIP member')
        roots = {PurePosixPath(n).parts[0] for n in names}
        need(len(roots) == 1, 'Expected one package root')
        prefix = next(iter(roots)) + '/'
        files = {name[len(prefix):]: archive.read(name) for name in names if not name.endswith('/')}
    manifest = loads(files['MANIFEST.json'])
    exact(manifest, {'schema', 'job', 'files'})
    need(manifest['schema'] == 'portable-review-package/1', 'Package schema')
    need(isinstance(manifest['files'], dict) and set(files) == set(manifest['files']) | {'MANIFEST.json'}, 'Package file inventory')
    for name, expected in manifest['files'].items():
        need(sha_bytes(files[name]) == sha_value(expected), 'Package file changed')
    job = loads(files['REVIEW_JOB.json']); bound(job, 'job_id')
    need(job['schema'] == 'reviewer-job/1' and job['job_id'] == manifest['job'], 'Job binding')
    need(job['reviewer_id'] == expected_reviewer, 'Wrong assigned reviewer package')
    need(job['author_answers_included'] is False, 'Author answers must not be in issued package')
    if job['phase'] == 'phase1':
        packet = loads(files['packet_manifest.json']); bound(packet, 'packet_id')
        need(packet['packet_id'] == job['packet_id'], 'Phase-1 packet binding')
        for page in packet['pages']:
            need(sha_bytes(files[page['image']]) == page['file_sha256'], 'Image binding')
    elif job['phase'] == 'phase2':
        pages = [v for k, v in files.items() if k.endswith('index.html') and b'window.OUTPUT_PACKET=' in v]
        need(len(pages) == 1, 'Missing/duplicate phase-2 packet')
        payload = pages[0].split(b'window.OUTPUT_PACKET=', 1)[1].split(b'</script>', 1)[0].strip()
        packet = loads(payload.removesuffix(b';'), max_bytes=10000000)
        need(digest(packet) == job['portable_view_sha256'], 'Portable view binding')
        need(packet['packet_id'] == job['canonical_packet_id'] and packet['phase1_snapshot'] == job['phase1_snapshot'], 'Phase-2 binding')
        need(all('author_reference' not in c for c in packet['cases']), 'Author hint leaked')
    else:
        raise ValueError('Unknown phase')
    return dict(job=job, packet=packet, archive_sha256=expected_sha)


def validate(raw, bundle, *, phase1_seal=None, synthetic=False):
    value = loads(raw); job = bundle['job']; packet = bundle['packet']
    need(isinstance(value, dict), 'Expected review object')
    expected_mode = 'unit_injected' if synthetic else 'human_entered'
    need(value.get('mode') == expected_mode, 'Synthetic and human evidence must stay separate')
    need(not synthetic or job['reviewer_id'].startswith('SYNTHETIC_'), 'Synthetic identity required')
    need(value.get('export_kind') == 'reviewed_observations', 'Draft cannot be ingested')
    timestamp(value.get('exported_at'))
    need(isinstance(value.get('items'), list) and value['items'], 'Empty observations')
    need(value.get('packet_id') == packet['packet_id'], 'Wrong packet ID')
    if job['phase'] == 'phase1':
        exact(value, PHASE1_TOP)
        exact(value['reviewer'], {'reviewer_id', 'role', 'output_exposure', 'independence_verified'})
        need(value['reviewer']['reviewer_id'] == job['reviewer_id'], 'Wrong reviewer export')
        need(value['no_model_outputs_shown_by_packet'] is True and value['no_expected_values_shown_by_packet'] is True, 'Blind packet declarations')
        need(value['review_state'] in ('complete', 'partial'), 'Review state')
        for item in value['items']:
            exact(item, ITEM1)
            need(item['touched'] is True and item['entry_complete'] is True, 'Incomplete/default item')
            need(isinstance(item['sources'], list), 'Source list')
            for source in item['sources']:
                exact(source, SOURCE)
                for entry in source.values(): text(entry)
            for key in ITEM1 - {'sources', 'touched', 'entry_complete'}: text(item[key])
        result = review.validate_export(value, packet, allow_unit=synthetic)
        need(result['incomplete_observations'] == 0, 'Invalid enum or incomplete item')
        total = sum(len(p['fields']) for p in packet['pages'])
        need((value['review_state'] == 'complete') == (len(value['items']) == total), 'Completion declaration mismatch')
    else:
        exact(value, {'schema', 'mode', 'packet_id', 'phase1_snapshot', 'export_kind', 'exported_at', 'items'})
        need(value['schema'] == 'ifv-output-observations/1', 'Phase-2 schema')
        need(isinstance(phase1_seal, dict), 'Phase 1 must be sealed first')
        need(phase1_seal.get('snapshot_id') == job['phase1_snapshot'] == value['phase1_snapshot'], 'Phase order/snapshot binding')
        need(phase1_seal.get('reviewer_id') == job['reviewer_id'] and phase1_seal.get('complete') is True, 'Own complete phase 1 required')
        cases = {c['case_id'] for c in packet['cases']}; seen = set()
        for item in value['items']:
            exact(item, ITEM2)
            for entry in item.values(): text(entry)
            need(item['case_id'] in cases and item['case_id'] not in seen, 'Unknown/duplicate case')
            seen.add(item['case_id'])
            need(item['test_validity'] in ('valid', 'invalid', 'uncertain'), 'Validity enum')
            need(item['before_reading'] in ifv.READINGS and item['after_reading'] in ifv.READINGS, 'Reading enum')
            need(item['absence_check'] in ('all_sources_removed', 'not_established', 'not_applicable'), 'Absence enum')
            text(item['reason'], nonempty=True); timestamp(item['first_reveal_at'])
            if item['after_reading'] in ('wrong_value', 'readable_omission', 'unsupported_verified'):
                text(item['output_note'], nonempty=True)
        total = len(cases)
    return value, dict(schema='strict-review-validation/1', phase=job['phase'], raw_sha256=sha_bytes(raw),
        normalized_sha256=digest(value), package_sha256=bundle['archive_sha256'], job_id=job['job_id'],
        observations=len(value['items']), expected_observations=total, missing=total-len(value['items']),
        complete=len(value['items']) == total, origin='SYNTHETIC' if synthetic else 'HUMAN_SUBMITTED_UNVERIFIED',
        gold_created=False, independent_truth_verified=False)


def quarantine(raw, bundle, destination, *, phase1_seal=None, synthetic=False, dry_run=True, legacy_digests=frozenset()):
    value, result = validate(raw, bundle, phase1_seal=phase1_seal, synthetic=synthetic)
    root = Path(destination).resolve()
    need(root.is_relative_to((EC/'local').resolve()), 'Intake stays private under local/')
    folder = root/result['normalized_sha256']
    need(result['normalized_sha256'] not in legacy_digests and not folder.exists(), 'Already ingested (including reformatted export)')
    if dry_run:
        return dict(result, status='VALIDATED_DRY_RUN', writes=0)
    root.mkdir(parents=True, exist_ok=True); folder.mkdir()
    with (folder/'raw.json').open('xb') as stream: stream.write(raw)
    save_new(folder/'normalized.json', value)
    save_new(folder/'receipt.json', dict(result, received_at=datetime.now(timezone.utc).isoformat(),
        state='QUARANTINED_NO_SCIENTIFIC_LABELS', raw_bytes_preserved=True))
    return dict(result, status='QUARANTINED_NO_SCIENTIFIC_LABELS', writes=3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('validate-review', 'ingest-review'))
    parser.add_argument('submission', type=Path)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--package-sha256', required=True)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    bundle = package(args.package, args.package_sha256, args.reviewer)
    seal = None
    if bundle['job']['phase'] == 'phase2':
        sid = bundle['job']['phase1_snapshot']
        _, validation, profile = ifv.sealed_phase1(sid)
        seal = dict(snapshot_id=sid, reviewer_id=profile['reviewer_id'], complete=validation['missing_slots'] == validation['incomplete_observations'] == 0)
    old = set()
    for root in (ifv.SUBMISSIONS, ifv.STAGE2):
        for name in ('observations.json', 'output_observations.json'):
            for path in root.rglob(name): old.add(digest(loads(path.read_bytes())))
    result = quarantine(args.submission.read_bytes(), bundle, EC/'local/reviewer_intake_v2', phase1_seal=seal,
                        dry_run=args.dry_run or args.action == 'validate-review', legacy_digests=old)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
