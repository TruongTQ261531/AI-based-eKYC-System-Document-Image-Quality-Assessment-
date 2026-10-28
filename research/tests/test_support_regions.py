import numpy as np
import pytest

from research.support_regions import area,intersection,expand_region,required_margin,conformal_quantile


def test_expansion_uses_outward_halfplanes_and_is_monotone():
    quad=np.float32([[30,20],[80,30],[70,80],[20,70]])
    previous=quad
    for amount in (0,1,5,20,100):
        region=expand_region(quad,[amount]*4,120,100)
        assert area(intersection(region,previous))>=area(previous)-.01
        previous=region


def test_computed_required_margin_contains_target_polygon():
    quad=np.float32([[30,30],[70,30],[70,70],[30,70]])
    target=np.float32([[20,10],[90,10],[90,80],[20,80]])
    scales=np.array([2,3,4,5])
    score=required_margin(quad,[target],scales)
    region=expand_region(quad,score*scales,120,100)
    assert area(intersection(region,target))==pytest.approx(area(target),abs=.01)


def test_finite_sample_quantile_does_not_use_interpolated_percentile():
    assert conformal_quantile(range(20),.1)==18
    assert np.isinf(conformal_quantile([1,2,3],.1))
    with pytest.raises(ValueError):conformal_quantile([], .1)


def test_full_frame_is_an_explicit_fallback_not_hidden_success():
    quad=np.float32([[30,30],[70,30],[70,70],[30,70]])
    region=expand_region(quad,[float('inf')]*4,120,100)
    assert area(region)==119*99
    assert area(quad)/area(region)<.8
