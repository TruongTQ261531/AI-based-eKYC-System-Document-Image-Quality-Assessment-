from types import SimpleNamespace

import numpy as np
import pytest

from ekyc.module3_ocr import OCRExtraction, parse_regions, form_fields
from ekyc.scanocr import decode_regions, letterbox
from ekyc.io import StageError


def region(field, text, y=0, confidence=.99):
    return dict(field=field,text=text,confidence=confidence,box=[[0,y],[100,y],[100,y+10],[0,y+10]])


def test_vietnamese_field_labels_accents_leading_zeros_dates_and_multiline_address():
    rows = [region('address','Phường Bến Nghé, Thành phố Hồ Chí Minh',60),
            region('gender','Giới tính / Sex: Nữ'),region('full_name','Họ và tên / Full name: NGUYỄN THỊ ÁNH'),
            region('dob','Ngày sinh / Date of birth: 03/02/1999'),region('id_number','Số / No.: 001 234 567 890'),
            region('address','Địa chỉ: 12 Đường Thử Nghiệm',40),region('hometown','Không phải địa chỉ',20)]
    fields = form_fields(parse_regions(rows))
    assert fields == dict(full_name='NGUYỄN THỊ ÁNH',id_number='001234567890',dob='1999-02-03',
                          gender='Nữ',address='12 Đường Thử Nghiệm Phường Bến Nghé, Thành phố Hồ Chí Minh')


def test_invalid_or_conflicting_values_remain_blank_and_no_expiry_as_dob():
    rows = [region('id_number','00123456789O'),region('dob','31/02/1999'),
            region('expiry','12/12/2030'),region('gender','không đọc được')]
    assert all(v=='' for v in form_fields(parse_regions(rows)).values())
    assert parse_regions([region('id_number','001234567890'),region('id_number','991234567890')])['id_number'] is None


def test_ocr_confidence_gate_keeps_unknown_fields_blank():
    ocr = OCRExtraction.__new__(OCRExtraction)
    ocr.min_confidence = .65
    ocr.reader = SimpleNamespace(read=lambda card:[region('full_name','NGUYỄN THỊ ÁNH'),region('id_number','001234567890',confidence=.40)])
    faces = SimpleNamespace(extract_document=lambda card:(card,card,np.ones((1,2)),{}))
    result,_,_ = ocr.run(np.zeros((200,300,3),np.uint8),faces)
    assert result['fields']['full_name']=='NGUYỄN THỊ ÁNH'
    assert result['fields'].get('id_number') is None and result['requires_review']
    assert result['accepted_line_count']==1


def test_scanocr_letterbox_rgb_and_field_box_inverse_mapping_with_nms():
    image = np.full((400,800,3), [10,20,30], np.uint8)
    tensor,ratio,left,top = letterbox(image)
    assert tensor.shape==(1,3,640,640) and tensor.dtype==np.float32
    assert tensor[0,:,200,0]==pytest.approx(np.array([30,20,10])/255)
    assert (ratio,left,top)==(.8,0,160)
    output = np.zeros((1,15,4),np.float32)
    output[0,:4,:]=np.array([[320,320,320,100],[320,320,320,200],[160,160,640,80],[32,32,320,24]])
    output[0,5,0]=.99  # Full_Name
    output[0,5,1]=.9   # Duplicate must be suppressed.
    output[0,11,2]=.99 # CCCD_Chip whole-card box must not be OCRed.
    output[0,4,3]=.2   # Low-confidence ID_Number.
    rows=decode_regions(output,image.shape,ratio,left,top)
    assert len(rows)==1 and rows[0]['field']=='full_name'
    assert rows[0]['xyxy']==pytest.approx([300,180,500,220])


def test_unexpected_or_nonfinite_detector_output_fails_closed():
    with pytest.raises(StageError): decode_regions(np.zeros((1,84,100)),(400,800,3),1,0,0)
    with pytest.raises(StageError): decode_regions(np.full((1,15,4),np.nan),(400,800,3),1,0,0)
