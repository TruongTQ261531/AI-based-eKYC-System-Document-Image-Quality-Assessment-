"""Dataset algebra and fallback behavior; not independent accuracy evidence."""
import collections
import json
import unittest
from research.v3_common import DATA,R2DATA,OUT,read
from research.v3_metrics import scoring
from research.v3_cpu import fallback
from research.tests.test_v3_sources import specimen

class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=read(DATA/'samples.json');cls.body=read(R2DATA/'samples.json')
    def test_every_row_keeps_original_pixel_hash_path_uid_order(self):
        self.assertEqual(len(self.rows),1496)
        self.assertEqual([(r['uid'],r['path'],r['input_sha256']) for r in self.rows],[(r['uid'],r['path'],r['input_sha256']) for r in self.body])
    def test_targets_have_explicit_reference_and_score_themselves(self):
        for row in self.rows:
            with self.subTest(uid=row['uid']):
                self.assertEqual(set(row['target']),set(row['source_refs']))
                m,_=scoring(row,json.dumps(row['target'],ensure_ascii=False))
                self.assertEqual(m['correct'],len(row['target']));self.assertEqual(m['max_precision_correct'],len(row['target']))
    def test_no_identity_crosses_train_development_test(self):
        ids={role:{r['physical_id'] for r in self.rows if r['role']==role} for role in ('train','development','test')}
        for a,b in [('train','development'),('train','test'),('development','test')]:self.assertFalse(ids[a]&ids[b])
        self.assertEqual({k:len(v) for k,v in ids.items()},{'train':128,'development':24,'test':48})
    def test_public_manifest_has_no_private_labels_or_paths(self):
        for row in read(OUT/'dataset_manifest.json'):
            self.assertFalse(set(row)&{'target','body_target','fields','path','source_refs','source_evidence','accepted_values','masked_keys'})
    def test_changes_are_reported_not_silently_erased(self):
        counts=collections.Counter()
        for row,old in zip(self.rows,self.body):
            counts[row['role']+'/changed_targets']+=row['target']!=old['target']
            counts[row['role']+'/new_supported_keys']+=len(set(row['target'])-set(old['target']))
            counts[row['role']+'/lost_body_keys']+=len(set(old['target'])-set(row['target']))
        self.assertEqual(dict(counts),read(OUT/'dataset_card.json')['target_changes'])

class ConventionalFallback(unittest.TestCase):
    def predictions(self,corrupt=False):
        a,b=specimen()
        if corrupt:b=b[:19]+str((int(b[19])+1)%10)+b[20:]
        return [dict(text=s,box=[[0,y],[440,y],[440,y+20],[0,y+20]],confidence=.99) for s,y in [(a,0),(b,30)]]
    def test_body_values_are_not_overwritten_and_no_century_is_added(self):
        fields,info=fallback({'first_name':'BODY VALUE'},self.predictions(),True)
        self.assertEqual(fields['first_name'],'BODY VALUE');self.assertEqual(fields['dob'],'990101')
        self.assertNotIn('personal_number',fields);self.assertFalse(info['authenticity_verified'])
    def test_format_and_checksum_baselines_have_distinct_failure_policy(self):
        loose,_=fallback({},self.predictions(True),False);strict,_=fallback({},self.predictions(True),True)
        self.assertIn('dob',loose);self.assertNotIn('dob',strict)
        self.assertNotIn('first_name',strict)
    def test_missing_mrz_does_not_invent_fields(self):
        fields,info=fallback({'id_number':'DEMO'},[],True)
        self.assertEqual(fields,{'id_number':'DEMO'});self.assertFalse(info['mrz_pair_found'])

if __name__=='__main__':unittest.main()
