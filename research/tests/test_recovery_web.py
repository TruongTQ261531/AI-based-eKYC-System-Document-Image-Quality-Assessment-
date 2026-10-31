import io
import json

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import research.recovery_web as web


def image_bytes():
    buffer=io.BytesIO();Image.new('RGB',(100,80),'white').save(buffer,format='JPEG');return buffer.getvalue()


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(web,'OUT',tmp_path)
    with TestClient(web.app,base_url='http://localhost:8001') as result:yield result


def test_page_and_results_do_not_invent_unfinished_study(client):
    assert client.get('/').status_code==200
    assert client.get('/api/results').json()['rows']==[]
    response=client.post('/api/scan',content=image_bytes(),headers={'content-type':'image/jpeg'})
    assert response.status_code==503 and 'thay' in response.json()['detail']
    assert response.headers['cache-control']=='no-store'


def test_cross_origin_and_arbitrary_asset_are_blocked(client):
    assert client.post('/api/scan',content=b'x',headers={'origin':'https://evil.example','content-type':'image/jpeg'}).status_code==403
    assert client.get('/assets/secrets.json').status_code==404
    assert client.get('/api/specimen/private').status_code==404


def test_raw_body_limit_applies_before_decode(client,monkeypatch):
    monkeypatch.setattr(web,'MAX_BODY',20)
    assert client.post('/api/scan',content=b'x'*21,headers={'content-type':'image/jpeg'}).status_code==413


def test_invalid_image_error_does_not_echo_body(client,monkeypatch):
    monkeypatch.setattr(web,'locked_model',lambda:{})
    secret=b'private-test-value-should-not-be-echoed'
    result=client.post('/api/scan',content=secret,headers={'content-type':'image/jpeg'})
    assert result.status_code==400 and secret.decode() not in result.text


def test_observed_fields_return_without_disk_or_identity_approval(client,monkeypatch,tmp_path):
    class Fake:
        def online(self,image,model):
            return dict(fields={'student_id':'MOCK42'},predictions=[],selected_policy='raw',primary_method='cascade_ridge',reader='rapid_latin_v5',
                review_recommended=True,warnings=['Check capture'],observed_corners=2,actual_wall_seconds=.1,actual_cpu_seconds=.1,
                ocr_executions=1,localizer_calls=1,_private_preview=np.zeros((80,100,3),np.uint8),liveness_evaluated=False,identity_approved=False)
    monkeypatch.setattr(web,'locked_model',lambda:{})
    monkeypatch.setattr(web,'engine',lambda:Fake())
    before=set(tmp_path.iterdir());response=client.post('/api/scan',content=image_bytes(),headers={'content-type':'image/jpeg'})
    assert response.status_code==200
    data=response.json();assert data['fields']=={'student_id':'MOCK42'} and not data['identity_approved']
    assert '_private_preview' not in data and set(tmp_path.iterdir())==before
    assert response.headers['cache-control']=='no-store'


def test_busy_inference_is_rejected_without_second_model_call(client,monkeypatch):
    monkeypatch.setattr(web,'locked_model',lambda:{})
    web.inference_lock.acquire()
    try:assert client.post('/api/scan',content=image_bytes(),headers={'content-type':'image/jpeg'}).status_code==429
    finally:web.inference_lock.release()


def test_model_hash_tampering_is_detected(tmp_path,monkeypatch):
    monkeypatch.setattr(web,'OUT',tmp_path)
    (tmp_path/'selector_models.json').write_text('{}')
    (tmp_path/'selector_lock.json').write_text(json.dumps({'signature':'x','model_sha256':'wrong'}))
    with pytest.raises(web.HTTPException) as error:web.locked_model()
    assert error.value.status_code==503


def test_deployed_parser_validation_does_not_open_training_annotations(tmp_path,monkeypatch):
    from research.benchmark import digest
    import research.layout_kie_study as study
    monkeypatch.setattr(web,'OUT',tmp_path)
    monkeypatch.setattr(study,'signature',lambda:(_ for _ in ()).throw(AssertionError('Training data must not be opened')))
    lock={'signature':'offline-study','deployment_approved_on_development':True}
    (tmp_path/'layout_kie_lock.json').write_text(json.dumps(lock),encoding='utf-8')
    (tmp_path/'selector_models.json').write_text('{}',encoding='utf-8')
    seal=dict(source_lock_sha256=digest(tmp_path/'layout_kie_lock.json'),study_signature='offline-study',
        model_sha256=digest(tmp_path/'selector_models.json'),deployment_approved_on_development=True,
        code_sha256={'research/layout_kie.py':digest(web.ROOT/'layout_kie.py')})
    (tmp_path/'kie_deployment.json').write_text(json.dumps(seal),encoding='utf-8')
    assert web.kie_settings()==lock
    seal['code_sha256']['research/layout_kie.py']='tampered'
    (tmp_path/'kie_deployment.json').write_text(json.dumps(seal),encoding='utf-8')
    with pytest.raises(ValueError):web.kie_settings()
