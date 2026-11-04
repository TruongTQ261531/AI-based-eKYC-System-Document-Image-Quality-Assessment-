import pytest
from fastapi.testclient import TestClient
from research.labels_issues import store,events,active,status
from research.labels_review import events as reviews,status as review_status
from research.labels_web import create_app

def sample():return dict(uid='fixture',input_sha256='f'*64,fields=[{'reference_text':'UNCHANGED_AUTHOR'}])

def test_flag_and_withdraw_are_append_only_and_not_readability_labels(tmp_path):
    path=tmp_path/'issues.sqlite3';source=sample()
    first=store(source,dict(reviewer='A',category='wrong_region',reason='Wrong text region'),path)
    assert first['image_deleted'] is False and first['benchmark_case_removed'] is False
    assert status(path)['active_flagged_images']==1 and len(active(path))==1
    assert reviews(path)==[] and review_status(path)['single_review_images']==0
    store(source,dict(reviewer='A',action='withdraw',category='other',reason=''),path)
    assert len(events(path))==2 and not active(path)
    assert source['fields'][0]['reference_text']=='UNCHANGED_AUTHOR'

@pytest.mark.parametrize('change',[dict(reason=''),dict(reviewer=''),dict(action='delete'),dict(category='bad_quality')])
def test_issue_needs_specific_reason_and_never_accepts_delete(tmp_path,change):
    payload=dict(reviewer='A',category='wrong_region',reason='Wrong text region');payload.update(change)
    with pytest.raises(ValueError):store(sample(),payload,tmp_path/'bad.sqlite3')

def test_issue_API_does_not_require_fake_field_assessments(tmp_path):
    key='a'*64;source=sample()
    def lookup(given):
        if given!=key:raise KeyError(given)
        return source
    app=create_app(lookup,lambda *args:(0,[]),lambda:[],tmp_path/'api.sqlite3')
    with TestClient(app) as client:
        response=client.post('/api/issues/'+key,json=dict(reviewer='A',category='not_document',reason='Not the intended document type'))
        assert response.status_code==200 and response.json()['benchmark_changed'] is False
        assert client.get('/api/issues/export').json()['active']['active_flagged_images']==1
        assert client.get('/api/reviews/export').json()['events']==[]

def test_unselected_readability_is_not_silently_submitted():
    from research.labels_schema import validate_review
    with pytest.raises(ValueError):validate_review(dict(reviewer='A',languages=['vi'],independent=True,
        items=[dict(field_id='f',status='',text='')]))
