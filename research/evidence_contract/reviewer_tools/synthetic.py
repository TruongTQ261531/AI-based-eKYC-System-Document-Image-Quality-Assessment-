"""Explicit test fixtures only; never invoke the real reviewer importer."""
import json
from pathlib import Path
import zipfile

from .strict import canonical, digest, sha_bytes


def fixture(phase='phase1', *, reviewer='SYNTHETIC_A', snapshot=None):
    evidence = dict(slot_id='SYNTHETIC_SLOT', image_id='SYNTHETIC_IMG', image_sha256='a'*64,
        field_key='id_number', touched=True, availability='visible', readability='readable',
        semantic_key_confirmed='yes', observed_transcript='SYNTHETIC_TEXT', notes='', prior_exposure='no',
        sources=[dict(kind='body', location='SYNTHETIC_LOCATION', availability='visible', readability='readable',
                      observed_text='SYNTHETIC_TEXT', mrz_line_1='', mrz_line_2='')], entry_complete=True)
    if phase == 'phase1':
        packet = dict(schema='blind-reference-review/1', purpose='blind_review', pages=[dict(
            image_id='SYNTHETIC_IMG', image='images/SYNTHETIC.png', file_sha256='a'*64,
            fields=[dict(slot_id='SYNTHETIC_SLOT', field_key='id_number', label='SYNTHETIC')])])
        packet['packet_id'] = digest(packet)
        value = dict(schema='blind-human-review/1', packet_id=packet['packet_id'], packet_purpose='blind_review',
            mode='unit_injected', export_kind='reviewed_observations', exported_at='2026-11-17T00:00:00+07:00',
            reviewer=dict(reviewer_id=reviewer, role='external_reviewer', output_exposure='none', independence_verified=False),
            review_state='complete', items=[evidence], no_model_outputs_shown_by_packet=True, no_expected_values_shown_by_packet=True)
        job = dict(schema='reviewer-job/1', phase=phase, reviewer_id=reviewer, packet_id=packet['packet_id'], author_answers_included=False)
    else:
        snapshot = snapshot or digest(fixture()[1])
        packet = dict(schema='ifv-blind-output-review/1', purpose='blind_output_review', phase1_snapshot=snapshot,
                      cases=[dict(case_id='SYNTHETIC_CASE', field_key='id_number')])
        packet['packet_id'] = digest(packet)
        value = dict(schema='ifv-output-observations/1', mode='unit_injected', packet_id=packet['packet_id'],
            phase1_snapshot=snapshot, export_kind='reviewed_observations', exported_at='2026-11-17T00:01:00+07:00',
            items=[dict(case_id='SYNTHETIC_CASE', test_validity='uncertain', absence_check='not_applicable',
                reason='SYNTHETIC_ONLY', first_reveal_at='2026-11-17T00:00:30+07:00',
                before_reading='uncertain', after_reading='uncertain', output_note='')])
        job = dict(schema='reviewer-job/1', phase=phase, reviewer_id=reviewer, phase1_snapshot=snapshot,
            canonical_packet_id=packet['packet_id'], portable_view_sha256=digest(packet), author_answers_included=False)
    job['job_id'] = digest(job)
    return dict(job=job, packet=packet, archive_sha256='b'*64), value


def zip_fixture(path, bundle):
    """Creates only an artificial test bundle; bytes are not document imagery."""
    packet = bundle['packet']; job = bundle['job']
    files = {}
    if job['phase'] == 'phase1':
        raw = b'SYNTHETIC_NOT_AN_IMAGE'; packet['pages'][0]['file_sha256'] = sha_bytes(raw)
        packet.pop('packet_id'); packet['packet_id'] = digest(packet)
        job['packet_id'] = packet['packet_id']
        files.update({'packet_manifest.json':canonical(packet), 'images/SYNTHETIC.png':raw})
    else:
        files['reviews/SYNTHETIC/index.html'] = b'<script>window.OUTPUT_PACKET='+canonical(packet)+b';</script>'
    job.pop('job_id'); job['job_id'] = digest(job)
    files['REVIEW_JOB.json'] = canonical(job)
    files['MANIFEST.json'] = canonical(dict(schema='portable-review-package/1', job=job['job_id'],
        files={name:sha_bytes(raw) for name, raw in files.items()}))
    with zipfile.ZipFile(path, 'x') as archive:
        for name, raw in files.items(): archive.writestr('SYNTHETIC/'+name, raw)
    return sha_bytes(Path(path).read_bytes())
