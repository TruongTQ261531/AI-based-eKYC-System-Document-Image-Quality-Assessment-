from research.layout_kie import extract
import numpy as np


def box(text,x,y,w=120,h=20):
    return dict(text=text,box=[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],confidence=.95)


def test_two_columns_bind_values_below_each_printed_label():
    predictions=[box('Full name:',20,20),box('Student ID:',400,20),
        box('MOCK PERSON',20,55,200),box('SV78923',400,55),
        box('Date of birth:',20,110),box('31/12/2000',20,145)]
    fields,_,_=extract(predictions)
    assert fields['full_name']=='MOCK PERSON'
    assert fields['student_id']=='SV78923' and fields['dob']=='2000-12-31'
    shifted=[dict(p,box=[[x*2+10,y*2+15] for x,y in p['box']]) for p in reversed(predictions)]
    assert extract(shifted)[0]==fields


def test_unknown_explicit_label_keeps_observed_value_and_missing_stays_absent():
    fields,labels,_=extract([box('Department:',20,20),box('SCIENCE',20,55),box('Date of birth:',20,110)])
    key=next(k for k,v in labels.items() if v=='Department')
    assert fields[key]=='SCIENCE'
    assert 'dob' not in fields and 'id_number' not in fields


def test_vietnamese_bare_school_label_and_inline_date_are_observed():
    fields,_,_=extract([box('Trường:',20,20),box('MOCK UNIVERSITY',20,55,220),box('Ngày sinh: 12/02/2001',20,110,260)])
    assert fields['school']=='MOCK UNIVERSITY' and fields['dob']=='2001-02-12'


def test_multiple_labels_in_one_box_and_multiline_address_do_not_steal_columns():
    fields,_,_=extract([box('Full name: MOCK PERSON Student ID: SV78923',20,20,650),
        box('Address:',20,80),box('17 MOCK ROAD',20,115),box('SPECIMEN CITY',20,145),
        box('Gender:',400,80),box('Male',400,115)])
    assert fields['full_name']=='MOCK PERSON' and fields['student_id']=='SV78923'
    assert fields['address']=='17 MOCK ROAD SPECIMEN CITY' and fields['gender']=='Nam'


def test_online_alternative_uses_existing_predictions_without_more_ocr(monkeypatch):
    import research.layout_kie as module
    engine=object.__new__(module.LayoutKIEEngine)
    predictions=[box('Trường:',120,120),box('MOCK UNIVERSITY',120,155,220)]
    def original(self,image,locked,reader):
        self._request_locations['fastvit']={'points':[]}
        return dict(fields={},predictions=predictions,selected_policy='completion',actual_wall_seconds=.1,
            actual_cpu_seconds=.1,ocr_executions=1,identity_approved=False,liveness_evaluated=False)
    monkeypatch.setattr(module.RecoveryEngine,'online',original)
    monkeypatch.setattr(module,'make_view',lambda *a,**k:(None,np.array([[1.,0.,100.],[0.,1.,100.],[0.,0.,1.]]),'test',True))
    engine.ocr=lambda *a:(_ for _ in ()).throw(AssertionError('No additional OCR permitted'))
    result=engine.online(np.zeros((300,600,3),np.uint8),{})
    assert result['fields']['school']=='MOCK UNIVERSITY'
    assert result['ocr_executions']==1 and not result['identity_approved']
    assert result['predictions'] is predictions
    assert result['actual_wall_seconds']>=.1 and result['kie_additional_wall_seconds']>0


def test_bilingual_labels_are_not_filled_as_values():
    fields,_,_=extract([box('Họ và tên / Full name:',20,20,250),box('MOCK PERSON',20,55,220),
        box('Ngày sinh (Date of birth):',20,110,280),box('12/02/2001',20,145)])
    assert fields['full_name']=='MOCK PERSON' and fields['dob']=='2001-02-12'
