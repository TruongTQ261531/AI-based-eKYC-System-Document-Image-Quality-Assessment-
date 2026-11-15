"""No real human observations are authored or changed by these fixture tests."""
from copy import deepcopy
import json

from research.evidence_contract.task55.review_resume import completion_summary, render_resume
from research.evidence_contract.tests.test_task55_ifv import phase1


def control_with_missing_source():
    packet, value = phase1()
    item = value['items'][0]
    item['sources'] = []
    second = dict(deepcopy(item), slot_id='F-b', field_key='b', availability='not_seen',
                  readability='unreadable', observed_transcript='')
    value['items'].append(second)
    return packet, value


def test_completion_keeps_submitted_text_and_explains_missing_sources():
    packet, value = control_with_missing_source()
    original = deepcopy(value)
    report = completion_summary(value, packet, allow_unit=True)
    assert value == original
    assert report['complete_observations'] == 1
    assert report['incomplete_observations'] == 1
    assert report['issue_counts'] == {'missing_source_location_and_state': 1}
    assert report['generated_human_annotations'] == 0
    assert 'UNIT_EXAMPLE' not in json.dumps(report)


def test_completion_reports_overlapping_reasons_without_double_counting_fields():
    packet, value = control_with_missing_source()
    value['items'][0]['observed_transcript'] = ''
    report = completion_summary(value, packet, allow_unit=True)
    assert report['incomplete_observations'] == 1
    assert sum(report['issue_counts'].values()) == 2
    assert report['issue_counts']['missing_readable_transcript'] == 1


def test_completion_rejects_self_reported_fullness_and_preserves_contradictions():
    packet, value = phase1()
    item = dict(deepcopy(value['items'][0]), slot_id='F-b', field_key='b',
                availability='not_seen', readability='unreadable', sources=[], entry_complete=True)
    value['items'].append(item)
    value['review_state'] = 'complete'
    report = completion_summary(value, packet, allow_unit=True)
    assert report['incomplete_observations'] == 1
    assert report['issue_counts'] == {'absent_value_has_transcript': 1}
    assert item['observed_transcript'] == 'UNIT_EXAMPLE'


def test_resume_html_roundtrips_human_input_without_script_injection():
    packet, value = phase1()
    value['items'][0]['notes'] = '</script><script>unit-injected</script>'
    before = deepcopy((packet, value))
    page = render_resume(packet, value, '<main><!--PACKET--></main>')
    assert page.count('<script>') == page.count('</script>') == 1
    embedded = page.split('window.BLIND_REVIEW_RESUME=', 1)[1].split(';\n', 1)[0]
    assert json.loads(embedded) == value
    assert (packet, value) == before
    assert 'BLIND_REVIEW_STORAGE_KEY' in page
    assert 'author_reference' not in page and 'predicted_fields' not in page


def test_completion_missing_slots_stay_missing():
    packet, value = phase1()
    report = completion_summary(value, packet, allow_unit=True)
    assert report['complete_observations'] == 1
    assert report['missing_slots'] == 1
    assert report['issue_counts'] == {'missing_observation': 1}
