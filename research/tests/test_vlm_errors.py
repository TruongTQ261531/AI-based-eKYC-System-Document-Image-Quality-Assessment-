import unittest
from research.vlm_errors import classify


class ErrorTaxonomyTests(unittest.TestCase):
    def test_masked_clipped_and_unprinted_are_separate(self):
        sample=dict(target={'id_number':'123'},fields=[dict(key='id_number'),dict(key='full_name',occluded=True),dict(key='dob')])
        result=classify(sample,{'id_number':'124','full_name':'MOCK','dob':'2000','address':'MOCK'},True)
        self.assertEqual(result['wrong_visible_value'],1);self.assertEqual(result['output_opaque_masked_field'],1)
        self.assertEqual(result['output_clipped_label_or_value'],1);self.assertEqual(result['output_unprinted_field'],1)
        self.assertEqual(result['opaque_mask_opportunities'],1)

    def test_format_failure_is_not_silently_reading_error(self):
        result=classify(dict(target={'dob':'01/02/2000'},fields=[dict(key='dob')]),{},False)
        self.assertEqual(result['format_failure'],1);self.assertEqual(result['omitted_visible'],1)

    def test_same_date_formatting_not_reading_error(self):
        result=classify(dict(target={'dob':'01/02/2000'},fields=[dict(key='dob')]),{'dob':'2000-02-01'},True)
        self.assertEqual(result['correct_visible_value'],1);self.assertNotIn('wrong_visible_value',result)


if __name__=='__main__':unittest.main()
