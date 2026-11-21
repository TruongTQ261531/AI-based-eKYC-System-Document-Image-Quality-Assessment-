from PIL import Image
from research.evidence_contract.oracle_reliability import pixel_lineage_audit as pixel
from research.evidence_contract.oracle_reliability.corpus_audit import exposure_state
from research.evidence_contract.oracle_reliability.verify_p2 import cross_role_patterns


def test_exact_and_near_do_not_merge_identities(tmp_path):
    original=Image.new('RGB',(80,50))
    original.putdata([(x*3,y*4,120) for y in range(50) for x in range(80)])
    original.save(tmp_path/'first.png')
    (tmp_path/'copy.png').write_bytes((tmp_path/'first.png').read_bytes())
    original.save(tmp_path/'same.bmp')
    original.crop((2,0,80,50)).resize((40,25)).save(tmp_path/'crop.png')
    rows=[]
    for name,pid in [('first.png','A'),('copy.png','B'),('same.bmp',None),('crop.png','A')]:
        row=pixel.inspect(tmp_path/name,tmp_path)
        row.update(path=name,records=[{'physical_id':pid}])
        rows.append(row)
    report,groups=pixel.summarize(rows)
    assert report['decoded']==4 and report['file_duplicate_groups']==1
    assert report['pixel_duplicate_groups']==report['exact_pixel_multiple_physical_ids']==1
    assert groups==[[0,1,2,3]] and report['physical_ids']==2
    assert report['unknown_metadata_entries']['physical_id']==1
    assert exposure_state([])=='EXPOSURE_UNKNOWN'


def test_bad_inputs(tmp_path):
    (tmp_path/'broken.png').write_bytes(b'not an image')
    bad=pixel.inspect(tmp_path/'broken.png',tmp_path)
    assert 'file' in bad and 'pixel' not in bad and 'error' in bad
    assert pixel.inspect(tmp_path/'missing.png',tmp_path)['error']=='FileNotFoundError'
    assert pixel.inspect(tmp_path.parent/'other.png',tmp_path)['error']=='outside_root'
    assert pixel.inspect(tmp_path/'..'/'other.png',tmp_path)['error']=='outside_root'


def test_alias_exclusion(tmp_path,monkeypatch):
    # Windows reparse bit can be simulated on runners without symlink privilege.
    from types import SimpleNamespace
    from pathlib import Path
    path=tmp_path/'redirect'
    path.mkdir()
    real=Path.lstat
    def patched(p):
        if p==path:
            return SimpleNamespace(st_mode=real(p).st_mode,st_file_attributes=0x400)
        return real(p)
    monkeypatch.setattr(Path,'lstat',patched)
    assert list(pixel.inventory(tmp_path))==[(path,'path_alias')]


def test_declared_parent_must_exist_by_bytes():
    rows=[dict(path='a',file='abc',records=[]),
          dict(path='b',file='def',records=[dict(original_sha256='abc',source_sha256='missing')])]
    report,_=pixel.summarize(rows)
    assert report['file_bound_parent_links']==1 and rows[1]['bound_parent_files']==['abc']


def test_mpo_hashes_both_frames_and_single_frame_cache_reuses_only_matching_bytes(tmp_path):
    image=Image.new('RGB',(32,24),'white')
    path=tmp_path/'picture.jpg'
    image.save(path,format='JPEG')
    first=pixel.inspect(path,tmp_path)
    cache={first['file']:{k:first[k] for k in ('pixel','size','dhash')}}
    assert pixel.inspect(path,tmp_path,cache)==first
    image.save(path,format='MPO',save_all=True,append_images=[Image.new('RGB',(32,24),'black')])
    multiple=pixel.inspect(path,tmp_path,cache)
    assert multiple['file']!=first['file'] and len(multiple['additional_frames'])==1
    assert multiple['pixel']!=multiple['additional_frames'][0]['pixel']


def test_unreadable_second_mpo_frame_preserves_primary(tmp_path):
    path = tmp_path / 'two_frames.jpg'
    primary = Image.new('RGB', (32, 24), 'white')
    primary.save(path, format='MPO', save_all=True, append_images=[Image.new('RGB', (32, 24), 'black')])
    intact = pixel.inspect(path, tmp_path)
    raw = path.read_bytes()
    second = raw.index(b'\xff\xd8\xff', 3)
    path.write_bytes(raw[:second])
    partial = pixel.inspect(path, tmp_path)
    assert partial['pixel'] == intact['pixel']
    assert partial['additional_frames'] == []
    assert partial['additional_frame_errors'][0]['index'] == 1
    report, _ = pixel.summarize([dict(partial, path='two_frames.jpg')])
    assert report['decoded'] == 1 and report['excluded_entries'] == 0
    assert report['additional_frames_hashed'] == 0
    assert sum(report['additional_frame_errors'].values()) == 1


def test_cross_role_counts_each_exact_pixel_group_once():
    train = dict(dataset='first', role='train')
    test = dict(dataset='second', role='test')
    rows = [dict(pixel='a', records=[train, train]), dict(pixel='a', records=[test]),
            dict(pixel='b', records=[train, test]), dict(pixel='c', records=[train]),
            dict(error='decode', records=[train, test])]
    assert cross_role_patterns(rows) == [
        dict(collection_roles=[dict(collection='first', role='train'), dict(collection='second', role='test')],
             pixel_groups=2)]
