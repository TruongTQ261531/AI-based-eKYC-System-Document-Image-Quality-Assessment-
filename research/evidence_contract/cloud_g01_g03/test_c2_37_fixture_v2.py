"""Run: python -m unittest research.evidence_contract.cloud_g01_g03.test_c2_37_fixture_v2"""
import unittest
from collections import Counter
from . import c2_37_fixture_v2 as v


def fixture():
    cs, reader = v.locked_cases(), v.synthetic_reader()
    outputs = {h: v.seal(dict(image=h, reader=reader.copy(), content='SYNTH_SAME_TEXT'))
               for c in cs for h in (c['before'], c['after'])}
    statuses, decisions, truth = [], [], []
    pairs = [('FAULT','UNKNOWN'), ('FAULT','FAULT'), ('NO_FAULT','UNKNOWN'),
             ('UNKNOWN','UNKNOWN'), ('INVALID_TEST','INVALID_TEST'), ('FAULT','FAULT'), ('NO_FAULT','NO_FAULT')]
    for i,c in enumerate(cs,1):
        k = c['case_id']; ref = v.digest(['SYNTH_REFERENCE', k])
        s = dict(case_id=k, rights='PERMITTED', proposals=2, adjudicated=True, reference=ref,
                 conditions=dict.fromkeys(v.CONDITIONS,'PASS'), exposure='UNKNOWN')
        statuses.append(v.seal(s))
        a,z = pairs[(i-1)%7]
        b,o = [outputs[c[x]]['record_sha256'] for x in ('before','after')]
        decisions.append(v.seal(dict(case_id=k, shared_payload=v.payload(c,s,reader,b,o),asserted=a,checked=z)))
        if i%3:
            truth.append(v.seal(dict(case_id=k,field=c['field'],after_record=o,basis='SYNTH_INDEPENDENT',
                                    value=i%3==1,evidence=v.digest(['SYNTH_TRUTH',k,c['field'],o]))))
    return dict(schema='C2-37-fixture/2',scope='SYNTHETIC_ONLY',membership=cs,reader=reader,
                statuses=statuses,outputs=list(outputs.values()),decisions=decisions,truth=truth)


def change(item, **updates):
    item.pop('record_sha256'); item.update(updates); item.update(v.seal(item))


def drop(data, ids):
    for key in ('decisions','truth'):
        data[key] = [r for r in data[key] if r['case_id'] not in ids]


class TestV2(unittest.TestCase):
    def test_full_and_differential_v1(self):
        r=v.analyze(fixture()); m=r['enrolled_frame']['metrics']
        self.assertEqual(r['flow']['enrolled'],dict(candidates=37,physical_ids=18))
        self.assertEqual(r['unique_cached_images'],45)
        self.assertEqual(m['matrix'],[[11,0,6,0],[0,5,5,0],[0,0,5,0],[0,0,0,5]])
        self.assertEqual(m['missing_truth'],12)
        self.assertEqual(m['withdrawals']['all'],6)
        self.assertEqual(r['qualified_frame_proposal']['metrics'],m)
        self.assertEqual(r['superiority'],'NOT_EVALUATED')
    def test_qualification_fail_distinct_from_pointwise(self):
        for cond in ('primary_removed_after','semantic_equality_approved'):
            with self.subTest(cond=cond):
                d=fixture();s=d['statuses'][0];s['conditions'][cond]='FAIL';change(s)
                r=v.analyze(d)
                self.assertEqual(r['enrolled_frame']['metrics']['candidates'],37)
                self.assertEqual(r['qualified_frame_proposal']['metrics']['candidates'],36)
                self.assertEqual(r['conditions'][cond]['FAIL'],dict(candidates=1,physical_ids=1))
    def test_unknown_qualification_withholds_subset(self):
        d=fixture();s=d['statuses'][0];s['conditions']['semantic_equality_approved']='UNKNOWN';change(s)
        r=v.analyze(d);self.assertEqual(r['qualified_frame_proposal']['status'],'QUALIFICATION_PENDING')
        self.assertIsNone(r['qualified_frame_proposal']['metrics'])
    def test_provenance_blocks_decision(self):
        for state in ('UNKNOWN','FAIL'):
            d=fixture();s=d['statuses'][0];s['conditions']['provenance_verified']=state;change(s)
            with self.assertRaisesRegex(ValueError,'provenance'):v.analyze(d)
    def test_membership_locked(self):
        for key,value in [('case_id','SYNTH_REPLACEMENT'),('field','SYNTH_OTHER'),('backup_precision','YYYYMMDD'),
                          ('backup_region','SYNTH_WRONG'),('template','25'),('physical_id','SYNTH_OTHER')]:
            with self.subTest(key=key):
                d=fixture();d['membership'][0][key]=value
                with self.assertRaisesRegex(ValueError,'membership'):v.analyze(d)
        d=fixture();d['membership'].reverse()
        with self.assertRaisesRegex(ValueError,'membership'):v.analyze(d)
    def test_record_tamper(self):
        d=fixture();d['decisions'][0]['checked']='FAULT'
        with self.assertRaisesRegex(ValueError,'digest'):v.analyze(d)
    def test_wrong_shared_payload_and_transition(self):
        d=fixture();change(d['decisions'][0],shared_payload='0'*64)
        with self.assertRaisesRegex(ValueError,'shared payload'):v.analyze(d)
        d=fixture();change(d['decisions'][0],checked='NO_FAULT')
        with self.assertRaisesRegex(ValueError,'transition'):v.analyze(d)
    def test_truth_copy_and_field(self):
        d=fixture();change(d['truth'][1],evidence=d['truth'][0]['evidence'])
        with self.assertRaisesRegex(ValueError,'Truth basis'):v.analyze(d)
        d=fixture();change(d['truth'][0],field='SYNTH_WRONG')
        with self.assertRaisesRegex(ValueError,'Truth field'):v.analyze(d)
    def test_denied_cache_not_authorized(self):
        d=fixture();s=d['statuses'][0];s['conditions']['reference_approved']='FAIL'
        change(s,rights='DENIED',proposals=0,adjudicated=False,reference=None);drop(d,{'SYNTH_C1'})
        r=v.analyze(d);self.assertEqual(r['flow']['cached_pair']['candidates'],37)
        self.assertEqual(r['flow']['authorized_pair']['candidates'],36)
        self.assertIsNone(r['enrolled_frame']['metrics']);self.assertEqual(r['qualified_frame_proposal']['metrics']['candidates'],36)
    def test_unapproved_reference_unknown_not_qualified(self):
        d=fixture();s=d['statuses'][0];s['conditions']['reference_approved']='FAIL';change(s,reference=None)
        c=d['membership'][0];o={x['image']:x['record_sha256'] for x in d['outputs']}
        change(d['decisions'][0],shared_payload=v.payload(c,s,d['reader'],o[c['before']],o[c['after']]),asserted='UNKNOWN',checked='UNKNOWN')
        r=v.analyze(d);self.assertEqual(r['flow']['reference_approved']['candidates'],36)
        self.assertEqual(r['enrolled_frame']['metrics']['candidates'],37)
        self.assertIsNone(r['qualified_frame_proposal']['metrics'])
        change(d['decisions'][0],asserted='FAULT')
        with self.assertRaisesRegex(ValueError,'Binary without reference'):v.analyze(d)
    def test_missing_output_and_decision(self):
        d=fixture();c=d['membership'][0];h=c['before'];affected={x['case_id'] for x in d['membership'] if x['before']==h}
        d['outputs']=[o for o in d['outputs'] if o['image']!=h];drop(d,affected)
        r=v.analyze(d);self.assertEqual(r['flow']['missing_output']['candidates'],len(affected));self.assertIsNone(r['enrolled_frame']['metrics'])
        d=fixture();drop(d,{'SYNTH_C1'});r=v.analyze(d)
        self.assertEqual(r['flow']['missing_decision_given_authorized_pair']['candidates'],1);self.assertIsNone(r['qualified_frame_proposal']['metrics'])
    def test_no_truth_and_empty_qualified(self):
        d=fixture();d['truth']=[];m=v.analyze(d)['enrolled_frame']['metrics']
        self.assertIsNone(m['far_difference']['value']);self.assertIsNone(m['arms']['checked']['base']['sensitivity_all_labeled_faults']['value'])
        for s in d['statuses']:s['conditions']['primary_removed_after']='FAIL';change(s)
        self.assertEqual(v.analyze(d)['qualified_frame_proposal']['status'],'EMPTY_FRAME')
    def test_output_reuse_and_duplicates(self):
        d=fixture();self.assertEqual(len({r['content'] for r in d['outputs']}),1)
        self.assertEqual(len({r['record_sha256'] for r in d['outputs']}),45);v.analyze(d)
        d['outputs'].append(d['outputs'][0]);self.assertRaisesRegex(ValueError,'duplicate',v.analyze,d)
    def test_wrong_reader_and_production(self):
        d=fixture();d['scope']='PRODUCTION';self.assertRaisesRegex(ValueError,'Production forbidden',v.analyze,d)
        for k in ('run','runtime','checkpoint','config','profile'):
            d=fixture();o=d['outputs'][0];o['reader'][k]='SYNTH_CHANGED';change(o)
            self.assertRaisesRegex(ValueError,'Output binding',v.analyze,d)
    def test_duplicate_status_decision_truth_and_missing_status(self):
        for key in ('statuses','decisions','truth'):
            d=fixture();d[key].append(d[key][0]);self.assertRaisesRegex(ValueError,'duplicate',v.analyze,d)
        d=fixture();d['statuses'].pop();self.assertRaisesRegex(ValueError,'Incomplete status',v.analyze,d)
    def test_status_sequence(self):
        d=fixture();change(d['statuses'][0],proposals=1);self.assertRaisesRegex(ValueError,'Adjudication',v.analyze,d)
        d=fixture();change(d['statuses'][0],rights='PENDING');self.assertRaisesRegex(ValueError,'Proposals without rights',v.analyze,d)
    def test_exhaustive_missing_bounds(self):
        d=fixture();m=v.analyze(d)['enrolled_frame']['metrics'];known={r['case_id']:r['value'] for r in d['truth']}
        missing=[r['case_id'] for r in d['decisions'] if r['case_id'] not in known]
        values=[[] for _ in range(5)]
        for bits in range(1<<len(missing)):
            t=dict(known,**{k:bool(bits&(1<<i)) for i,k in enumerate(missing)})
            f=[r for r in d['decisions'] if t[r['case_id']]];n=[r for r in d['decisions'] if not t[r['case_id']]]
            vals=[sum(r[a]=='FAULT' for r in group)/len(group) for group in (f,n) for a in v.ARMS]
            vals.append(vals[2]-vals[3])
            for a,b in zip(values,vals):a.append(b)
        targets=[m['arms'][a][k] for k in ('sensitivity_bounds','far_bounds') for a in v.ARMS]+[m['far_difference_bounds']]
        for target,vals in zip(targets,values):
            self.assertAlmostEqual(target['minimum'],min(vals));self.assertAlmostEqual(target['maximum'],max(vals))


if __name__=='__main__':unittest.main()
