import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research.hp_audit import intervals
from research import hp_study
from research.hp_common import ROOT,KEYS,read


def records():
    result={}
    for key in KEYS:
        hard=key.startswith('hard_');rows=[]
        for pid,source,digest in [('a','authored','same'),('b','authored','same'),('c','midv2020','c'),('d','midv2020','d')]:
            rows.append(dict(physical_id=pid,source=source,input_sha256=digest,correct=2 if hard else 1,
                reference=2,predicted=2,neighbor_correct=2 if hard else 1,neighbor_reference_keys=2,
                declared_hidden_outputs=0 if hard else 1))
        result[key]=dict(rows=rows,summary=dict(f1=1. if hard else .5,neighbor_recall=1. if hard else .5,
                                               declared_hidden_outputs=0 if hard else 4))
    return result


class ClusterIntervals(unittest.TestCase):
    def test_identical_per_id_effect_is_recovered_without_field_pseudoreplication(self):
        result=intervals(records())
        self.assertEqual(result['resampling_clusters'],4)
        for comparison in result['comparisons']:
            self.assertEqual(comparison['f1']['delta'],.5)
            self.assertEqual(comparison['f1']['ci95_low'],.5)
            self.assertEqual(comparison['f1']['ci95_high'],.5)

    def test_duplicate_raster_sensitivity_joins_ids(self):
        result=intervals(records(),True)
        self.assertEqual(result['document_instances'],4)
        self.assertEqual(result['resampling_clusters'],3)
        self.assertEqual(result['comparisons'][0]['f1']['delta'],.5)


class DevelopmentPromotion(unittest.TestCase):
    def invoke(self,unsupported):
        summaries={k:dict(f1=.36,unsupported_nonempty=20,neighbor_omissions=10) for k in KEYS}
        summaries['hard_42']=dict(f1=.42,unsupported_nonempty=unsupported,neighbor_omissions=9)
        summaries['hard_31415']=dict(f1=.4,unsupported_nonempty=19,neighbor_omissions=9)
        def fake_read(path):
            name=Path(path).stem
            if not name.startswith('development_'):raise AssertionError('Selection read a non-development result')
            return {'summary':summaries[name[len('development_'):]]}
        cache=ROOT/'research/cache/hard_pairs_v1/test_tmp';cache.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache) as folder,patch.object(hp_study,'OUT',Path(folder)), \
             patch.object(hp_study,'read',side_effect=fake_read),patch.object(hp_study,'preserve'), \
             patch.object(hp_study,'signature',return_value='sig'), \
             patch.object(hp_study,'sha',return_value='hash'), \
             patch.object(hp_study,'adapter_for',side_effect=lambda k:(ROOT/'example'/k,'digest')):
            hp_study.seal()
            return read(Path(folder)/'test_lock.json')

    def test_more_unsupported_outputs_block_promotion_despite_higher_f1(self):
        lock=self.invoke(21)
        self.assertEqual(lock['selected_hard_candidate'],'hard_42')
        self.assertFalse(lock['promotion_approved'])
        self.assertFalse(lock['test_scoring_started'])

    def test_both_error_constraints_and_f1_must_pass_on_development(self):
        self.assertTrue(self.invoke(19)['promotion_approved'])


if __name__=='__main__':unittest.main()
