from research.recovery_semantic_eval import canonical,score_semantics


def test_schema_equivalence_does_not_penalize_date_or_gender_format():
    assert canonical('dob','31/10/2026')==canonical('dob','2026-10-31')
    assert canonical('gender','Female')==canonical('gender','Nữ')
    assert canonical('id_number','001O')!=canonical('id_number','0010')


def test_missing_invalid_value_never_becomes_correct_empty_reference():
    sample=dict(width=100,height=100,fields=[dict(key='dob',text='12/11/2000',quad=[[10,10],[90,10],[90,30],[10,30]])])
    assert score_semantics(sample,{})['canonical_exact']==0
    assert score_semantics(sample,{'dob':'2000-11-12'})['canonical_exact']==1
    assert score_semantics(sample,{'dob':'2000-11-12'})['literal_exact']==0
