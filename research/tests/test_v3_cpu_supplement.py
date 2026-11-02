"""Synthetic prefix/geometry contracts; not OCR accuracy evidence."""
import copy
import unittest
from research.v3_cpu_supplement import normalize,predict
from research.tests.test_v3_sources import specimen


def boxes(label,value):
    return [dict(text=label,box=[[10,10],[220,10],[220,30],[10,30]],confidence=.99),
            dict(text=value,box=[[10,40],[180,40],[180,60],[10,60]],confidence=.99)]


class PrefixSupplement(unittest.TestCase):
    def test_foreign_prefix_keeps_observed_value_and_does_not_mutate_input(self):
        items=boxes('Příjmení / Surname','UNIT SAMPLE');before=copy.deepcopy(items)
        self.assertEqual(predict(items,'search',False),{'last_name':'UNIT SAMPLE'})
        self.assertEqual(items,before)

    def test_bilingual_continuation_is_not_an_inline_name_value(self):
        items=boxes('Surname / Nom','UNIT SAMPLE')
        self.assertEqual(predict(items,'bilingual',False),{'last_name':'UNIT SAMPLE'})

    def test_numeric_prefix_and_inline_number_are_preserved(self):
        items=boxes('7. Document Number: TEST12345','OTHER')
        self.assertEqual(predict(items,'bilingual',False)['id_number'],'TEST12345')

    def test_mrz_text_is_never_rewritten_by_label_search(self):
        a,b=specimen();items=boxes(a,b)
        self.assertEqual(normalize(items,'bilingual'),items)


if __name__=='__main__':unittest.main()
