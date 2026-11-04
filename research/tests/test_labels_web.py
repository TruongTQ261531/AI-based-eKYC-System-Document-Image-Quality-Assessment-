import hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
import pytest
from research.labels_web import create_app
from research.labels_review import store,events,export_verified

SECRET='AUTHOR_SECRET_MUST_NOT_APPEAR_IN_BLIND_PAYLOAD'

@pytest.fixture
def sample(tmp_path):
    path=tmp_path/'image.png';Image.new('RGB',(20,20),'white').save(path)
    return dict(uid='private-sample',input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path),
        width=20,height=20,role='test',source='authored',coordinate_mode='raw_pixels',quality=None,
        fields=[dict(field_id='f1',raw_key='field01',semantic_key=None,polygon=[[1,1],[19,1],[19,10],[1,10]],
                     reference_text=SECRET,glyphs=[{'character':SECRET}],geometry_origin='renderer_ink')])

@pytest.fixture
def client(sample,tmp_path):
    key='a'*64
    def lookup(given):
        if given!=key:raise KeyError(given)
        return sample
    app=create_app(lookup,lambda *a:(1,[dict(id=key,name='sample')]),lambda:[key],tmp_path/'reviews.sqlite3')
    with TestClient(app) as value:yield value

def payload(reviewer='A'):
    return dict(reviewer=reviewer,languages=['vi'],independent=True,items=[dict(field_id='f1',status='readable',text='OBSERVED')])

def test_blind_route_never_sends_answer_or_glyph_characters(client):
    r=client.get('/api/blind/'+'a'*64)
    assert r.status_code==200 and SECRET not in r.text and 'glyphs' not in r.text
    assert r.json()['answers_included'] is False

def test_catalog_identifies_author_answer_as_unverified(client):
    r=client.get('/api/sample/'+'a'*64)
    assert r.status_code==200 and SECRET in r.text
    assert 'chưa xác minh' in r.json()['answer_source']

def test_review_append_does_not_change_reference(client,sample):
    r=client.post('/api/reviews/'+'a'*64,json=payload())
    assert r.status_code==200 and r.json()['released_reference_changed'] is False
    assert sample['fields'][0]['reference_text']==SECRET
    data=client.get('/api/reviews/export').json()
    assert len(data['events'])==1 and data['events'][0]['independence_verified_by_system'] is False

def test_extra_reference_text_cannot_overwrite_released_labels(client):
    p=payload();p['reference_text']='REPLACEMENT'
    assert client.post('/api/reviews/'+'a'*64,json=p).status_code==422

@pytest.mark.parametrize('origin',['https://example.invalid','http://localhost:9999','http://localhost:bad'])
def test_cross_origin_or_malformed_origin_rejected(client,origin):
    assert client.post('/api/reviews/'+'a'*64,json=payload(),headers={'Origin':origin}).status_code==403

def test_image_contains_no_original_exif(client):
    import io
    r=client.get('/api/image/'+'a'*64)
    assert r.status_code==200 and r.headers['cache-control']=='no-store'
    with Image.open(io.BytesIO(r.content)) as image:assert len(image.getexif())==0 and image.size==(20,20)

def test_unknown_hash_cannot_read_an_arbitrary_file(client):
    assert client.get('/api/image/'+'b'*64).status_code==404

def test_two_self_declared_codes_do_not_become_verified_humans(sample,tmp_path):
    path=tmp_path/'separate-review-test.sqlite3'
    store(sample,payload('A'),path);store(sample,payload('B'),path)
    assert len(events(path))==2
    assert export_verified(path)==[]
