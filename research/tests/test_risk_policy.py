import numpy as np
import pytest

from research.risk_policy import choose_index


def test_document_correction_is_not_a_frame_count_correction():
    losses = np.tile([.2, .08, 0.], (20, 1))
    assert choose_index(losses, correction=False)[0] == 1
    assert choose_index(losses)[0] == 2
    assert choose_index(np.repeat(losses, 70, axis=0))[0] == 1


def test_nonmonotone_family_is_rejected_instead_of_claiming_crc():
    with pytest.raises(ValueError, match='not monotone'):
        choose_index([[.1, .2, 0.]])


def test_small_calibration_sample_falls_back_without_false_certificate():
    index, criterion, certified = choose_index([[1., 0.]]*3)
    assert index == 1 and criterion == .25 and not certified


def test_corrected_boundary_uses_inclusive_comparison():
    losses = np.zeros((19, 2)); losses[:, 0] = 1/19
    assert choose_index(losses, alpha=.1)[0] == 0
