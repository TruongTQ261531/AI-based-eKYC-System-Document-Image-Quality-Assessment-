import time
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import ekyc.api as api
from test_live_challenge import observation,action_observation,face_extract


@pytest.fixture
def live_client(monkeypatch):
    clock=SimpleNamespace(now=time.monotonic())
    monkeypatch.setattr(api,'time',SimpleNamespace(monotonic=lambda:clock.now))
    observer=SimpleNamespace(current=observation())
    observer.observe=lambda image: observer.current
    class Pipeline:
        faces=SimpleNamespace(extract=face_extract)
        def match_live_selfie(self,image,embedding,samples):
            assert len(samples)>=3
            return dict(status='matched',matching={'cosine_similarity':.9,'threshold':.363},
                        identity_consistent=True,identity_verified=False,issues=[])
    monkeypatch.setattr(api,'get_observer',lambda:observer)
    monkeypatch.setattr(api,'get_pad',lambda:SimpleNamespace(check=lambda image,faces:observer.current['pad']))
    monkeypatch.setattr(api,'get_pipeline',lambda:Pipeline())
    with TestClient(api.app,base_url='http://localhost') as client:
        api.sessions['test']=dict(embedding=np.array([[1.,0.]]),fields={},confirmed=True,expires=clock.now+600)
        yield client,clock,observer


def image(number=0):
    return cv2.imencode('.jpg',np.full((300,500,3),number%255,np.uint8))[1].tobytes()


def test_camera_challenge_api_end_to_end_and_no_photo_only_bypass(live_client):
    client,clock,observer=live_client
    headers={'X-Session-Token':'test'}
    assert client.post('/api/selfie',headers=headers,files={'image':('s.jpg',image())}).status_code==409
    packet=client.post('/api/liveness/start',headers=headers).json()
    assert packet['status']=='running'
    counter=0
    def frame(obs):
        nonlocal packet,counter
        observer.current=obs; clock.now+=.2; counter+=1
        frame_headers=dict(headers,**{'X-Liveness-Id':packet['challenge_id'],
            'X-Frame-Token':packet['frame_token'],'X-Frame-Sequence':str(packet['next_sequence'])})
        response=client.post('/api/liveness/frame',headers=frame_headers,files={'image':('f.jpg',image(counter))})
        assert response.status_code==200,response.text
        previous=packet; packet=response.json()
        return previous,frame_headers
    for _ in range(6): frame(observation())
    # Reading/performing one action may take longer than the old hidden 18 seconds.
    clock.now+=25
    while packet['status']=='running':
        action=packet['action']
        for _ in range(2): frame(observation())
        for _ in range(3): frame(action_observation(action))
        if action=='blink': frame(observation())
        assert packet['phase']=='return_center'
        for _ in range(2): frame(observation())
    assert packet['status']=='passed' and packet['completed']==4 and packet['total']==4
    observer.current=observation()
    result=client.post('/api/selfie',headers=headers,files={'image':('s.jpg',image(100))})
    assert result.status_code==200,result.text
    data=result.json()
    assert data['status']=='matched' and data['liveness_checked'] and data['liveness_passed']
    assert not data['identity_verified'] and not api.sessions


def test_nonce_replay_restart_cancel_and_expiry(live_client):
    client,clock,observer=live_client
    headers={'X-Session-Token':'test'}
    first=client.post('/api/liveness/start',headers=headers).json()
    second=client.post('/api/liveness/start',headers=headers).json()
    assert first['challenge_id']!=second['challenge_id']
    def submit(packet):
        return client.post('/api/liveness/frame',headers=dict(headers,**{
            'X-Liveness-Id':packet['challenge_id'],'X-Frame-Token':packet['frame_token'],
            'X-Frame-Sequence':str(packet['next_sequence'])}),files={'image':('f.jpg',image())})
    assert submit(first).status_code==409
    response=submit(second)
    assert response.status_code==200
    clock.now+=.2
    assert submit(second).status_code==409
    assert client.delete('/api/liveness',headers=headers).status_code==200
    assert submit(response.json()).status_code==409
    third=client.post('/api/liveness/start',headers=headers).json()
    clock.now+=181
    assert submit(third).json()['status']=='failed'
    assert client.post('/api/selfie',headers=headers,files={'image':('s.jpg',image())}).status_code==409
    assert client.post('/api/liveness/start',headers=headers).status_code==429


def test_frame_limits_and_no_unconfirmed_or_forged_measurements(live_client):
    client,clock,observer=live_client
    headers={'X-Session-Token':'test'}
    api.sessions['test']['confirmed']=False
    assert client.post('/api/liveness/start',headers=headers).status_code==409
    api.sessions['test']['confirmed']=True
    assert client.post('/api/selfie',headers=headers,files={'image':('s.jpg',image())},
                       data={'liveness_passed':'true','yaw':'30','blinks':'10'}).status_code==409
    assert client.post('/api/liveness/frame',headers=headers,content=b'x'*(api.MAX_LIVE_BODY+1)).status_code==413
    packet=client.post('/api/liveness/start',headers=headers).json()
    frame_headers=dict(headers,**{'X-Liveness-Id':packet['challenge_id'],
        'X-Frame-Token':packet['frame_token'],'X-Frame-Sequence':'0'})
    huge=cv2.imencode('.jpg',np.zeros((1200,1200,3),np.uint8))[1].tobytes()
    assert client.post('/api/liveness/frame',headers=frame_headers,files={'image':('f.jpg',huge)}).status_code==413


def test_cancelled_inflight_frame_does_not_delete_the_document_session(live_client):
    client,clock,observer=live_client
    headers={'X-Session-Token':'test'}
    packet=client.post('/api/liveness/start',headers=headers).json()
    def cancel_during_inference(image):
        api.sessions['test'].pop('liveness',None)
        return observation()
    observer.observe=cancel_during_inference
    response=client.post('/api/liveness/frame',headers=dict(headers,**{
        'X-Liveness-Id':packet['challenge_id'],'X-Frame-Token':packet['frame_token'],'X-Frame-Sequence':'0'}),
        files={'image':('f.jpg',image())})
    assert response.status_code==409
    assert api.sessions['test']['confirmed']


def test_final_selfie_must_match_the_person_in_the_challenge():
    from ekyc.pipeline import EKYCPipeline
    pipeline=EKYCPipeline()
    pipeline._faces=SimpleNamespace(extract=lambda image:(image,np.array([[0.,1.]]),{}))
    result=pipeline.match_live_selfie(np.zeros((200,300,3),np.uint8),np.array([[0.,1.]]),
                                      [np.array([[1.,0.]])]*3)
    assert result['status']=='not_matched' and result['identity_consistent'] is False
    assert result['issues'][0]['code']=='selfie_identity_changed'


def test_spoof_frame_rejected_despite_client_claiming_live(live_client):
    client,clock,observer=live_client
    headers={'X-Session-Token':'test'}
    packet=client.post('/api/liveness/start',headers=headers).json()
    observer.current=dict(observation(),pad={'decision':'spoof','method':'minifasnet_v2_v1se_rgb_v1'})
    response=client.post('/api/liveness/frame',headers=dict(headers,**{
        'X-Liveness-Id':packet['challenge_id'],'X-Frame-Token':packet['frame_token'],'X-Frame-Sequence':'0'}),
        files={'image':('f.jpg',image())},data={'pad':'live','liveness_passed':'true'})
    assert response.json()['status']=='failed' and response.json()['reason']=='spoof_detected'
    assert client.post('/api/selfie',headers=headers,files={'image':('s.jpg',image())}).status_code==409


@pytest.mark.parametrize('decision,code',[('spoof',403),('uncertain',422)])
def test_final_photo_pad_recheck_revokes_proof_and_blocks_matching(live_client,monkeypatch,decision,code):
    from ekyc.live_challenge import LiveChallenge
    client,clock,observer=live_client
    # Construct only the pre-existing proof; final capture must independently pass PAD.
    challenge=LiveChallenge(clock.now)
    challenge.status='passed'; challenge.passed_at=clock.now; challenge.pad_consecutive_live=6
    challenge.baseline={'yaw':0.,'pitch':0.,'gaze':.5}
    api.sessions['test']['liveness']=challenge
    observer.current=dict(observation(),pad={'decision':decision,'method':'minifasnet_v2_v1se_rgb_v1'})
    def forbidden_match(*args): raise AssertionError('Must not run Module 5')
    monkeypatch.setattr(api,'get_pipeline',lambda:SimpleNamespace(faces=object(),match_live_selfie=forbidden_match))
    response=client.post('/api/selfie',headers={'X-Session-Token':'test'},files={'image':('s.jpg',image())})
    assert response.status_code==code and response.json()['liveness_invalidated']
    assert not challenge.proof_valid(clock.now)
    assert 'test' in api.sessions


def test_pad_load_failure_never_creates_a_motion_only_challenge(live_client,monkeypatch):
    client,_,_=live_client
    def unavailable(): raise FileNotFoundError('model unavailable')
    monkeypatch.setattr(api,'get_pad',unavailable)
    response=client.post('/api/liveness/start',headers={'X-Session-Token':'test'})
    assert response.status_code==503 and 'liveness' not in api.sessions['test']


def test_pad_runtime_failure_on_final_photo_revokes_proof(live_client,monkeypatch):
    from ekyc.live_challenge import LiveChallenge
    from ekyc.io import StageError
    client,clock,_=live_client
    challenge=LiveChallenge(clock.now)
    challenge.status='passed'; challenge.passed_at=clock.now; challenge.pad_consecutive_live=6
    api.sessions['test']['liveness']=challenge
    def broken(*args): raise StageError('invalid model output')
    monkeypatch.setattr(api,'get_pad',lambda:SimpleNamespace(check=broken))
    response=client.post('/api/selfie',headers={'X-Session-Token':'test'},files={'image':('s.jpg',image())})
    assert response.status_code==503 and 'liveness' not in api.sessions['test']
