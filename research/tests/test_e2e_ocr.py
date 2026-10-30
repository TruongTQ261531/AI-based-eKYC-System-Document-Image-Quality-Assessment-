import cv2
import numpy as np
import pytest

from research.e2e_eval import score,target_fields
from research.e2e_pipeline import crop_support,warp_document,to_source,expand_quad
from research.support_regions import area,intersection


def sample(fields):
    return dict(width=200,height=100,gt=[[10,10],[190,10],[190,90],[10,90]],fields=fields)


def field(key,text,box):return dict(key=key,text=text,quad=box)


def test_rejected_or_missed_field_counts_as_error_not_removed():
    data=sample([field('id','12345',[[20,20],[90,20],[90,40],[20,40]])])
    result=score(data,[],False)
    assert result['eligible_fields']==1
    assert result['fields'][0]['cer']==1
    assert not result['fields'][0]['exact'] and not result['all_targets_exact']


def test_prediction_inverse_coordinates_match_source_field_without_gt_crop():
    data=sample([field('id','12345',[[20,20],[90,20],[90,40],[20,40]])])
    predicted=[dict(box=[[0,0],[70,0],[70,20],[0,20]],text='12345',confidence=.8)]
    mapped=to_source(predicted,np.array([[1,0,20],[0,1,20],[0,0,1]],float))
    result=score(data,mapped,True)
    assert result['fields'][0]['exact']
    assert predicted[0]['box'][0]==[0,0]


def test_split_predicted_words_can_map_to_one_field_but_not_two():
    data=sample([field('name','ABC DEF',[[10,10],[110,10],[110,40],[10,40]]),
                 field('id','9876',[[120,10],[190,10],[190,40],[120,40]])])
    predictions=[dict(box=[[12,12],[45,12],[45,38],[12,38]],text='ABC',confidence=.9),
                 dict(box=[[50,12],[105,12],[105,38],[50,38]],text='DEF',confidence=.8)]
    result=score(data,predictions,True)
    assert result['fields'][0]['exact'] and not result['fields'][1]['detected']


def test_partial_and_unsupported_fields_are_counted_explicitly():
    data=sample([field('partial','ABC',[[-50,20],[50,20],[50,40],[-50,40]]),
                 field('nonlatin','\u0410\u0411\u0412',[[20,20],[90,20],[90,40],[20,40]])])
    targets,counts=target_fields(data)
    assert targets==[] and counts==dict(partial=1,non_latin_or_invalid=1)
    assert score(data,[],True)['all_targets_exact'] is False


def test_support_mask_preserves_inside_and_does_not_mutate_input():
    image=np.zeros((100,200,3),np.uint8);original=image.copy()
    polygon=np.float32([[20,20],[120,20],[20,70]])
    masked,transform=crop_support(image,polygon,True)
    plain,_=crop_support(image,polygon,False)
    assert np.array_equal(image,original) and np.all(plain==0)
    assert np.all(masked[-1,-1]==255) and np.all(masked[1,1]==0)
    assert np.allclose(transform@np.array([0,0,1]),[20,20,1])


def test_expanded_warp_preserves_expansion_and_invertible_coordinate_map():
    quad=np.float32([[30,20],[170,25],[160,80],[35,75]])
    expanded=expand_quad(quad)
    assert area(intersection(expanded,quad))==pytest.approx(area(quad),abs=.02)
    image=np.full((100,200,3),200,np.uint8)
    raster,to_original=warp_document(image,expanded)
    corners=np.float32([[0,0],[raster.shape[1]-1,0],[raster.shape[1]-1,raster.shape[0]-1],[0,raster.shape[0]-1]])
    restored=cv2.perspectiveTransform(corners[None],to_original)[0]
    assert np.allclose(restored,expanded,atol=.01)
