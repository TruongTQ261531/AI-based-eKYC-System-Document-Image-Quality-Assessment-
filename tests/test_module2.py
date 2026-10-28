"""Geometry regressions for Module 2; synthetic coordinates are ground truth.

These checks exercise localization and the image transform, not OCR accuracy or
semantic proof that a rectangle is an identity document.
"""
import itertools
import json

import cv2
import numpy as np
import pytest

from ekyc.io import StageError
from ekyc.module2_homography import Homography, order_corners, _refine_sides


def polygon_iou(first, second):
    """Compare convex polygons independently of vertex order or image raster size."""
    first = cv2.convexHull(np.asarray(first, dtype=np.float32))
    second = cv2.convexHull(np.asarray(second, dtype=np.float32))
    intersection, _ = cv2.intersectConvexConvex(first, second)
    union = cv2.contourArea(first) + cv2.contourArea(second) - intersection
    return intersection / union


def make_document(corners, background=20, foreground=200):
    image = np.full((480, 640, 3), background, dtype=np.uint8)
    cv2.fillConvexPoly(image, np.asarray(corners, np.int32), (foreground,) * 3)
    return image


def test_order_is_invariant_to_input_vertex_permutation():
    expected = np.float32([[90, 70], [550, 120], [490, 420], [60, 350]])
    for permutation in itertools.permutations(expected.tolist()):
        np.testing.assert_allclose(order_corners(permutation), expected)


def test_supplied_corners_map_to_output_corners_and_preserve_contract():
    corners = np.float32([[120, 80], [560, 130], [500, 420], [80, 360]])
    image = make_document(corners)
    rectified, result = Homography().run(image, corners[::-1])
    height, width = rectified.shape[:2]
    expected = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
    transformed = cv2.perspectiveTransform(corners[None], np.asarray(result['matrix']))[0]
    np.testing.assert_allclose(transformed, expected, atol=1e-3)
    assert result['width'] == width and result['height'] == height
    assert result['method'] == 'provided_corners'
    assert result['requires_review'] is False
    json.dumps(result, allow_nan=False)


def test_portrait_geometry_is_not_forced_to_landscape_card_ratio():
    image = np.zeros((600, 400, 3), np.uint8)
    corners = [[80, 50], [280, 50], [280, 550], [80, 550]]
    rectified, _ = Homography().run(image, corners)
    assert rectified.shape == (500, 200, 3)


def test_explicit_physical_aspect_ratio_controls_output_shape():
    corners = [[120, 80], [560, 130], [500, 420], [80, 360]]
    _, result = Homography().run(make_document(corners), corners, aspect_ratio=1.6)
    # Pixel rounding may change the requested ratio by roughly one output pixel.
    assert abs(result['width'] / result['height'] - 1.6) <= 2 / result['height']


@pytest.mark.parametrize('aspect_ratio', [0, -1, np.nan, np.inf, -np.inf])
def test_invalid_explicit_aspect_ratio_is_rejected(aspect_ratio):
    image = np.zeros((480, 640, 3), np.uint8)
    corners = [[80, 80], [560, 80], [560, 400], [80, 400]]
    with pytest.raises(StageError):
        Homography().run(image, corners, aspect_ratio=aspect_ratio)


@pytest.mark.parametrize('corners', [
    [],
    [[0, 0], [100, 0], [100, 100]],
    [[0, 0, 0]] * 4,
    [['invalid', 0], [100, 0], [100, 100], [0, 100]],
    [[20, 20], [420, 20], [420, 300], [np.nan, 300]],
    [[20, 20], [420, 20], [420, 300], [np.inf, 300]],
    [[20, 20], [420, 20], [420, 300], [20, 20]],
    [[20, 20], [420, 20], [420, 300], [220, 100]],
    [[20, 20], [220, 21], [420, 22], [220, 23]],
    [[-1, 20], [420, 20], [420, 300], [20, 300]],
    [[20, 20], [640, 20], [640, 300], [20, 300]],
])
def test_malformed_or_degenerate_corners_raise_stage_error(corners):
    with pytest.raises(StageError):
        Homography().run(np.zeros((480, 640, 3), np.uint8), corners)


@pytest.mark.parametrize('image', [
    None,
    np.empty((0, 640, 3), np.uint8),
    np.zeros((480, 640), np.uint8),
    np.zeros((480, 640, 4), np.uint8),
    np.zeros((480, 640, 3), np.float32),
])
def test_invalid_source_image_raises_stage_error(image):
    with pytest.raises(StageError):
        Homography().run(image)


def test_transform_preserves_original_colors_without_mutating_input():
    image = np.full((320, 480, 3), (12, 37, 81), np.uint8)
    original = image.copy()
    corners = [[80, 50], [400, 50], [400, 250], [80, 250]]
    rectified, _ = Homography().run(image, corners)
    np.testing.assert_array_equal(image, original)
    np.testing.assert_array_equal(rectified, np.full_like(rectified, (12, 37, 81)))


@pytest.mark.parametrize('background,foreground,corners', [
    (10, 42, [[120, 80], [560, 130], [500, 420], [80, 360]]),
    (20, 200, [[230, 80], [470, 170], [600, 430], [70, 400]]),
    (20, 200, [[230, 50], [440, 70], [470, 440], [200, 420]]),
])
def test_auto_localization_retains_dark_perspective_and_portrait_support(background, foreground, corners):
    image = make_document(corners, background, foreground)
    original = image.copy()
    rectified, result = Homography().run(image)
    assert polygon_iou(result['corners'], corners) >= 0.95
    assert min(rectified.shape[:2]) >= 80
    assert result['requires_review'] is True
    np.testing.assert_array_equal(image, original)


def test_uniform_image_has_no_automatic_document():
    with pytest.raises(StageError):
        Homography().run(np.full((480, 640, 3), 100, np.uint8))


def test_refinement_recovers_observed_boundary_from_inset_polygon():
    edges = np.zeros((480, 640), np.uint8)
    cv2.rectangle(edges, (100, 80), (540, 400), 255, 1)
    proposed = np.float32([[104, 84], [536, 84], [536, 396], [104, 396]])
    expected = np.float32([[100, 80], [540, 80], [540, 400], [100, 400]])
    refined = _refine_sides(proposed, edges)
    assert refined is not None
    np.testing.assert_allclose(refined, expected, atol=1.0)


def test_stronger_inner_portrait_does_not_replace_supported_outer_document():
    image = np.full((480, 640, 3), 90, np.uint8)
    cv2.rectangle(image, (100, 100), (540, 380), (105, 105, 105), -1)
    cv2.rectangle(image, (135, 135), (320, 345), (20, 20, 20), -1)
    _, result = Homography().run(image)
    assert polygon_iou(result['corners'], [[100, 100], [540, 100], [540, 380], [100, 380]]) > .95


def test_three_visible_edges_do_not_invent_a_fourth_boundary():
    image = np.full((480, 640, 3), 20, np.uint8)
    cv2.polylines(image, [np.int32([[100, 400], [100, 80], [550, 80], [550, 400]])],
                  False, (200, 200, 200), 3)
    with pytest.raises(StageError):
        Homography().run(image)


def test_clipped_document_does_not_use_image_border_as_missing_side():
    image = np.full((480, 640, 3), 20, np.uint8)
    cv2.rectangle(image, (100, 80), (700, 400), (200, 200, 200), -1)
    with pytest.raises(StageError):
        Homography().run(image)


def test_complete_document_close_to_frame_can_be_localized():
    corners = [[3, 3], [636, 3], [636, 476], [3, 476]]
    image = make_document(corners)
    _, result = Homography().run(image)
    assert polygon_iou(result['corners'], corners) >= .98
    assert result['requires_review'] is True
    assert result['orientation'] == 'geometric_only'
    assert result['aspect_ratio_source'] == 'edge_estimate'
    evidence = result['detection']
    assert len(evidence['edge_supports']) == 4
    assert all(0 <= support <= 1 for support in evidence['edge_supports'])
    assert evidence['score_is_probability'] is False
    json.dumps(result, allow_nan=False)


def test_semantic_card_hint_excludes_strong_inner_text_rectangle():
    image=np.full((480,640,3),110,np.uint8)
    cv2.rectangle(image,(100,100),(540,380),(125,125,125),-1)
    cv2.rectangle(image,(180,160),(480,340),(40,40,40),2)
    hint=dict(box=[100,100,540,380],confidence=.95,label='CCCD_Chip')
    _,geometry=Homography().run(image,region_hints=[hint])
    assert polygon_iou(geometry['corners'],[[100,100],[540,100],[540,380],[100,380]])>.90
    assert geometry['detection']['policy']=='semantic_boundary_v4'


def test_semantic_crop_preserves_card_when_no_four_edges_are_corroborated():
    image=np.full((480,640,3),110,np.uint8)
    hint=dict(box=[100,100,540,380],confidence=.95,label='GPLX')
    _,geometry=Homography().run(image,region_hints=[hint])
    assert geometry['method']=='detected_region_crop'
    assert geometry['requires_review']
    assert 'perspective_not_verified_region_preserved' in geometry['warnings']
    assert geometry['corners'][0][0]<100 and geometry['corners'][0][1]<100


def test_complete_rounded_card_is_localized_without_a_known_card_type():
    from PIL import Image,ImageDraw
    image=Image.new('RGB',(1200,800),'#424b52')
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((95,70,1105,725),radius=25,fill='#f1f5ef',outline='#a3c3bb',width=4)
    _,geometry=Homography().run(np.asarray(image)[:,:,::-1].copy())
    assert polygon_iou(geometry['corners'],[[95,70],[1105,70],[1105,725],[95,725]])>.95
