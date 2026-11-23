"""Small, standalone regressions for the independent scoped-package verifier."""
import pytest

from research.evidence_contract.human_gate.verify37 import check_html


def page(ids, scoped):
    header = '<h1>C2 · R02</h1>\n'
    if scoped:
        header += '<p>Generated Photos · Azerbaijan · Latvia · Serbia</p>\n'
    parts = []
    for n, cid in enumerate(ids, 1):
        parts.append(f'<details><summary>{n}/{len(ids)} · dob · {cid}</summary>\n'
                     f'<form data-assessor="R02" data-candidate="{cid}" data-item="bound">'
                     f'<img src="assets/{cid}.png"></form></details>\n')
    return header + ''.join(parts) + '<script>offline()</script></html>'


def verify_text(html):
    items = [dict(field='dob', candidate_id=cid) for cid in ('first', 'last')]
    return check_html(html, page(['first', 'held', 'last'], False), items, {'held'}, 'R02')


def test_kept_form_order_and_source_links():
    assert verify_text(page(['first', 'last'], True)) == {'assets/first.png', 'assets/last.png'}


@pytest.mark.parametrize(('old', 'new'), [
    ('assets/first.png', 'assets/last.png'),  # both assets legitimately exist, but belong to different cases
    ('assets/last.png', 'assets/held.png'),
    ('2/2', '2/45'),
    ('offline()', 'network()'),
    ('Azerbaijan', 'held'),
    (' · Serbia', '<img src="https://example.invalid/tracker"> · Serbia'),
    ('data-item="bound"', 'data-item="other"'),
    ('<img src=', '<textarea>prefilled</textarea><img src='),
    ('R02', 'R03'),
])
def test_scoped_workspace_rejects_tampering(old, new):
    with pytest.raises(ValueError):
        verify_text(page(['first', 'last'], True).replace(old, new))
