import json
import unittest
from unittest.mock import patch
from research.hp_metrics import scoring,summary
from research.hp_study import verify_test


def sample():
    return dict(role='test',width=100,height=100,target={'full_name':'VISIBLE'},
        fields=[dict(key='id_number',quad=[[10,10],[40,10],[40,20],[10,20]],occluded=True),
                dict(key='full_name',quad=[[10,24],[40,24],[40,34],[10,34]])],
        source_refs={'full_name':[dict(value='VISIBLE',kind='body',source='body',priority=0)]},
        pair_hidden_key='id_number',pair_kept_key='full_name')


class OpposingErrorMetrics(unittest.TestCase):
    def test_empty_json_cannot_pass_pair_by_abstaining_on_everything(self):
        metrics,_=scoring(sample(),'{}')
        self.assertEqual(metrics['pair_hidden_leaked'],0)
        self.assertEqual(metrics['pair_success'],0)
        self.assertEqual(metrics['neighbor_omissions'],1)

    def test_visible_correct_and_hidden_absent_pass_both_directions(self):
        metrics,_=scoring(sample(),'{"full_name":"VISIBLE"}')
        self.assertEqual(metrics['pair_success'],1)
        self.assertEqual(metrics['neighbor_correct'],1)

    def test_hidden_output_and_wrong_neighbor_are_counted_separately(self):
        metrics,_=scoring(sample(),'{"id_number":"GUESS","full_name":"WRONG"}')
        self.assertEqual(metrics['pair_hidden_leaked'],1)
        self.assertEqual(metrics['neighbor_wrong'],1)
        self.assertEqual(metrics['pair_success'],0)

    def test_invalid_publication_blocks_test_before_any_inference(self):
        with patch('research.hp_study.read',side_effect=[{'signature':'x'},{'signature':'x','lock_sha256':'bad'}]), \
             patch('research.hp_study.signature',return_value='x'),patch('research.hp_study.sha',return_value='good'):
            with self.assertRaisesRegex(ValueError,'Test seal'):verify_test()


if __name__=='__main__':unittest.main()
