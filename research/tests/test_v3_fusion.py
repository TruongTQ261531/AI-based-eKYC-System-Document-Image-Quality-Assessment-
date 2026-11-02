"""Synthetic merge-contract checks; these are not OCR accuracy measurements."""
import unittest
from research.tests.test_v3_sources import specimen
from research.v3_fusion import compose


def predictions(a,b):
    return [dict(text=s,score=.99,box=[[0,y],[440,y],[440,y+10],[0,y+10]])
            for y,s in ((0,a),(20,b))]


class MergeContract(unittest.TestCase):
    def test_missing_fields_are_filled_without_overwriting_model_or_guessing_century(self):
        a,b=specimen();original={'id_number':'MODEL_VALUE','school':'DEMO SCHOOL'}
        merged,origins,info=compose(original,predictions(a,b))
        self.assertEqual(merged['id_number'],'MODEL_VALUE')
        self.assertEqual(merged['dob'],'990101')
        self.assertEqual(origins['dob'],'mrz');self.assertEqual(origins['school'],'model')
        self.assertEqual(original,{'id_number':'MODEL_VALUE','school':'DEMO SCHOOL'})
        self.assertGreater(info['added'],0);self.assertFalse(info['authenticity_verified'])

    def test_bad_number_check_does_not_fill_number_or_unprotected_names(self):
        a,b=specimen();bad=b[:9]+str((int(b[9])+1)%10)+b[10:]
        fields,_,_=compose({},predictions(a,bad))
        self.assertNotIn('id_number',fields);self.assertNotIn('last_name',fields)

    def test_no_mrz_preserves_exact_model_fields_and_provenance(self):
        fields={'student_id':'SYNTHETIC-1'}
        merged,origins,info=compose(fields,[])
        self.assertEqual(merged,fields);self.assertEqual(origins,{'student_id':'model'})
        self.assertEqual(info['added'],0);self.assertFalse(info['mrz_pair_found'])


if __name__=='__main__':unittest.main()
