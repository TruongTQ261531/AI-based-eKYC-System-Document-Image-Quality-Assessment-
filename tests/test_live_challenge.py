import math

import cv2
import numpy as np
import pytest

from ekyc.face_observation import rotation_angles, iris_ratio
from ekyc.live_challenge import LiveChallenge, ChallengeRequestError


def observation(yaw=0.,pitch=0.,gaze=.5,blink=0.):
    return dict(face_count=1, quality_ok=True,problems=[],
                pose=dict(yaw=yaw,pitch=pitch,roll=0.),
                gaze_horizontal=gaze,blink_left=blink,blink_right=blink,overlay=[],
                pad=dict(decision='live',method='minifasnet_v2_v1se_rgb_v1'))  # Mock classifier evidence.


def face_extract(image):
    return image,np.array([[1.,0.]],np.float32),{}


def action_observation(action):
    return observation(**{'turn_left':{'yaw':20.},'turn_right':{'yaw':-20.},
                           'look_left':{'gaze':.61},'look_right':{'gaze':.39},
                           'nod':{'pitch':18.},'blink':{'blink':.9}}[action])


def test_geometry_rotation_and_iris_are_measured_in_image_coordinates():
    angle=math.radians(20)
    matrix=np.eye(4)
    matrix[:3,:3]=[[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]]
    assert rotation_angles(matrix)['yaw']==pytest.approx(20)
    assert rotation_angles(matrix)['pitch']==pytest.approx(0)
    points=np.array([[10.,20.],[30.,20.],[22.,20.]])
    assert iris_ratio(points,0,1,2)==pytest.approx(.6)
    assert iris_ratio(points*.1,0,1,2) is None


def test_random_challenge_nonce_order_expiry_and_static_frames():
    challenge=LiveChallenge(0.)
    assert set(challenge.actions)=={'blink','turn_left','turn_right','nod'}
    assert len(challenge.actions)==4
    assert 'actions' not in challenge.report(0.)
    with pytest.raises(ChallengeRequestError): challenge.validate('wrong',challenge.frame_token,0,0.)
    old=challenge.frame_token
    image=np.zeros((200,300,3),np.uint8)
    challenge.update(observation(),image,.2,face_extract)
    with pytest.raises(ChallengeRequestError): challenge.validate(challenge.id,old,0,.5)
    for t in (.5,.8,1.1): challenge.update(observation(),image,t,face_extract)
    assert challenge.status=='failed' and challenge.reason=='repeated_frame'
    expired=LiveChallenge(0.)
    result=expired.update(observation(),image,expired.lifetime,face_extract)
    assert result['reason']=='challenge_timeout' and result['expires_in']==0


@pytest.mark.parametrize('gaze',[.5,None])
def test_full_motion_sequence_with_return_to_center_and_multiple_identity_samples(gaze):
    challenge=LiveChallenge(0.)
    tick=0
    def send(obs):
        nonlocal tick
        tick+=1
        return challenge.update(dict(obs,gaze_horizontal=gaze),np.full((10,10,3),tick%256,np.uint8),tick*.2,face_extract)
    for _ in range(6): send(observation())
    assert challenge.baseline is not None
    for action in challenge.actions:
        for _ in range(2): send(observation())
        active=action_observation(action)
        for _ in range(3): send(active)
        if action=='blink': send(observation())
        assert challenge.phase=='return_center'
        for _ in range(2): send(observation())
    assert challenge.status=='passed'
    assert challenge.proof_valid(tick*.2)
    assert not challenge.proof_valid(tick*.2+46.)
    assert challenge.summary()['identity_samples']>=3
    assert challenge.summary()['presentation_attack_detection']=='not_certified'


def test_visible_deadline_does_not_stop_a_step_early_or_after_500_frames():
    challenge=LiveChallenge(0.)
    for tick in range(1,627):
        image=np.zeros((10,10,3),np.uint8)
        image[:]=[tick//256,tick%256,123]
        result=challenge.update(observation(),image,tick*.15,face_extract)
        assert result['status']=='running'
    assert challenge.baseline is not None
    assert challenge.index==0 and challenge.checked_frames>500
    assert result['expires_in']>0 and tick*.15>90


def test_return_to_center_accepts_a_small_angle_without_requiring_iris_tracking():
    challenge=LiveChallenge(0.)
    challenge.baseline={'yaw':0.,'pitch':0.,'gaze':None}
    assert challenge.neutral(observation(yaw=9.,pitch=9.,gaze=None))
    assert not challenge.neutral(observation(yaw=11.,gaze=None))


def test_wink_static_pose_wrong_action_and_unreliable_quality_cannot_pass():
    challenge=LiveChallenge(0.)
    challenge.actions=['blink','turn_left','turn_right','nod']
    for tick in range(1,9):
        challenge.update(observation(),np.full((10,10,3),tick,np.uint8),tick*.2,face_extract)
    wink=observation(blink=.9); wink['blink_right']=.1
    for tick,obs in enumerate([wink,wink,observation(),observation(yaw=20),observation()],9):
        challenge.update(obs,np.full((10,10,3),tick,np.uint8),tick*.2,face_extract)
    assert challenge.index==0 and challenge.phase=='action'
    for tick in range(15,47):
        challenge.update(dict(face_count=0,quality_ok=False,problems=['face_missing']),
                         np.full((10,10,3),tick,np.uint8),tick*.2,face_extract)
    assert challenge.status=='failed' and challenge.reason=='face_lost'


def test_multiple_faces_and_identity_switch_invalidate_evidence():
    image=np.zeros((10,10,3),np.uint8)
    challenge=LiveChallenge(0.)
    challenge.update(dict(face_count=2),image,.2,face_extract)
    assert challenge.status=='failed' and challenge.reason=='multiple_faces'
    challenge=LiveChallenge(0.)
    challenge.update(observation(),image,.2,face_extract)
    challenge.update(observation(),image+1,1.,lambda im:(im,np.array([[0.,1.]]),{}))
    assert challenge.reason=='identity_changed' and not challenge.embeddings
