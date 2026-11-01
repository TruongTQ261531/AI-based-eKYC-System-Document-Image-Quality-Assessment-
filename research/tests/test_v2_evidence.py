"""Checks target semantics, identity isolation and matched exposure, not model accuracy."""
import collections
import unittest
import numpy as np
from research.v2_common import DATA,read,load,FIELD_MAP
from research.v2_data import augment,target,mapped_fields,mock
from research.v2_metrics import score,canonical

class PrintedDates(unittest.TestCase):
    def test_verbatim_dates_remain_correct_across_author_formats(self):
        for s in ('14 02 1985','14. 02. 1985','14.02.1985.','14 FEB 85','29-02-1985'):
            self.assertEqual(score({'dob':s},{'dob':s},True)['correct'],1)
    def test_short_year_never_invents_a_century(self):
        self.assertNotEqual(canonical('dob','14 FEB 85'),canonical('dob','14/02/1985'))
        self.assertNotEqual(canonical('dob','14 FEB 85'),canonical('dob','14/02/2085'))
    def test_unambiguous_numeric_formats_compare_equally(self):
        self.assertEqual(canonical('dob','14. 02. 1985.'),canonical('dob','1985-02-14'))

class Targets(unittest.TestCase):
    def setUp(self):
        self.image=np.full((100,200,3),255,np.uint8)
        self.fields=[dict(key='first_name',value='TEST',quad=[[20,20],[80,20],[80,40],[20,40]]),
                     dict(key='id_number',value='123',quad=[[20,60],[80,60],[80,80],[20,80]])]
    def test_crop_never_keeps_a_partial_value(self):
        for i in range(20):
            image,ff=augment(self.image,self.fields,str(i),'field_clip')
            gt=target(ff,image.shape[1],image.shape[0])
            self.assertLess(len(gt),2)
            for f in ff:
                if f['key'] in gt:
                    q=np.asarray(f['quad']);self.assertTrue((q[:,1]>=0).all() and (q[:,1]<=image.shape[0]).all())
    def test_mask_never_trains_the_hidden_value(self):
        image,ff=augment(self.image,self.fields,'mask','value_mask')
        gt=target(ff,200,100);self.assertLess(len(gt),2)
        self.assertTrue(all(f['key'] not in gt for f in ff if f['occluded']))
    def test_author_field_mapping_has_no_invented_full_name(self):
        source=dict(fields=[dict(author_key='name',value='A',quad=self.fields[0]['quad']),
                            dict(author_key='surname',value='B',quad=self.fields[1]['quad']),
                            dict(author_key='mrz_line0',value='SECRET',quad=self.fields[0]['quad'])])
        ff=mapped_fields(source);self.assertEqual({f['key'] for f in ff},{'first_name','last_name'})
    def test_no_semantic_mapping_for_positional_field01(self):self.assertNotIn('field01',FIELD_MAP)
    def test_test_renderer_layouts_differ_from_training(self):
        _,_,a,_=mock('v2-unit/train',0,'train');_,_,b,_=mock('v2-unit/test',0,'test')
        self.assertLess(a,6);self.assertGreaterEqual(b,6)

@unittest.skipUnless((DATA/'samples.json').exists(),'Dataset still being acquired')
class Dataset(unittest.TestCase):
    def test_roles_have_disjoint_ids_and_rasters(self):
        rows=load();roles=['train','development','test']
        for a in roles:
            for b in roles:
                if a==b:continue
                self.assertFalse({r['physical_id'] for r in rows if r['role']==a}&{r['physical_id'] for r in rows if r['role']==b})
                self.assertFalse({r['input_sha256'] for r in rows if r['role']==a}&{r['input_sha256'] for r in rows if r['role']==b})
    def test_control_and_partial_have_same_ordered_identity_slots(self):
        a=load('train','control');b=load('train','partial')
        self.assertEqual([(r['physical_id'],r['slot']) for r in a],[(r['physical_id'],r['slot']) for r in b])
        self.assertEqual(len(a),640)
        for x,y in zip(a,b):
            if x['slot']<3:self.assertEqual(x['input_sha256'],y['input_sha256'])
    def test_held_layouts_and_samsung_do_not_enter_train(self):
        for r in load('train'):
            self.assertNotIn(r['layout'],('fin_id','lva_passport'))
            if r['source']=='midv2020':self.assertEqual(r['device'],'iPhone XS Max')
    def test_photo_evaluation_is_new_to_earlier_studies(self):
        sources=read(DATA/'sources.json')
        self.assertTrue(all(not r['prior_study_used'] for r in sources if r['role']!='train'))

if __name__=='__main__':unittest.main()
