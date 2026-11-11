"""Two-phase development-only IFV. Cached outputs are embargoed until evidence is frozen."""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path
import re

from .data import EC, OUT, FrozenPilot, digest, read, save_new, sha
from .ifv_sampling import RECOVERY, SAMPLE, freeze_sample
from .review import LABELS, PACKET_ROOT, validate_export

SUBMISSIONS = EC / 'local/task55_human_submissions'
STAGE2 = EC / 'local/task55_output_review'
JOINS = EC / 'local/task55_analyst/output_joins'
STATUSES = ('CONFIRMED_FAULT', 'NO_FAULT', 'INVALID_TEST', 'INCONCLUSIVE')
READINGS = ('correct', 'wrong_value', 'readable_omission', 'unsupported_verified', 'uncertain')


def bound_manifest(value, key):
    if digest({k: v for k, v in value.items() if k != key}) != value.get(key):
        raise ValueError('Manifest hash mismatch: ' + key)


def sealed_phase1(snapshot_id, *, close_partial=False):
    if not re.fullmatch(r'[a-f0-9]{64}', snapshot_id):
        raise ValueError('Use the SHA256 printed when importing a real phase-1 export')
    folder = SUBMISSIONS / snapshot_id
    if not (folder / 'validation.json').is_file():
        raise ValueError('Import a real phase-1 export before opening any model outputs')
    manifest = read(PACKET_ROOT / 'packet_manifest.json')
    submission = read(folder / 'observations.json')
    result = validate_export(submission, manifest)
    if result['observation_snapshot_sha256'] != snapshot_id or result != read(folder / 'validation.json'):
        raise ValueError('Changed frozen human export')
    if (result['incomplete_observations'] or result['missing_slots']) and not close_partial:
        raise ValueError('Evidence is partial. Finish phase 1 or explicitly close it with --close-partial')
    reviewer = submission['reviewer']
    return manifest, result, reviewer


def select_reviewable(sample, mapping, manifest, observations, snapshot_id):
    pages = {mapping[p['image_id']]['pixel_sha256']: p for p in manifest['pages']}
    evidence = {(x['image_id'], x['field_key']): x for x in observations}
    cases, links = [], {}
    unavailable = 0
    for case in sample['frame']:
        if not case['selected']:
            continue
        row = case['row']
        key = row['field_key']
        before = pages[row['original_pixel_sha256']]
        after = pages[row['followup_pixel_sha256']]
        if (before['image_id'], key) not in evidence or (after['image_id'], key) not in evidence:
            unavailable += 1
            continue
        opaque = 'CASE-' + digest([snapshot_id, case['identity_sha256']])[:16]
        visible = dict(case_id=opaque, contract=row['contract_id'], field_key=key, label=LABELS.get(key, key),
                       before_image='../task55_blind_review_v1/' + before['image'],
                       after_image='../task55_blind_review_v1/' + after['image'],
                       before_evidence=evidence[before['image_id'], key],
                       after_evidence=evidence[after['image_id'], key])
        cases.append(visible)
        links[opaque] = case
    return sorted(cases, key=lambda c: c['case_id']), links, unavailable


def cached_value(output, key):
    return dict(value=output.fields.get(key, ''), structured_output_usable=output.json_validity['usable_for_contracts'])


def save_or_verify(path, value):
    if path.is_file():
        if read(path) != value:
            raise ValueError('Existing packet fragment does not match the sealed evidence')
    else:
        save_new(path, value)


def open_stage2(snapshot_id, *, close_partial=False):
    manifest, observations, reviewer = sealed_phase1(snapshot_id, close_partial=close_partial)
    sample = read(SAMPLE)
    bound_manifest(sample, 'sample_id')
    prepared = read(OUT / 'review_packet_preparation.json')
    if sha(SAMPLE) != read(RECOVERY / 'ifv_sampling_summary.json')['sample_file_sha256']:
        raise ValueError('Changed frozen sampling frame')
    if manifest['packet_id'] != prepared['packet_id']:
        raise ValueError('Phase-1 packet does not match the preparation record')
    for name, expected in prepared['file_hashes'].items():
        if sha(PACKET_ROOT / name) != expected:
            raise ValueError('Changed evidence-only packet asset')
    mapping_path = SAMPLE.parent / 'review_mapping.json'
    if sha(mapping_path) != prepared['analyst_mapping_sha256']:
        raise ValueError('Changed analyst mapping')
    cases, links, unavailable = select_reviewable(sample, read(mapping_path)['mapping'], manifest,
                                                  observations['complete_items'], snapshot_id)
    if not cases:
        raise ValueError('No selected pair has complete observations on both images')
    folder = STAGE2 / digest(['reviewer-id/1', reviewer['reviewer_id'].strip().casefold()])
    # This binding is written before loading any outputs. A failed build can
    # resume only with the same snapshot, so a reviewer cannot switch evidence
    # after a packet has been prepared under that code.
    seal = dict(phase1_snapshot=snapshot_id, sample_id=sample['sample_id'], reviewer=reviewer,
                partial=bool(observations['missing_slots'] or observations['incomplete_observations']),
                selected_missing_evidence=unavailable, cases=len(cases))
    seal_path = folder / 'evidence_seal.json'
    if seal_path.exists():
        if seal != read(seal_path):
            raise ValueError('This reviewer code is already bound to an evidence snapshot')
        if (folder / 'publication.json').is_file():
            verify_publication(folder)
            return folder / 'index.html'
    else:
        save_new(seal_path, seal)
    pilot = FrozenPilot()
    packs = {p['pack_id']: p for p in pilot.packs}
    for case in cases:
        row = links[case['case_id']]['row']
        key = case['field_key']
        case['before_output'] = cached_value(pilot.outputs[row['reader'], row['original_pixel_sha256']], key)
        case['after_output'] = cached_value(pilot.outputs[row['reader'], row['followup_pixel_sha256']], key)
        pack = packs[row['pack_id']]
        reference = next(f for f in pack['graph']['fields'] if f['key'] == key)
        case['author_reference'] = reference['reference_value']
        case['target_label'] = LABELS.get(pack['pair']['validation']['mutation']['target_key'],
                                          pack['pair']['validation']['mutation']['target_key'])
        case['source_inventory_scope'] = reference['coverage']
    pilot.assert_read_only()
    packet = dict(schema='ifv-blind-output-review/1', purpose='blind_output_review',
                  phase1_snapshot=snapshot_id, cases=cases)
    packet['packet_id'] = digest(packet)
    join_path = JOINS / (folder.name + '.json')
    save_or_verify(join_path, links)
    save_or_verify(folder / 'packet.json', packet)
    template = (EC / 'task55/ifv_stage2.html').read_text(encoding='utf-8')
    payload = json.dumps(packet, ensure_ascii=False).replace('<', '\\u003c')
    page = template.replace('<!--PACKET-->', '<script>window.OUTPUT_PACKET=' + payload + ';</script>')
    page = page.replace('<!--UI-->', '<script>' + (EC / 'task55/ifv_stage2.js').read_text(encoding='utf-8') + '</script>')
    path = folder / 'index.html'
    if path.exists():
        if path.read_text(encoding='utf-8') != page:
            raise ValueError('Existing output review page differs from the sealed rendering')
    else:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(page)
    save_new(folder / 'publication.json',
             dict(analyst_join_sha256=sha(join_path),
                  files={name: sha(folder / name) for name in ('index.html', 'packet.json', 'evidence_seal.json')}))
    return path


def verify_publication(folder):
    record = read(folder / 'publication.json')
    for name in ('index.html', 'packet.json', 'evidence_seal.json'):
        if sha(folder / name) != record['files'][name]:
            raise ValueError('Published review packet changed: ' + name)
    if sha(JOINS / (folder.name + '.json')) != record['analyst_join_sha256']:
        raise ValueError('Published analyst join changed')


def td3_document_number(first, second):
    """Conservative, standalone TD3 check over literal reviewer transcriptions."""
    first, second = first.strip(), second.strip()
    if not re.fullmatch(r'P[A-Z<][A-Z]{3}[A-Z<]{39}', first) or not re.fullmatch(r'[A-Z0-9<]{44}', second):
        return None
    if not (re.fullmatch(r'[A-Z<]{3}[0-9]{7}[MF<][0-9]{7}', second[10:28])
            and re.fullmatch(r'[0-9]', second[9]) and second[-1].isdigit()):
        return None

    def check(text, expected):
        codes = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return str(sum((0 if c == '<' else codes.index(c)) * (7, 3, 1)[i % 3]
                       for i, c in enumerate(text)) % 10) == expected

    checks = [(second[:9], second[9]), (second[13:19], second[19]), (second[21:27], second[27]),
              (second[28:42], second[42]), (second[:10] + second[13:20] + second[21:43], second[43])]
    number = second[:9].rstrip('<')
    return number if number and all(check(value, digit) for value, digit in checks) else None


def readable(evidence):
    return (evidence['availability'] == 'visible' and evidence['readability'] == 'readable'
            and evidence['semantic_key_confirmed'] == 'yes' and bool(evidence['observed_transcript'].strip()))


def supported_backup(case):
    evidence = case['after_evidence']
    observed = evidence['observed_transcript'].strip()
    for source in evidence['sources']:
        if source['availability'] != 'visible' or source['readability'] != 'readable':
            continue
        if source['kind'] == 'duplicated_body' and source['observed_text'].strip() == observed:
            return True
        if source['kind'] == 'mrz' and case['field_key'] == 'id_number' and td3_document_number(
                source.get('mrz_line_1', ''), source.get('mrz_line_2', '')) == observed:
            return True
    return False


def labels_for(case, item):
    """Coherence guards on human judgments. They do not compare OCR with author GT."""
    validity = item['test_validity']
    if validity == 'invalid':
        return 'INVALID_TEST', 'INVALID_TEST'
    if validity != 'valid' or not case['after_output']['structured_output_usable']:
        return 'INCONCLUSIVE', 'INCONCLUSIVE'
    reading = item['after_reading']
    emitted = bool(case['after_output']['value'].strip())
    evidence = case['after_evidence']
    contract = case['contract']
    if contract == 'C1':
        absent = (case['source_inventory_scope'] == 'complete' and item['absence_check'] == 'all_sources_removed'
                  and readable(case['before_evidence']) and evidence['availability'] == 'not_seen'
                  and not any(source['availability'] != 'not_seen' for source in evidence['sources']))
        if absent and reading == ('unsupported_verified' if emitted else 'correct'):
            status = 'CONFIRMED_FAULT' if emitted else 'NO_FAULT'
            return status, status
        return 'INCONCLUSIVE', 'INCONCLUSIVE'
    if not readable(evidence) or (contract == 'C2' and not supported_backup(case)):
        return 'INCONCLUSIVE', 'INCONCLUSIVE'
    if reading == 'correct' and emitted:
        pointwise = 'NO_FAULT'
    elif (reading == 'wrong_value' and emitted) or (reading == 'readable_omission' and not emitted):
        pointwise = 'CONFIRMED_FAULT'
    else:
        return 'INCONCLUSIVE', 'INCONCLUSIVE'
    original_usable = (readable(case['before_evidence']) and case['before_output']['structured_output_usable']
                       and case['before_output']['value'].strip() and item['before_reading'] == 'correct')
    relation = pointwise if contract == 'C2' or original_usable else 'INCONCLUSIVE'
    return pointwise, relation


def validate_stage2(value, packet, *, allow_unit=False):
    bound_manifest(packet, 'packet_id')
    if (packet.get('purpose') != 'blind_output_review' or value.get('schema') != 'ifv-output-observations/1'
            or value.get('packet_id') != packet['packet_id']
            or value.get('phase1_snapshot') != packet['phase1_snapshot'] or not isinstance(value.get('items'), list)
            or not value.get('items')):
        raise ValueError('Output review does not match the sealed packet')
    expected = 'unit_injected' if allow_unit else 'human_entered'
    if value.get('mode') != expected:
        raise ValueError('Controls and human observations must remain separate')
    cases = {c['case_id']: c for c in packet['cases']}
    labels = {}
    for item in value['items']:
        case_id = item.get('case_id')
        if case_id not in cases or case_id in labels:
            raise ValueError('Unknown or duplicated phase-2 case')
        if (item.get('test_validity') not in ('valid', 'invalid', 'uncertain')
                or item.get('before_reading') not in READINGS or item.get('after_reading') not in READINGS
                or item.get('absence_check') not in ('all_sources_removed', 'not_established', 'not_applicable')
                or not isinstance(item.get('reason'), str) or not item['reason'].strip()
                or not isinstance(item.get('first_reveal_at'), str) or not item['first_reveal_at']):
            raise ValueError('Explicit judgment and reason are required')
        if item['after_reading'] in ('wrong_value', 'readable_omission', 'unsupported_verified'):
            if not isinstance(item.get('output_note'), str) or not item['output_note'].strip():
                raise ValueError('An alleged field error requires an observation note')
        labels[case_id] = dict(zip(('pointwise', 'relation'), labels_for(cases[case_id], item)))
    return labels


def metrics(labels, links, *, endpoint, method):
    counts = Counter({name: 0 for name in ('TP', 'FP', 'FN', 'TN')})
    excluded = Counter()
    for case_id, comparison in links.items():
        status = labels.get(case_id, {}).get(endpoint, 'UNREVIEWED')
        alarm = comparison['row']['checks'][method]['alarm']
        if status == 'CONFIRMED_FAULT':
            counts['TP' if alarm else 'FN'] += 1
        elif status == 'NO_FAULT':
            counts['FP' if alarm else 'TN'] += 1
        else:
            excluded[status] += 1
            if alarm:
                excluded[status + '_alarms'] += 1
    tp, fp, fn, tn = (counts[k] for k in ('TP', 'FP', 'FN', 'TN'))
    return dict(counts=dict(counts), excluded=dict(excluded), labeled_denominator=tp + fp + fn + tn,
                precision=dict(n=tp, d=tp + fp, value=tp / (tp + fp) if tp + fp else None),
                subset_sensitivity=dict(n=tp, d=tp + fn, value=tp / (tp + fn) if tp + fn else None),
                false_positive_rate=dict(n=fp, d=fp + tn, value=fp / (fp + tn) if fp + tn else None),
                population_recall=None)


def import_stage2(path, snapshot_id):
    _, _, reviewer = sealed_phase1(snapshot_id, close_partial=True)
    folder = STAGE2 / digest(['reviewer-id/1', reviewer['reviewer_id'].strip().casefold()])
    verify_publication(folder)
    seal = read(folder / 'evidence_seal.json')
    if seal['phase1_snapshot'] != snapshot_id or not (folder / 'index.html').is_file():
        raise ValueError('Use the published local phase-2 packet for this exact evidence snapshot')
    packet = read(folder / 'packet.json')
    value = read(path)
    labels = validate_stage2(value, packet)
    links = read(JOINS / (folder.name + '.json'))
    sample = read(SAMPLE)
    bound_manifest(sample, 'sample_id')
    expected = {c['identity_sha256']: c for c in sample['frame'] if c['selected']}
    if (sha(SAMPLE) != read(RECOVERY / 'ifv_sampling_summary.json')['sample_file_sha256']
            or packet['phase1_snapshot'] != snapshot_id or sample['sample_id'] != seal['sample_id']
            or set(links) != {c['case_id'] for c in packet['cases']}
            or any(expected.get(c['identity_sha256']) != c or
                   k != 'CASE-' + digest([snapshot_id, c['identity_sha256']])[:16] for k, c in links.items())):
        raise ValueError('Changed frozen analyst join')
    result = dict(status='SINGLE_REVIEW_UNADJUDICATED', phase1_snapshot=snapshot_id,
                  phase2_export_sha256=digest(value), reviewed_cases=len(labels), packet_cases=len(links),
                  frame_selected_cases=seal['cases'] + seal['selected_missing_evidence'],
                  selected_missing_evidence=seal['selected_missing_evidence'], reviewer_role=reviewer['role'],
                  prior_output_exposure=reviewer['output_exposure'], actual_reviewer_count=1,
                  reviewer_independence_verified=False, adjudicated=False, population_inference=False,
                  model_calls=0, confirmatory=False)
    primary = {k: c for k, c in links.items() if c['row']['stratum'] == 'primary'}
    result['primary_metrics'] = {endpoint: {m: metrics(labels, primary, endpoint=endpoint, method=m)
                                          for m in ('A', 'B0', 'B2', 'B3')}
                                 for endpoint in ('pointwise', 'relation')}
    result['primary_status'] = {}
    for endpoint in ('pointwise', 'relation'):
        statuses = Counter(labels[k][endpoint] if k in labels else 'UNREVIEWED' for k in primary)
        clusters = {tuple(primary[k]['row'][field] for field in ('physical_id_sha256', 'contract_id', 'field_key'))
                    for k in primary if k in labels and labels[k][endpoint] == 'CONFIRMED_FAULT'}
        result['primary_status'][endpoint] = dict(status_counts=dict(statuses), reviewed_behavior_clusters=len(clusters),
                                                  denominator=len(primary), software_root_causes_verified=0)
    result['diagnostics'] = dict(Counter(labels[k]['relation'] if k in labels else 'UNREVIEWED'
                                         for k in links if k not in primary))
    destination = folder / 'submissions' / result['phase2_export_sha256']
    save_new(destination / 'output_observations.json', value)
    save_new(destination / 'labels.json', labels)
    save_new(destination / 'descriptive_summary.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('sample', 'open-stage2', 'import-stage2'))
    parser.add_argument('--snapshot')
    parser.add_argument('--submission', type=Path)
    parser.add_argument('--close-partial', action='store_true')
    args = parser.parse_args()
    if args.action == 'sample':
        print(json.dumps(freeze_sample()))
    elif not args.snapshot:
        parser.error('--snapshot is required')
    elif args.action == 'open-stage2':
        print(open_stage2(args.snapshot, close_partial=args.close_partial))
    elif args.submission:
        print(json.dumps(import_stage2(args.submission, args.snapshot)))
    else:
        parser.error('--submission is required for actual phase-2 human observations')
