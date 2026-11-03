import unittest
from research.fc_statistics import holm, analyze
from research.fc_common import KEYS


def records(improved=False):
    result={}
    for key in KEYS:
        better=improved and key.startswith('hard_');rows=[]
        for i,source in enumerate(('authored','authored','midv2020','midv2020')):
            rows.append(dict(uid=str(i),physical_id=str(i),input_sha256=str(i),pixel_sha256='shared' if i<2 else str(i),
                source=source,correct=2 if better else 1,reference=2,predicted=2,neighbor_correct=2 if better else 1,
                neighbor_reference_keys=2,declared_hidden_outputs=0 if better else 1))
        result[key]=dict(rows=rows,summary=dict(f1=1. if better else .5,neighbor_recall=1. if better else .5,
                                               declared_hidden_outputs=0 if better else 4))
    return result


class PairedInference(unittest.TestCase):
    def test_holm_step_down_is_monotone_in_rank_and_mapped_back(self):
        for actual,expected in zip(holm([.01,.04,.03,.002]),[.03,.06,.06,.008]):
            self.assertAlmostEqual(actual,expected)

    def test_identical_models_have_zero_intervals_and_p_one(self):
        result=analyze(records())
        self.assertEqual(len([r for r in result['comparisons'] if r['primary']]),4)
        for value in result['comparisons']:
            self.assertEqual(value['f1']['delta'],0.)
            self.assertEqual(value['f1']['ci95_low'],0.)
            self.assertEqual(value['f1']['ci95_high'],0.)
            if value['primary']:
                self.assertEqual(value['p_permutation'],1.)
                self.assertEqual(value['p_holm'],1.)

    def test_constant_document_effect_is_preserved_in_both_interval_levels(self):
        result=analyze(records(True),permutations=False)
        for value in result['comparisons']:
            self.assertEqual(value['f1']['ci95_low'],.5)
            self.assertEqual(value['f1']['ci95_high'],.5)
            if value['primary']:self.assertEqual(value['f1']['ci9875_low'],.5)

    def test_duplicate_pixel_components_join_ids_without_field_pseudoreplication(self):
        result=analyze(records(True),joined=True,permutations=False)
        self.assertEqual(result['document_instances'],4)
        self.assertEqual(result['resampling_clusters'],3)

    def test_unpaired_inputs_are_rejected(self):
        values=records();values['random_42']['rows'][0]['input_sha256']='different'
        with self.assertRaises(ValueError):analyze(values)


if __name__=='__main__':unittest.main()
