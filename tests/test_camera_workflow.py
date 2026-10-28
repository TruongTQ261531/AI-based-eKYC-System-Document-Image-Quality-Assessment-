import io
import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import ekyc.api as api
from ekyc.config import Settings
from ekyc.io import StageError
from ekyc.module3_ocr import parse_lines, form_fields
from ekyc.pipeline import EKYCPipeline


@pytest.fixture
def client(monkeypatch):
    class Pipeline:
        def process_document(self, image):
            assert image.shape[:2] == (400, 640)
            return dict(status='review', fields=dict(full_name='OCR NAME', id_number='001234567890',
                        dob='', gender='', address='')), np.array([[1., 0.]])
        def match_selfie(self, image, embedding):
            return dict(status='matched', matching={'cosine_similarity':.9,'threshold':.363},
                        liveness_checked=False, identity_verified=False)
    monkeypatch.setattr(api, 'get_pipeline', lambda: Pipeline())
    with TestClient(api.app, base_url='http://localhost') as client:
        yield client


def picture():
    return cv2.imencode('.jpg', np.full((400,640,3),127,np.uint8))[1].tobytes()


def document(client):
    response = client.post('/api/document', files={'card':('camera.jpg',picture(),'image/jpeg')})
    assert response.status_code == 200
    return response.json()


def test_photo_only_flow_cannot_skip_camera_challenge(client):
    result = document(client)
    headers = {'X-Session-Token':result['session_token']}
    assert result['fields']['id_number'] == '001234567890'
    assert result['fields']['gender'] == ''
    assert client.post('/api/selfie',headers=headers,files={'image':('selfie.jpg',picture())}).status_code == 409
    edited = dict(full_name='Edited name', id_number='000123456789', dob='1999-02-03',gender='Nữ',address='Updated address')
    response = client.post('/api/confirm',headers=headers,json=edited)
    assert response.json()['fields'] == edited
    assert response.json()['fields_verified'] is False
    assert response.json()['liveness_required'] is True
    assert client.post('/api/selfie',headers=headers,files={'image':('selfie.jpg',picture())}).status_code == 409
    assert result['session_token'] in api.sessions


def test_private_expired_and_deleted_sessions(client):
    result = document(client)
    token = result['session_token']
    assert client.post('/api/confirm',json={}).status_code == 401
    assert client.post('/api/confirm',headers={'X-Session-Token':'wrong'},json={}).status_code == 401
    api.sessions[token]['expires'] = time.monotonic()-1
    assert client.post('/api/confirm',headers={'X-Session-Token':token},json={}).status_code == 401
    token = document(client)['session_token']
    assert client.delete('/api/session',headers={'X-Session-Token':token}).status_code == 200
    assert not api.sessions


def test_no_pii_in_validation_or_artifact_routes(client):
    response = client.post('/api/confirm',json={'full_name':'PRIVATE'*100})
    assert response.status_code == 422 and 'PRIVATE' not in response.text
    assert client.get('/api/results/'+'a'*32+'/id_face.jpg').status_code == 404
    for path in ('/','/api/health','/app.js'):
        response = client.get(path)
        assert response.headers['cache-control'] == 'no-store'
        assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert client.post('/api/document',headers={'Origin':'https://evil.example'},files={'card':('x.jpg',picture())}).status_code == 403
    assert client.get('/',headers={'Host':'evil.example'}).status_code in (400,403)


def test_invalid_date_and_oversized_body(client,monkeypatch):
    headers={'X-Session-Token':document(client)['session_token']}
    assert client.post('/api/confirm',headers=headers,json={'dob':'2000-02-30'}).status_code==422
    assert client.post('/api/confirm',headers=headers,content='x'*9000).status_code==413
    monkeypatch.setattr(api,'MAX_CARD',10)
    assert client.post('/api/document',files={'card':('x.jpg',picture())}).status_code==413


def test_quality_failure_cannot_create_session(client, monkeypatch):
    class Reject:
        def process_document(self,image):
            return {'status':'retake','reason':'quality_rejected'}, None
    monkeypatch.setattr(api,'get_pipeline',lambda:Reject())
    result=document(client)
    assert result['status']=='retake'
    assert 'session_token' not in result and not api.sessions


def test_missing_portrait_cannot_confirm_or_match_even_with_forged_client(client, monkeypatch):
    class NoPortrait:
        def process_document(self, image):
            return {'status':'review','fields':{'full_name':'OCR only'},'can_match_selfie':False}, None
        def match_selfie(self, *args):
            pytest.fail('Matching must not run without an ID embedding')
    monkeypatch.setattr(api, 'get_pipeline', lambda:NoPortrait())
    result = document(client)
    assert result['fields']['full_name'] == 'OCR only'
    headers = {'X-Session-Token':result['session_token']}
    assert client.post('/api/confirm', headers=headers, json={}).status_code == 409
    api.sessions[result['session_token']]['confirmed'] = True
    assert client.post('/api/selfie', headers=headers, files={'image':('s.jpg',picture())}).status_code == 409


def test_actual_pipeline_gate_no_disk_or_ocr(tmp_path,monkeypatch):
    pipeline=EKYCPipeline(Settings(output_dir=tmp_path))
    class Reject:
        def run(self,image): return {'passed':False,'label':'Blur'}
    pipeline._quality=Reject()
    response,embedding=pipeline.process_document(np.zeros((400,640,3),np.uint8))
    assert response['status']=='retake' and embedding is None
    assert list(tmp_path.iterdir())==[]


def test_actual_document_order_and_single_selfie(tmp_path,monkeypatch):
    from ekyc.module2_homography import Homography
    calls=[]
    frame=np.zeros((400,640,3),np.uint8)
    feature=np.array([[1.,0.]])
    class Quality:
        def run(self,image): calls.append('quality'); return {'passed':True}
    class OCR:
        def run(self,image,faces):
            calls.append('ocr'); return {'fields':{'full_name':'Name'}},image,feature
    class Faces:
        def extract(self,image): return image,feature,{}
    def rectify(self,image): calls.append('rectify'); return image,{'requires_review':True}
    monkeypatch.setattr(Homography,'run',rectify)
    pipeline=EKYCPipeline(Settings(output_dir=tmp_path))
    pipeline._quality,pipeline._ocr,pipeline._faces=Quality(),OCR(),Faces()
    response,embedding=pipeline.process_document(frame)
    assert calls==['quality','rectify','ocr']
    assert response['fields']['dob']==''
    result=pipeline.match_selfie(frame,embedding)
    assert result['status']=='matched' and result['liveness_checked'] is False
    assert list(tmp_path.iterdir())==[]


def test_vietnamese_ocr_and_unknown_fields():
    fields=parse_lines([{'text':'Họ và tên: Nguyễn Thị Ánh'}, {'text':'Giới tính: Nữ'},
                       {'text':'Số: 001234567890'}, {'text':'Ngày sinh: 03/02/1999'},
                       {'text':'Nơi thường trú: Hà Nội'}])
    assert fields['full_name']=='Nguyễn Thị Ánh'
    assert form_fields(fields)==dict(full_name='Nguyễn Thị Ánh',gender='Nữ',id_number='001234567890',dob='1999-02-03',address='Hà Nội')
    assert all(value=='' for value in form_fields({}).values())
    assert form_fields({'dob':'31/02/1999'})['dob']==''


def test_background_quality_failure_is_recovered_by_readable_card(monkeypatch):
    from ekyc.module2_homography import Homography
    frame=np.full((400,640,3),127,np.uint8);frame[:,::2]=50
    crop=frame[50:350,100:550]
    class Quality:
        def run(self,image): return dict(passed=image is crop,label='Blur',issues=[],warnings=[],
            metrics=dict(min_side=min(image.shape[:2]),contrast=30,p90=127))
    class OCR:
        def run(self,image,faces):
            assert image is crop
            return dict(fields={'full_name':'Test'},accepted_line_count=1),None,np.ones((1,2))
    monkeypatch.setattr(Homography,'run',lambda self,image:(crop,{'requires_review':True}))
    pipeline=EKYCPipeline();pipeline._quality=Quality();pipeline._ocr=OCR();pipeline._faces=object()
    result,feature=pipeline.process_document(frame)
    assert result['status']=='review' and feature is not None
    assert result['quality']['reason']=='document_text_recovered'


def test_unlocalized_text_never_uses_live_face_as_document_portrait(monkeypatch):
    from ekyc.module2_homography import Homography
    def unavailable(*args): raise StageError('No corners')
    monkeypatch.setattr(Homography,'run',unavailable)
    class OCR:
        def run_unlocalized(self,image): return dict(fields={},accepted_line_count=2,raw_lines=[]),None,None
    pipeline=EKYCPipeline();pipeline._quality=type('Quality',(),{'run':lambda self,image:{'passed':True}})()
    pipeline._ocr=OCR()
    result,feature=pipeline.process_document(np.zeros((400,640,3),np.uint8))
    assert result['status']=='review' and not result['can_match_selfie'] and feature is None


def test_confirm_accepts_only_additional_fields_read_in_current_session(client,monkeypatch):
    result=document(client);token=result['session_token'];api.sessions[token]['additional_field_keys']={'student_id','class_name'}
    headers={'X-Session-Token':token}
    response=client.post('/api/confirm',headers=headers,json={'additional_fields':{'student_id':'HS42','class_name':'12A1'}})
    assert response.status_code==200
    assert response.json()['fields']['additional_fields']['student_id']=='HS42'
    assert client.post('/api/confirm',headers=headers,json={'additional_fields':{'invented':'value'}}).status_code==422
