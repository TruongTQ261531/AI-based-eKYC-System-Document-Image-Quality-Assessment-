import numpy as np
import pytest

from ekyc.io import StageError
from research.partial_support import observed_support
from research.support_regions import area, intersection, frame_polygon


def test_exact_observed_sides_preserve_visible_card_without_fourth_corner():
    card=np.float32([[-20,-20],[80,10],[85,80],[10,85]])
    points=[None,card[1],card[2],card[3]]
    region=observed_support(points,100,100)
    visible=intersection(card,frame_polygon(100,100))
    assert area(intersection(region,visible))==pytest.approx(area(visible),abs=.01)
    assert area(region)<area(frame_polygon(100,100))
    triangle=np.float32(points[1:])
    assert area(intersection(triangle,visible))<.8*area(visible)


def test_two_corners_do_not_define_a_claimed_support_rescue():
    with pytest.raises(StageError,match='Three observed corners'):
        observed_support([None,[80,10],[85,80],None],100,100)
