import unittest
import numpy as np
from research.hp_data import pair_for,refs_for,regions_for,masked_capture


def node(key,box,kind='body',source=None):
    a,b,c,d=box;q=[[a,b],[c,b],[c,d],[a,d]]
    return dict(key=key,value=key.upper(),kind=kind,author_source=source or key,priority=0,
                components=[q],mask_components=[q])


class PairedMaskSemantics(unittest.TestCase):
    def test_all_duplicate_sources_of_hidden_key_are_masked(self):
        nodes=[node('a',(10,10,35,20)),node('a',(10,80,35,90),'text','mrz'),node('b',(10,24,35,34))]
        pair=pair_for(nodes,100,100,'train')
        self.assertIsNotNone(pair)
        refs=refs_for(nodes,regions_for(nodes,'a'),100,100)['target']
        self.assertNotIn('a',refs);self.assertIn('b',refs)
        # Hiding one body region alone must not label a remaining MRZ source absent.
        self.assertIn('a',refs_for(nodes,regions_for(nodes[:1],'a'),100,100)['target'])

    def test_pair_is_refused_if_no_whole_retained_body_source_survives(self):
        nodes=[node('a',(10,10,35,20)),node('b',(10,10,35,20))]
        self.assertIsNone(pair_for(nodes,100,100,'train'))

    def test_distant_keys_do_not_become_nearby_training_pairs(self):
        self.assertIsNone(pair_for([node('a',(1,1,10,10)),node('b',(85,85,95,95))],100,100,'train'))

    def test_counterfactual_images_have_opposite_targets(self):
        nodes=[node('a',(10,10,35,20)),node('b',(10,24,35,34))]
        full={'fields':[dict(key=n['key'],quad=n['components'][0],value=n['value']) for n in nodes]}
        im=np.full((100,100,3),255,np.uint8)
        first=masked_capture(im,full,nodes,'a','b');second=masked_capture(im,full,nodes,'b','a')
        self.assertEqual(set(first[2]['target']),{'b'});self.assertEqual(set(second[2]['target']),{'a'})
        self.assertFalse(np.array_equal(first[0],second[0]))

    def test_retained_label_is_part_of_authored_evidence(self):
        a=node('a',(10,10,35,20));b=node('b',(10,24,35,34))
        b['components'].append(a['components'][0])
        self.assertIsNone(pair_for([a,b],100,100,'train'))


if __name__=='__main__':unittest.main()
