import numpy as np
from ekyc.module1_quality import assess_scores, image_metrics
from ekyc.feedback import retake


def metrics(**changes):
    return dict(min_side=1080,brightness=150,p90=220,contrast=45,sharpness=150,**{}) | changes


def test_clean_argmax_below_old_threshold_is_not_a_veto():
    result=assess_scores([.45,.2,.15,.1,.1],metrics())
    assert result['passed'] and result['needs_document_checks']
    assert result['warnings'][0]['code']=='quality_uncertain'


def test_cropped_and_distorted_predictions_need_geometry_evidence():
    for scores in ([.04,.02,.9,.02,.02],[.04,.02,.02,.02,.9]):
        result=assess_scores(scores,metrics())
        assert result['passed'] and result['warnings'][0]['certainty']=='suspected'


def test_blur_requires_corroboration_and_guidance():
    scores=[.02,.92,.02,.02,.02]
    assert assess_scores(scores,metrics())['passed']
    result=assess_scores(scores,metrics(sharpness=10))
    assert not result['passed']
    feedback=retake('quality_rejected',result)
    assert feedback['issues'][0]['code']=='blur'
    assert len(feedback['issues'][0]['instructions'])>=2


def test_severely_dark_and_blank_frames_rejected_even_if_model_says_clean():
    scores=[.9,.025,.025,.025,.025]
    for image,reason in [(np.zeros((400,640,3),np.uint8),'too_dark'),
                         (np.full((400,640,3),180,np.uint8),'no_detail')]:
        result=assess_scores(scores,image_metrics(image))
        assert not result['passed'] and result['issues'][0]['code']==reason


def test_geometry_failure_has_instructions_without_claiming_proven_crop():
    result=retake('document_corners_not_found')
    assert result['issues'][0]['instructions']
    assert 'không thể khẳng định' in result['issues'][0]['detail']
