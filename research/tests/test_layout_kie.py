from research.layout_kie import extract


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
