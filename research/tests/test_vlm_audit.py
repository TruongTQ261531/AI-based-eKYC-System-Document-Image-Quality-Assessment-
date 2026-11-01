import unittest
from research.vlm_final_report import require_cases,paired_interval,panel


class AuditTests(unittest.TestCase):
    def test_duplicate_does_not_hide_missing_case(self):
        with self.assertRaises(ValueError):require_cases([{'uid':'a'},{'uid':'a'}],{'a','b'})

    def test_wrong_case_same_count_rejected(self):
        with self.assertRaises(ValueError):require_cases([{'uid':'a'},{'uid':'x'}],{'a','b'})

    def test_interval_groups_views_by_physical_id(self):
        good=[dict(physical_id=uid,correct=1,reference=1,predicted=1) for uid in ('a','b') for _ in range(5)]
        bad=[dict(r,correct=0) for r in good]
        result=paired_interval(good,bad)
        self.assertEqual(result['physical_ids'],2);self.assertEqual(result['f1_difference'],1)
        self.assertEqual(result['ci95'],[1,1]);self.assertEqual(result['resampling_unit'],'physical_id')

    def test_unpaired_ids_rejected(self):
        with self.assertRaises(ValueError):paired_interval([dict(physical_id='a')],[dict(physical_id='b')])

    def test_repeat_panel_not_random_on_each_invocation(self):
        samples=[dict(uid=f'{i}/{c}',physical_id=str(i),capture=c) for i in range(24) for c in ('full','corner_clip','field_clip','blur_glare','value_mask')]
        self.assertEqual(len(panel(samples)),12);self.assertEqual(panel(samples),panel(list(reversed(samples))))


if __name__=='__main__':unittest.main()
