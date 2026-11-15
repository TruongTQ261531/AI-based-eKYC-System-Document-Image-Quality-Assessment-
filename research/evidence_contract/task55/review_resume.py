"""Resume a submitted blind review without changing observations or frozen assets.

This is a presentation update to phase 1, not a new sample or annotation source.
It imports no reader, model cache, author reference, graph or method verdict.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from .data import EC, OUT, digest, read, save_new, sha
from .review import PACKET_ROOT, validate_export


def completion_summary(value, packet, *, allow_unit=False):
    """Report existing validator decisions; never infer a missing annotation."""
    result = validate_export(value, packet, allow_unit=allow_unit)
    complete = {x['slot_id'] for x in result['complete_items']}
    by_slot = {x['slot_id']: x for x in value['items']}
    issues = []
    for page_number, page in enumerate(packet['pages'], start=1):
        for field in page['fields']:
            slot = field['slot_id']
            if slot in complete:
                continue
            item = by_slot.get(slot)
            reasons = []
            if item is None:
                reasons.append('missing_observation')
            else:
                if item['availability'] == 'visible' and not item['sources']:
                    reasons.append('missing_source_location_and_state')
                if item['readability'] == 'readable' and not item['observed_transcript'].strip():
                    reasons.append('missing_readable_transcript')
                if item['availability'] == 'not_seen' and item['observed_transcript'].strip():
                    reasons.append('absent_value_has_transcript')
                if not reasons:
                    reasons.append('incomplete_state_or_source')
            issues.append(dict(page=page_number, image_id=page['image_id'], slot_id=slot,
                               field_key=field['field_key'], reasons=reasons))
    return dict(schema='blind-review-completion/1', packet_id=packet['packet_id'],
                observation_snapshot_sha256=result['observation_snapshot_sha256'],
                images=len(packet['pages']), field_slots=sum(len(p['fields']) for p in packet['pages']),
                submitted_observations=len(value['items']),
                complete_observations=result['complete_observations'],
                incomplete_observations=result['incomplete_observations'],
                missing_slots=result['missing_slots'],
                images_requiring_completion=len({x['image_id'] for x in issues}),
                issue_counts=dict(Counter(r for x in issues for r in x['reasons'])),
                issues=issues, actual_reviewer_count=result['reviewer_count'],
                reviewer_independence_verified=False, usable_for_confirmatory=False,
                model_calls=0, generated_human_annotations=0)


def render_resume(packet, value, template):
    """Embed submitted values verbatim, escaped for an HTML script context."""
    def literal(item):
        return json.dumps(item, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c')

    if template.count('<!--PACKET-->') != 1:
        raise ValueError('Resume template must have one packet slot')
    snapshot = digest(value)
    script = ('<script>window.BLIND_PACKET=' + literal(packet) + ';\n'
              'window.BLIND_REVIEW_RESUME=' + literal(value) + ';\n'
              'window.BLIND_REVIEW_STORAGE_KEY=' + literal('document-review-resume/' + snapshot) + ';\n'
              'window.BLIND_IMAGE_PREFIX="../task55_blind_review_v1/";</script>')
    return template.replace('<!--PACKET-->', script)


def prepare_resume(submission_path):
    value = read(submission_path)
    packet = read(PACKET_ROOT / 'packet_manifest.json')
    summary = completion_summary(value, packet)
    snapshot = summary['observation_snapshot_sha256']
    imported = EC / 'local/task55_human_submissions' / snapshot
    validation = validate_export(value, packet)
    if read(imported / 'observations.json') != value or read(imported / 'validation.json') != validation:
        raise ValueError('Import the original submission before preparing a resume page')
    prepared = read(OUT / 'review_packet_preparation.json')
    if packet['packet_id'] != prepared['packet_id']:
        raise ValueError('Packet identity changed')
    for name, expected in prepared['file_hashes'].items():
        if sha(PACKET_ROOT / name) != expected:
            raise ValueError('Frozen packet asset changed: ' + name)
    # A reviewer already exposed to phase 2 cannot revise this evidence.
    reviewer = value['reviewer']['reviewer_id'].strip().casefold()
    phase2 = EC / 'local/task55_output_review' / digest(['reviewer-id/1', reviewer])
    if (phase2 / 'evidence_seal.json').exists():
        raise ValueError('Phase 2 already sealed for this reviewer; do not revise blind evidence')
    folder = EC / 'local' / ('task55_blind_review_resume_' + snapshot[:12])
    if folder.exists():
        raise FileExistsError('Preserve existing resume assets/drafts; verify the receipt before reusing them')
    page = render_resume(packet, value, (EC / 'task55/review_template.html').read_text(encoding='utf-8'))
    folder.mkdir()
    with (folder / 'index.html').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(page)
    for name in ('review_core.js', 'review_ui.js'):
        with (folder / name).open('xb') as stream:
            stream.write((EC / 'task55' / name).read_bytes())
    save_new(folder / 'completion_summary.json', summary)
    save_new(folder / 'resume_manifest.json', dict(schema='blind-review-resume/1',
        packet_id=packet['packet_id'], original_submission_file_sha256=sha(submission_path),
        observation_snapshot_sha256=snapshot, source_packet_unchanged=True,
        content_policy='submitted human observations only; no model output or author reference',
        files={p.name: sha(p) for p in folder.iterdir() if p.is_file()},
        image_source='../task55_blind_review_v1/', model_calls=0, human_annotations_generated=0))
    return folder / 'index.html'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--submission', required=True, type=Path)
    args = parser.parse_args()
    print(prepare_resume(args.submission))
