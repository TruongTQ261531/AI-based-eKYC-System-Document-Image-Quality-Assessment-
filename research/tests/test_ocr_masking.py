import numpy as np

from research.ocr_diagnostic import field_patch,edit_distance,normalized
from research.support_regions import frame_polygon


def test_full_frame_mask_does_not_change_oracle_field_pixels():
    image=np.random.default_rng(7).integers(0,256,(140,220,3),dtype=np.uint8)
    field={'quad':[[35,40],[180,35],[185,85],[30,90]]}
    unmasked=field_patch(image,field,None)
    full=field_patch(image,field,frame_polygon(220,140))
    np.testing.assert_array_equal(unmasked,full)


def test_disjoint_support_cannot_recover_field_pixels():
    image=np.full((140,220,3),200,np.uint8)
    field={'quad':[[35,40],[180,40],[180,90],[35,90]]}
    disjoint=np.float32([[190,0],[219,0],[219,139],[190,139]])
    assert not field_patch(image,field,disjoint).any()


def test_character_errors_are_not_confidence_or_capped_accuracy():
    assert edit_distance('AB12','AB12')==0
    assert edit_distance('AB12','AB13')==1
    assert edit_distance('A','AAAA')/len('A')>1
    assert normalized('  á b  ')=='Á B'
