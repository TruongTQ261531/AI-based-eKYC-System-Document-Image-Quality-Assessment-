import unittest
from research.vlm_analysis import tolerant


class SecondaryFormatTests(unittest.TestCase):
    def test_null_abstention_does_not_discard_visible_value(self):
        fields,meta=tolerant('{"id_number":"000123","dob":null}')
        self.assertEqual(fields,{'id_number':'000123'});self.assertEqual(meta['null_or_empty'],1)

    def test_whole_fence_unwrapped(self):
        fields,meta=tolerant('```json\n{"id_number":"000123"}\n```')
        self.assertEqual(fields,{'id_number':'000123'});self.assertTrue(meta['fenced'])

    def test_prose_not_guessed(self):
        fields,meta=tolerant('I think: {"id_number":"123"}')
        self.assertFalse(meta['syntax_object_success']);self.assertEqual(fields,{})

    def test_duplicate_rejected(self):
        self.assertFalse(tolerant('{"id_number":"1","id_number":"2"}')[1]['syntax_object_success'])

    def test_empty_and_bad_values_disclosed(self):
        fields,meta=tolerant('{"id_number":"", "dob":[], "gender":true, "full_name":"MOCK"}')
        self.assertEqual(fields,{'full_name':'MOCK'});self.assertEqual(meta['null_or_empty'],1);self.assertEqual(meta['bad_type'],2)


if __name__=='__main__':unittest.main()
