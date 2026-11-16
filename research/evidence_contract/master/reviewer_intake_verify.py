"""Read-only replay of R02 intake; requires organizer-private evidence.

Prints aggregate checks only. It neither adjudicates answers nor certifies
independence. The role correction remains separate from the original export.
"""
from collections import Counter
import hashlib
import json
import re
import unicodedata
import zipfile

from ..task55 import agreement, ifv, portable_review
from ..task55.data import EC, FrozenPilot, digest, read, sha
from .ifv_report import sealed_results


RUN = 'reviewer_intake_20261116_r02'
PUBLIC = EC / 'execution/master_01' / RUN
PRIVATE = EC / 'local/master_01' / RUN


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    intake = read(PUBLIC / 'intake.json')
    snapshot = intake['phase1_snapshot']
    raw_path = PRIVATE / 'original_review_R02.json'
    raw = read(raw_path)
    require(sha(raw_path) == intake['source_file_sha256'], 'Raw file bytes changed')
    require(digest(raw) == snapshot, 'Raw snapshot changed')
    manifest, validation, reviewer = ifv.sealed_phase1(snapshot)
    require(read(ifv.SUBMISSIONS / snapshot / 'observations.json') == raw, 'Imported answers changed')
    require(validation['complete_observations'] == 86, 'Incomplete phase 1')
    correction = read(PUBLIC / 'role_correction.json')
    require(correction['observation_snapshot_sha256'] == snapshot
            and correction['submission_file_sha256'] == sha(raw_path)
            and reviewer['role'] == correction['raw_declared_role'] == 'project_author'
            and correction['effective_role'] == 'external_reviewer'
            and correction['reviewer_independence_verified'] is False,
            'Role correction lost its source binding or overstated independence')
    author = read(ifv.SUBMISSIONS / intake['author_phase1_snapshot'] / 'observations.json')
    metrics = agreement.compare([author, raw], manifest)
    require(metrics == read(PUBLIC / 'phase1_agreement_raw_roles.json'), 'Agreement replay differs')
    by_slot = {v['slot_id']: v for v in raw['items']}
    keys = ('availability', 'readability', 'semantic_key_confirmed')
    cross = {key: [dict(author=a, R02=b, count=n) for (a, b), n in sorted(Counter(
        (v[key], by_slot[v['slot_id']][key]) for v in author['items']).items())] for key in keys}
    require(cross == read(PUBLIC / 'phase1_contingencies.json')['rows'], 'Contingency counts differ')
    normalize = lambda s: ' '.join(unicodedata.normalize('NFC', s).casefold().split())
    disagreements = []; counts = Counter(); by_field = {}
    for a in author['items']:
        b = by_slot[a['slot_id']]
        flags = [key for key in keys if a[key] != b[key]]
        eligible = all(v['readability'] == 'readable' and v['semantic_key_confirmed'] == 'yes'
                       and v['observed_transcript'].strip() for v in (a, b))
        if eligible and normalize(a['observed_transcript']) != normalize(b['observed_transcript']):
            flags.append('readable_transcript')
        counts.update(flags)
        field = by_field.setdefault(a['field_key'], dict(slots=0, any_disagreement=0))
        field['slots'] += 1; field['any_disagreement'] += bool(flags)
        if flags:
            disagreements.append(dict(slot_id=a['slot_id'], image_id=a['image_id'],
                                      field_key=a['field_key'], dimensions=flags, author=a, R02=b))
    require(len(disagreements) == intake['phase1_disagreement_slots_any']
            and dict(counts) == intake['phase1_disagreement_counts_by_dimension']
            and by_field == intake['phase1_disagreement_by_field'], 'Disagreement counts differ')
    saved = read(PRIVATE / 'disagreements.json')['items']
    require({v['slot_id']: v for v in disagreements} == {v['slot_id']: v for v in saved},
            'Private disagreement inspection differs')

    folder = ifv.STAGE2 / digest(['reviewer-id/1', 'r02'])
    ifv.verify_publication(folder)
    packet = read(folder / 'packet.json')
    ifv.bound_manifest(packet, 'packet_id')
    seal = read(folder / 'evidence_seal.json')
    require(packet['phase1_snapshot'] == seal['phase1_snapshot'] == snapshot
            and seal['reviewer'] == raw['reviewer'], 'Phase 2 is not sealed to raw R02')
    links = read(ifv.JOINS / (folder.name + '.json'))
    selected = {c['identity_sha256']: c for c in read(ifv.SAMPLE)['frame'] if c['selected']}
    require({v['identity_sha256'] for v in links.values()} == set(selected)
            and all(v == selected[v['identity_sha256']] for v in links.values()), 'Sample changed')
    require(set(links) == {c['case_id'] for c in packet['cases']}, 'Case join differs')
    observations = {i['slot_id']: i for i in raw['items']}
    pilot = FrozenPilot()
    for case in packet['cases']:
        link = links[case['case_id']]
        require(case['case_id'] == 'CASE-' + digest([snapshot, link['identity_sha256']])[:16],
                'Case identity is not reviewer-bound')
        row = link['row']
        for side, pixel in [('before', 'original_pixel_sha256'), ('after', 'followup_pixel_sha256')]:
            evidence = case[side + '_evidence']
            require(evidence == observations[evidence['slot_id']], 'Evidence is not own phase 1')
            expected = ifv.cached_value(pilot.outputs[row['reader'], row[pixel]], row['field_key'])
            require(case[side + '_output'] == expected, 'Output differs from frozen cache')
    pilot.assert_read_only()

    bundle = EC / 'local/reviewer_exports/r02_20261116/reviewer_R02_phase2'
    receipt = read(PUBLIC / 'phase2_package_receipt.json')
    require(sha(bundle.with_suffix('.zip')) == receipt['archive_sha256'], 'ZIP hash differs')
    job = read(bundle / 'REVIEW_JOB.json')
    require(digest({k: v for k, v in job.items() if k != 'job_id'}) == job['job_id'] == receipt['job_id'],
            'Portable job hash differs')
    require(job['phase1_snapshot'] == snapshot and job['canonical_packet_id'] == packet['packet_id']
            and job['source_publication_sha256'] == sha(folder / 'publication.json'), 'Portable binding differs')
    file_manifest = read(bundle / 'MANIFEST.json')
    actual_names = {p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}
    require(actual_names == set(file_manifest['files']) | {'MANIFEST.json'}, 'Unexpected package files')
    with zipfile.ZipFile(bundle.with_suffix('.zip')) as archive:
        expected_names = {bundle.name + '/' + name for name in actual_names}
        require(len(archive.namelist()) == len(expected_names)
                and set(archive.namelist()) == expected_names, 'Unexpected ZIP members')
        for name in actual_names:
            payload = archive.read(bundle.name + '/' + name)
            require(payload == (bundle / name).read_bytes(), 'ZIP differs from package')
            if name != 'MANIFEST.json':
                require(hashlib.sha256(payload).hexdigest() == file_manifest['files'][name],
                        'Package member hash differs')
    page = bundle / 'reviews' / folder.name / 'index.html'
    html = page.read_text(encoding='utf-8')
    embedded = re.findall(r'<script>window\.OUTPUT_PACKET=(.*?);</script>', html, re.S)
    require(len(embedded) == 1 and 'author_reference' not in html, 'Unexpected portable payload')
    portable = json.loads(embedded[0])
    expected = dict(packet, cases=[{k: v for k, v in c.items() if k != 'author_reference'}
                                  for c in packet['cases']])
    require(portable == expected and digest(portable) == job['portable_view_sha256'],
            'Portable view is not exactly own sealed packet minus author hints')
    images = set()
    for case in portable['cases']:
        for side in ('before', 'after'):
            path = (page.parent / case[side + '_image']).resolve()
            require(path.is_relative_to(bundle.resolve()), 'Image outside portable bundle')
            require(sha(path) == case[side + '_evidence']['image_sha256'], 'Image binding differs')
            images.add(path)
    strata = Counter(v['row']['stratum'] for v in links.values())
    require(len(packet['cases']) == job['cases'] == 46 and strata['primary'] == 42
            and len(images) == job['image_count'] == 30, 'Package denominator changed')

    old_phase2 = (ifv.STAGE2 / 'd7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223'
                  / 'submissions/812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d'
                  / 'output_observations.json')
    require(sealed_results(old_phase2) == read(EC / 'execution/master_01/ifv_descriptive_ece01b67a2f6af39.json'),
            'Historical author report replay differs')
    protected = read(PRIVATE / 'protected_before.json')
    require(all(sha(EC / name) == expected for name, expected in protected.items()),
            'Historical protected file changed')
    return dict(status='PASS',raw_bytes_and_answers_preserved=True,role_correction_separate=True,
                phase1_slots=86,phase1_agreement_replayed=True,phase2_cases=46,primary_cases=42,
                diagnostic_cases=4,portable_image_files=len(images),portable_files=len(actual_names),
                own_phase1_evidence_bindings=92,cached_output_bindings=92,
                historical_author_phase2_report_replayed=True,protected_files_unchanged=len(protected),
                raw_answers_changed=0,independence_verified=False,model_calls=0,training_runs=0)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
