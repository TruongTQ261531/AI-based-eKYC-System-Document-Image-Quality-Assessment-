import unittest

from research.priority_progress import diagnose, geometry, select_train


def fixture():
    return dict(role='development', uid='dev/1', physical_id='dev', width=100, height=100,
        fields=[dict(key='id_number',quad=[[10,10],[40,10],[40,20],[10,20]],occluded=True),
                dict(key='full_name',quad=[[10,24],[40,24],[40,34],[10,34]])],
        target={'full_name':'VISIBLE'}, source_refs={'full_name':[dict(value='VISIBLE',kind='body')]})


class HardCaseLeakageAndSourceSemantics(unittest.TestCase):
    def test_test_or_train_predictions_cannot_enter_development_mining(self):
        for role in ('train','test'):
            sample=fixture();sample['role']=role
            with self.assertRaises(ValueError):diagnose(sample,'{}')

    def test_reports_both_hidden_output_and_neighbor_omission_without_text(self):
        result=diagnose(fixture(),'{"id_number":"GUESS"}')
        self.assertEqual(result['hidden_output_keys'],['id_number'])
        self.assertEqual(result['neighbor_omission_keys'],['full_name'])
        self.assertNotIn('GUESS',str(result));self.assertNotIn('VISIBLE',str(result))

    def test_mrz_alternative_prevents_false_hidden_label(self):
        sample=fixture();sample['target']['id_number']='12345'
        sample['source_refs']['id_number']=[dict(value='12345',kind='text')]
        result=diagnose(sample,'{"id_number":"12345","full_name":"VISIBLE"}')
        self.assertEqual(result['hidden_output_keys'],[])
        self.assertEqual(geometry(sample),(set(),set()))

    def test_training_inventory_rejects_dev_and_test_identities(self):
        for role in ('development','test'):
            sample=fixture();sample['role']=role
            with self.assertRaises(ValueError):select_train([sample],{})

    def test_training_selection_keeps_one_case_per_id(self):
        rows=[]
        for uid in ('a/1','a/2','b/1'):
            sample=fixture();sample.update(role='train',uid=uid,physical_id=uid[0],capture='value_mask',input_sha256='x')
            rows.append(sample)
        selected=select_train(rows,{'full_name':3},limit=32)
        self.assertEqual(len(selected),2)
        self.assertEqual({r['physical_id'] for r in selected},{'a','b'})


if __name__=='__main__':unittest.main()
