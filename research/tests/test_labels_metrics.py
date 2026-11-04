import pytest
from research.labels_metrics import effects
from research.labels_synth import CONDITIONS

def cases():
    return [dict(source='authored',role='test',capture='full',physical_id=str(i),condition=c,
                 correct=3,reference=5,predicted=4) for i in range(3) for c in CONDITIONS]

def test_paired_equal_cells_have_zero_effect_and_interval():
    value=effects(cases())
    assert value['document_instances']==3
    for contrast in value['contrasts'].values():assert contrast=={'delta':0.,'ci95_low':0.,'ci95_high':0.}

def test_missing_factorial_view_rejected():
    with pytest.raises(ValueError):effects(cases()[:-1])

def test_reference_mismatch_is_not_a_font_effect():
    rows=cases();rows[1]['reference']=4
    with pytest.raises(ValueError):effects(rows)
