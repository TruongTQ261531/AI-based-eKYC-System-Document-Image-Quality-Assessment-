import hashlib
import json
from PIL import Image
from research import labels_study as study

def test_runner_passes_only_pixels_and_retains_malformed_outputs(tmp_path,monkeypatch):
    path=tmp_path/'input.png';Image.new('RGB',(16,16),(120,140,160)).save(path)
    image_sha=hashlib.sha256(path.read_bytes()).hexdigest();received=[]
    rows=[]
    for i,role in enumerate(('development','test')):
        rows.append(dict(uid='case-'+str(i),physical_id='doc-'+str(i),source='authored',role=role,device='renderer',
            layout='test-layout',condition='seen_layout_seen_font',capture='full',path='input.png',input_sha256=image_sha,
            pixel_sha256='1'*64,coordinate_mode='raw_pixels',target={'full_name':'SECRET_AUTHOR_REFERENCE'},
            source_refs={'full_name':[dict(value='SECRET_AUTHOR_REFERENCE',kind='body',source='f',priority=0)]}))
    def predict(image):
        assert isinstance(image,Image.Image)
        assert image.size==(16,16) and 'target' not in image.info
        received.append(True)
        return dict(text='{',wall_seconds=.1,cpu_seconds=.01,generated_tokens=None,predictor_receives='pixels_only')
    monkeypatch.setattr(study,'ROOT',tmp_path);monkeypatch.setattr(study,'CACHE',tmp_path/'cache');monkeypatch.setattr(study,'OUT',tmp_path/'results')
    monkeypatch.setattr(study,'verify_lock',lambda:'fixture-signature');monkeypatch.setattr(study,'sample_rows',lambda:rows)
    monkeypatch.setattr(study,'predictor',lambda name:predict)
    study.run('rapid_v4')
    output=json.loads((tmp_path/'results/evaluation_rapid_v4.json').read_text(encoding='utf-8'))
    assert len(received)==2 and len(output['rows'])==2
    assert all(not row['valid_json'] and row['reference']==1 and row['predicted']==0 for row in output['rows'])
    assert 'SECRET_AUTHOR_REFERENCE' not in json.dumps(output)
    events=[json.loads(s) for s in (tmp_path/'cache/execution_events.jsonl').read_text().splitlines()]
    assert sum(e['status']=='begin' for e in events)==2
    assert sum(e['status']=='completed' for e in events)==2
    study.run('rapid_v4')
    assert len(received)==2  # A cache resume is not another model invocation.
