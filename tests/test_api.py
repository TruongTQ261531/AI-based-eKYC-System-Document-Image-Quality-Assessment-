from fastapi.testclient import TestClient
from ekyc.api import app

client = TestClient(app, base_url='http://localhost')


def test_home_health_and_path_safety():
    assert client.get('/').status_code == 200
    assert client.get('/api/health').json()['status'] in ('ready','setup_required')
    assert client.get('/api/results/not-a-run/result.json').status_code == 404
    assert client.get('/api/results/'+'a'*32+'/secrets.txt').status_code == 404


def test_invalid_upload_and_corners():
    assert client.post('/api/verify', files={'card':('x.exe',b'x')}).status_code == 400
    assert client.post('/api/verify', files={'card':('x.jpg',b'')}).status_code == 400
    assert client.post('/api/verify', files={'card':('x.jpg',b'x')},data={'corners':'[]'}).status_code == 400
