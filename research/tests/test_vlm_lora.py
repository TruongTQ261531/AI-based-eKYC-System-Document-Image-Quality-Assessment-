import json
import unittest

from research.vlm_data import field_target,card,capture,COUNTS,load
from research.vlm_runtime import parsed,score,aggregate,normalized,pixels
from PIL import Image


class VLMContracts(unittest.TestCase):
    def test_label_cut_excludes_otherwise_visible_value(self):
        f=dict(key='full_name',value='MOCK',label_box=[-1,2,10,10],value_box=[2,12,15,20])
        self.assertEqual(field_target([f],100,100),{})

    def test_value_cut_excluded(self):
        f=dict(key='id_number',value='012345',label_box=[2,2,10,10],value_box=[2,12,101,20])
        self.assertEqual(field_target([f],100,100),{})

    def test_visible_field_kept(self):
        f=dict(key='dob',value='01/01/2000',label_box=[2,2,10,10],value_box=[2,12,100,20])
        self.assertEqual(field_target([f],100,100),{'dob':'01/01/2000'})

    def test_occluded_value_excluded(self):
        f=dict(key='id_number',value='0123',label_box=[2,2,10,10],value_box=[2,12,15,20],occluded=True)
        self.assertEqual(field_target([f],100,100),{})

    def test_masked_capture_has_fewer_targets(self):
        image,fields=card('test_only_mock',0,'citizen',True)
        result,ff=capture(image,fields,'test_only_mock','value_mask')
        target=field_target(ff,result.shape[1],result.shape[0])
        self.assertLess(len(target),len(fields))
        self.assertEqual(len(target),len(fields)-sum(f['occluded'] for f in ff))

    def test_leading_zero_remains_string(self):
        value,valid=parsed('{"id_number":"000123"}')
        self.assertTrue(valid);self.assertEqual(value['id_number'],'000123')

    def test_explanation_is_invalid_json(self):
        self.assertEqual(parsed('Thông tin: {"id_number":"123"}'),({},False))

    def test_json_list_rejected(self):
        self.assertEqual(parsed('[{"id_number":"123"}]'),({},False))

    def test_boolean_value_rejected(self):
        self.assertEqual(parsed('{"id_number":true}'),({},False))

    def test_duplicate_key_rejected(self):
        self.assertEqual(parsed('{"id_number":"1","id_number":"2"}'),({},False))

    def test_date_format_canonicalized_but_literal_retained(self):
        row=score({'dob':'01/02/2000'},{'dob':'2000-02-01'},True)
        self.assertEqual(row['correct'],1);self.assertEqual(row['literal_correct'],0)

    def test_invalid_date_never_correct(self):
        self.assertEqual(score({'dob':'01/02/2000'},{'dob':'32/14/2000'},True)['correct'],0)

    def test_hallucinated_field_penalizes_precision(self):
        row=score({'full_name':'MOCK'},{'full_name':'MOCK','id_number':'000'},True)
        self.assertEqual(row['extra_keys'],1)
        self.assertFalse(row['exact_document'])
        self.assertAlmostEqual(aggregate([row])['precision'],.5)

    def test_empty_output_not_perfect_for_nonempty_target(self):
        self.assertEqual(aggregate([score({'dob':'1'}, {},True)])['f1'],0)

    def test_true_empty_document_exact(self):
        self.assertTrue(score({}, {},True)['exact_document'])
        self.assertFalse(score({}, {},False)['exact_document'])

    def test_unicode_normalization(self):
        self.assertEqual(normalized(' LÊ  AN '),normalized('LE\u0302 AN'))

    def test_pixel_contract(self):
        result=pixels(Image.new('RGB',(1000,680),'white'))
        self.assertEqual(tuple(result.shape),(2,3,448,448))

    def test_identity_and_hash_isolation(self):
        rows=load();self.assertEqual(len(rows),sum(COUNTS.values())*5)
        sets={role:{r['physical_id'] for r in rows if r['role']==role} for role in COUNTS}
        for a in sets:
            for b in sets:
                if a!=b:self.assertFalse(sets[a]&sets[b])
        self.assertEqual(len({r['input_sha256'] for r in rows}),len(rows))


if __name__=='__main__':unittest.main()
