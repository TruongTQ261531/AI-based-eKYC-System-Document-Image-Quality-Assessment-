import numpy as np
import pytest
from research.labels_synth import specification,render,FONT_PAIRS,ensure_glyphs,anchors

def test_document_types_have_their_own_fields():
    assert 'student_id' in specification(1)['values']
    assert 'id_number' not in specification(1)['values']
    assert 'license_class' in specification(2)['values']

def test_mask_removes_one_value_without_touching_other_ink():
    spec=specification(0);full,fields,meta=render(spec,'new_layout_new_font','full')
    masked,masked_fields,masked_meta=render(spec,'new_layout_new_font','value_mask')
    assert not np.array_equal(full,masked)
    assert [f['reference_text'] for f in fields]==[f['reference_text'] for f in masked_fields]
    assert all(f['readability']['status']=='unassessed' for f in masked_fields)
    hidden=[f for f in masked_fields if f['construction_visibility']['status']=='ink_masked']
    assert len(hidden)==1 and hidden[0]['raw_key']==spec['masked_key']
    for f in fields:
        if f['raw_key']==spec['masked_key']:continue
        q=np.asarray(f['polygon'],int);a,b=q.min(axis=0);c,d=q.max(axis=0)
        assert np.array_equal(np.asarray(full)[b:d,a:c],np.asarray(masked)[b:d,a:c])

def test_font_size_and_content_are_controlled_across_factorial():
    spec=specification(2)
    _,a,_=render(spec,'seen_layout_seen_font','full')
    _,b,_=render(spec,'new_layout_new_font','full')
    assert [(f['raw_key'],f['reference_text'],f['font_size']) for f in a]==[(f['raw_key'],f['reference_text'],f['font_size']) for f in b]
    assert anchors(False)!=anchors(True)

def test_font_missing_required_glyph_is_not_silently_rendered():
    with pytest.raises(ValueError):ensure_glyphs(FONT_PAIRS[0][0],chr(0x10ffff))
