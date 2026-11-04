import collections
import numpy as np
import pytest
from research.labels_schema import field,in_frame,validate_field,validate_review
from research.labels_import import split_for
from research.labels_audit import homography,project,clipped_polygon,area

def example():
    return field('field01','AUTHOR VALUE',[[1,2],[9,2],[9,7],[1,7]],10,10,
                 origin='author_template_projection',annotation_ref={'field':'field01'})

def test_native_key_does_not_invent_semantics_or_legibility():
    value=example()
    assert value['reference_text']=='AUTHOR VALUE'
    assert value['semantic_key'] is None
    assert value['frame_visibility']['status']=='in_frame'
    assert value['readability']['status']=='unassessed'
    assert value['readability']['observed_transcript'] is None

def test_quality_label_cannot_be_readability():
    value=example();value['readability']['status']='Clean'
    with pytest.raises(ValueError):validate_field(value,10,10)

@pytest.mark.parametrize('quad',[[[0,0],[float('nan'),0],[5,5],[0,5]],[[0,0],[1,0],[2,0],[3,0]]])
def test_invalid_geometry_rejected(quad):
    with pytest.raises(ValueError):field('key','TEXT',quad,10,10,origin='author_template',annotation_ref={})

def test_independent_clipping_matches_half_and_absent():
    quad=[[-5,0],[5,0],[5,10],[-5,10]]
    value=in_frame(quad,10,10)
    assert value['status']=='partial_frame'
    assert value['area_fraction']==pytest.approx(.5)
    assert area(clipped_polygon(quad,10,10))/area(quad)==pytest.approx(.5)
    assert in_frame([[-10,0],[-5,0],[-5,5],[-10,5]],10,10)['status']=='out_of_frame'

def test_independent_homography_maps_all_corners():
    source=[[0,0],[100,0],[100,60],[0,60]];dest=[[20,30],[170,15],[150,120],[5,110]]
    assert np.allclose(project(source,homography(source,dest)),dest,atol=1e-8)

def test_split_is_by_fifty_document_groups():
    counts=collections.Counter(split_for(i) for i in range(1,51))
    assert counts=={'train':30,'development':10,'test':10}
    assert split_for(7)==split_for(7)

@pytest.mark.parametrize('status,text',[('readable',''),('partial',''),('unreadable','GUESSED'),('not_present','GUESSED'),('language_unknown','GUESSED')])
def test_review_does_not_guess_absent_values(status,text):
    with pytest.raises(ValueError):validate_review({'reviewer':'A','languages':['vi'],'independent':True,
        'items':[{'field_id':'f','status':status,'text':text}]})

def test_duplicate_review_fields_rejected():
    with pytest.raises(ValueError):validate_review({'reviewer':'A','languages':['vi'],'independent':True,
        'items':[{'field_id':'f','status':'uncertain','text':''}]*2})
