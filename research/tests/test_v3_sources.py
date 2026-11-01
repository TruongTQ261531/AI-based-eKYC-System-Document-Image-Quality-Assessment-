import unittest
import numpy as np
from research.v3_sources import check_digit,parse_td3,span_quad,visible_realizations
from research.v3_metrics import scoring,date_value

def specimen():
    first=('P<UTO'+'DEMO<<UNIT<SAMPLE').ljust(44,'<')
    doc='DEMO12345';dob='990101';expiry='350101';optional='LOCAL01'.ljust(14,'<')
    second=doc+check_digit(doc)+'UTO'+dob+check_digit(dob)+'F'+expiry+check_digit(expiry)+optional+check_digit(optional)
    second+=check_digit(second[:10]+second[13:20]+second[21:43])
    return first,second

class TD3(unittest.TestCase):
    def test_fields_and_all_numeric_checks_on_generated_specimen(self):
        a,b=specimen();self.assertEqual(len(a),44);self.assertEqual(len(b),44)
        result=parse_td3(a,b);self.assertTrue(all(result['checks'].values()))
        fields={r['key']:r['value'] for r in result['spans']}
        self.assertEqual(fields['last_name'],'DEMO');self.assertEqual(fields['first_name'],'UNIT SAMPLE')
        self.assertEqual(fields['dob'],'990101');self.assertEqual(fields['id_number'],'DEMO12345')
    def test_checksum_corruption_is_recorded_without_character_repair(self):
        a,b=specimen();wrong=b[:9]+str((int(b[9])+1)%10)+b[10:]
        result=parse_td3(a,wrong);self.assertFalse(result['checks']['id_number'])
        self.assertEqual(next(s['value'] for s in result['spans'] if s['key']=='id_number'),'DEMO12345')
    def test_malformed_or_digit_corrupted_names_are_not_guessed(self):
        a,b=specimen();self.assertIsNone(parse_td3(a[:-1],b));self.assertIsNone(parse_td3(a.replace('UNIT','UN1T'),b))
    def test_truncated_name_block_does_not_invent_complete_names(self):
        a,b=specimen();a='P<UTO'+('LONGNAME<<'+'A'*39)[:39]
        self.assertFalse(any(s['key'] in ('first_name','last_name') for s in parse_td3(a,b)['spans']))
    def test_character_span_projection_uses_correct_strip_positions(self):
        q=span_quad([[0,0],[440,0],[440,20],[0,20]],13,19)
        np.testing.assert_allclose(q,[[130,0],[190,0],[190,20],[130,20]],atol=1e-4)

class Visibility(unittest.TestCase):
    def test_one_hidden_body_box_does_not_erase_visible_backup(self):
        nodes=[dict(key='id_number',value='DEMO12345',components=[[[0,0],[20,0],[20,10],[0,10]]],kind='body',priority=0,author_source='number'),
               dict(key='id_number',value='DEMO12345',components=[[[40,0],[60,0],[60,10],[40,10]]],kind='text',priority=10,author_source='mrz')]
        refs,_,_=visible_realizations(nodes,np.eye(3),[np.float32([[0,0],[20,0],[20,10],[0,10]])],100,50)
        self.assertIn('id_number',refs);self.assertEqual(refs['id_number'][0]['source'],'mrz')
    def test_multiline_requires_every_component_but_ignores_empty_gap(self):
        node=dict(key='address',value='CITY COUNTRY',components=[[[0,0],[30,0],[30,10],[0,10]],[[0,30],[30,30],[30,40],[0,40]]],kind='body',priority=0,author_source='lines')
        gap=np.float32([[0,15],[30,15],[30,20],[0,20]])
        refs,_,_=visible_realizations([node],np.eye(3),[gap],100,50);self.assertIn('address',refs)
        refs,_,_=visible_realizations([node],np.eye(3),[],100,35);self.assertNotIn('address',refs)

class Precision(unittest.TestCase):
    def sample(self,extra=False):
        refs=[dict(value='990101',kind='date_yymmdd',priority=10,source='mrz')]
        if extra:refs.insert(0,dict(value='01/01/1999',kind='body',priority=0,source='body'))
        return dict(target={'dob':refs[0]['value']},source_refs={'dob':refs},masked_keys=[])
    def test_no_century_can_be_invented_from_only_YYMMDD(self):
        metrics,_=scoring(self.sample(),'{"dob":"01/01/1999"}')
        self.assertEqual(metrics['correct'],0);self.assertEqual(metrics['date_century_overreach'],1)
        metrics,_=scoring(self.sample(),'{"dob":"01/01/99"}');self.assertEqual(metrics['correct'],1)
    def test_maximum_precision_is_separate_from_any_visible_realization(self):
        metrics,_=scoring(self.sample(True),'{"dob":"990101"}')
        self.assertEqual(metrics['correct'],1);self.assertEqual(metrics['max_precision_correct'],0)
        metrics,_=scoring(self.sample(True),'{"dob":"01/01/1999"}');self.assertEqual(metrics['max_precision_correct'],1)

if __name__=='__main__':unittest.main()
