import numpy as np

from ekyc.document_fields import observed_information
from ekyc.module3_ocr import OCRExtraction


def lines(*texts):
    return [dict(text=text,confidence=.99,box=[[0,i*25],[600,i*25],[600,i*25+18],[0,i*25+18]],source='generic_text') for i,text in enumerate(texts)]


def test_student_card_does_not_require_cccd_gender_dob_or_address():
    fields,items,kind=observed_information(lines('THẺ HỌC SINH','Họ và tên: NGUYỄN VĂN AN',
        'Mã học sinh: HS20260042','Lớp: 12A3','Niên khóa: 2024 - 2027'),{})
    assert kind['key']=='student_card'
    assert fields==dict(full_name='NGUYỄN VĂN AN',student_id='HS20260042',class_name='12A3',course='2024 - 2027')
    assert {item['key'] for item in items}==set(fields)


def test_driver_license_keeps_category_dates_and_alphanumeric_document_number():
    fields,items,kind=observed_information(lines('GIẤY PHÉP LÁI XE','Họ tên / Full name: TRẦN THỊ LAN',
        'License number: A1234567','Hạng: B2','Ngày cấp: 02/03/2024','Có giá trị đến: 02/03/2034'),{})
    assert kind['key']=='driver_license'
    assert fields['id_number']=='A1234567' and fields['license_class']=='B2'
    assert fields['issue_date']=='2024-03-02' and fields['expiry_date']=='2034-03-02'
    assert 'dob' not in fields and 'gender' not in fields and 'address' not in fields


def test_split_label_value_boxes_and_bilingual_gender_nationality_are_not_mixed():
    data=lines('Họ và tên:','LÊ THỊ HOA','Giới tính / Sex: Nữ   Quốc tịch / Nationality: Việt Nam',
               'Quê quán / Place of origin: Hải Châu, Đà Nẵng','Nơi thường trú: 12 Đường Thử', 'Phường A, Thành phố B')
    fields,_,_=observed_information(data,{})
    assert fields['full_name']=='LÊ THỊ HOA'
    assert fields['gender']=='Nữ' and fields['nationality']=='Việt Nam'
    assert fields['hometown']=='Hải Châu, Đà Nẵng'
    assert fields['address']=='12 Đường Thử Phường A, Thành phố B'


def test_unknown_label_is_preserved_without_mandatory_template():
    fields,items,kind=observed_information(lines('THẺ THƯ VIỆN','Đơn vị: Khoa Công nghệ thông tin'),{})
    assert kind['key']=='unknown' and len(items)==1
    assert items[0]['label']=='Đơn vị' and items[0]['value']=='Khoa Công nghệ thông tin'
    assert not any(key in fields for key in ('id_number','full_name','dob','gender','address'))


def test_generic_ocr_keeps_unclassified_text_and_missing_portrait_without_inventing_fields():
    from types import SimpleNamespace
    ocr=OCRExtraction.__new__(OCRExtraction);ocr.min_confidence=.65
    ocr.reader=SimpleNamespace(read=lambda image:lines('THẺ THƯ VIỆN','Thông tin chưa có nhãn'))
    result,_,feature=ocr.run_unlocalized(np.zeros((400,600,3),np.uint8))
    assert result['accepted_line_count']==2 and result['raw_lines']
    assert not result['document_fields'] and not result['fields'] and feature is None


def test_conflicting_label_values_are_not_overwritten_by_specialized_guess():
    fields,_,_=observed_information(lines('Ngày sinh: 01/01/2000','Ngày sinh: 02/02/2000'),{'dob':'01/01/2000'})
    assert 'dob' not in fields


def test_student_number_is_not_duplicated_as_an_identity_card_number():
    fields,_,_=observed_information(lines('THẺ HỌC SINH','Mã học sinh: HS20260042'),{'id_number':'HS20260042'})
    assert fields['student_id']=='HS20260042' and 'id_number' not in fields
