import unittest
from research.vlm_control import load,signature
from research.vlm_runtime import signature as primary_signature


class ControlIsolationTests(unittest.TestCase):
    def test_control_has_same_ids_and_excludes_missing_content(self):
        rows=load('train')
        self.assertEqual(len(rows),288)
        self.assertEqual(len({r['physical_id'] for r in rows}),96)
        self.assertEqual({r['capture'] for r in rows},{'full','corner_clip','blur_glare'})
        self.assertTrue(all(len(r['target'])==5 for r in rows))

    def test_development_still_contains_missing_content(self):
        rows=load('development')
        self.assertEqual(len(rows),80)
        self.assertIn('field_clip',{r['capture'] for r in rows})
        self.assertIn('value_mask',{r['capture'] for r in rows})

    def test_control_provenance_separate_from_main(self):
        self.assertNotEqual(signature(),primary_signature())


if __name__=='__main__':unittest.main()
