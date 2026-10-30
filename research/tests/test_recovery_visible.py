from research.recovery_visible_eval import score_visible


def test_partial_field_scores_only_predefined_fully_visible_characters():
    sample=dict(width=100,height=70,fields=[dict(key='name',text='ABCDEF',visible_reference='DEF',geometric_visibility=.5,
        quad=[[-40,10],[80,10],[80,30],[-40,30]])])
    pred=[dict(text='DEF',confidence=.8,box=[[2,12],[78,12],[78,28],[2,28]])]
    result=score_visible(sample,pred)
    assert result['fields'][0]['exact'] and result['fields'][0]['partial']
    pred[0]['text']='ABCDEF'
    assert not score_visible(sample,pred)['fields'][0]['exact']
