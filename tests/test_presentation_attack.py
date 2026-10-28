import numpy as np
import pytest

from ekyc.io import StageError
from ekyc.live_challenge import LiveChallenge
from ekyc.presentation_attack import classify_logits, context_crop
from test_live_challenge import observation, face_extract


def test_pad_uses_class_one_bgr_raw_255_and_both_models():
    image = np.full((300,500,3), [10,80,240], np.uint8)
    tensor = context_crop(image, [0,5,100,100], 4.)
    assert tensor.shape==(1,3,80,80) and tensor.dtype==np.float32
    assert tensor[0,:,40,40].tolist()==[10.,80.,240.]
    assert classify_logits([[0,6,0],[0,6,0]])['decision']=='live'
    assert classify_logits([[6,0,0],[0,6,0]])['decision']=='spoof'
    assert classify_logits([[0,6,0],[0,0,6]])['decision']=='spoof'
    assert classify_logits([[0,1,0],[0,6,0]])['decision']=='uncertain'


@pytest.mark.parametrize('outputs', [[[0,1,0]],[[0,np.nan,0],[0,1,0]],[[0,1],[0,1,0]]])
def test_invalid_pad_evidence_cannot_pass(outputs):
    with pytest.raises(StageError): classify_logits(outputs)


@pytest.mark.parametrize('decision,reason',[('spoof','spoof_detected'),(None,'pad_unavailable')])
def test_fake_or_missing_pad_stops_immediately_without_calling_matching(decision,reason):
    challenge = LiveChallenge(0.)
    obs = observation()
    obs['pad'] = {'decision':decision}
    def forbidden_extract(image): raise AssertionError('Spoof must never reach matching')
    result=challenge.update(obs,np.zeros((200,300,3),np.uint8),.2,forbidden_extract)
    assert result['status']=='failed' and result['reason']==reason
    assert not challenge.proof_valid(.2) and not challenge.embeddings


def test_uncertain_pad_never_advances_even_when_motion_observation_is_good():
    challenge = LiveChallenge(0.)
    obs = observation(); obs['pad']={'decision':'uncertain'}
    for n in range(25):
        result=challenge.update(obs,np.full((20,20,3),n,np.uint8),n*.2,face_extract)
    assert result['status']=='running' and result['completed']==0
    assert challenge.baseline is None and challenge.good_frames==0
    assert not challenge.proof_valid(5.)


def test_spoof_revokes_previously_collected_identity_samples():
    challenge=LiveChallenge(0.)
    for n in range(8): challenge.update(observation(),np.full((20,20,3),n,np.uint8),n*.2,face_extract)
    assert challenge.embeddings
    obs=observation(); obs['pad']={'decision':'spoof'}
    challenge.update(obs,np.full((20,20,3),200,np.uint8),2.,face_extract)
    assert not challenge.embeddings and challenge.status=='failed'
