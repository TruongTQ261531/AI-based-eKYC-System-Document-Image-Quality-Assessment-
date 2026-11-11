"""Development baseline mechanism tests; all outputs below are injected controls."""
from dataclasses import replace
import inspect
import json
from pathlib import Path
import random
import tempfile
import unittest

from research.evidence_contract import generator, oracle
from research.evidence_contract.fixtures import backup_fixture, shared_context_fixture
from research.evidence_contract.source_graph import digest, pixel_sha256
from research.evidence_contract.validity import Validity
from research.evidence_contract.runner import InputRequest, Runner, sha_file
from research.evidence_contract.normalized_output import NativeOutput
from research.evidence_contract.tests.test_runner_oracle import output, spec
from research.evidence_contract.task5 import baselines as b, planning
from research.evidence_contract.task5.pilot import readonly_cached


class BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.graph,cls.a,cls.n=backup_fixture()
        cls.truth={f.key:f.reference_value for f in cls.graph.fields}

    def pair(self,kind):
        return generator.generate(self.image,self.graph,generator.plan(self.graph,kind,target_key=self.a,retained_key=self.n))

    def values(self,pair,after,before=None):
        return output(self.truth if before is None else before,pair.original),output(after,pair.followup)

    def test_correct_backup_not_an_A_B3_alarm_but_nominal_B2_disagrees(self):
        p=self.pair('single_source_mask');before,after=self.values(p,self.truth)
        checks=b.run_checks(self.graph,p.validation,before,after)
        self.assertFalse(b.unpack(checks['A'])['alarm'])
        self.assertFalse(b.unpack(checks['B3'])['alarm'])
        self.assertTrue(b.unpack(checks['B2'])['alarm'])
        self.assertTrue(b.unpack(checks['A_no_alternative'])['alarm'])
        self.assertFalse(b.unpack(checks['A'])['confirmed'])

    def test_full_reference_error_is_not_equivalent_to_supported_field_fault(self):
        p=self.pair('all_sources_mask');before,after=self.values(p,{self.n:self.truth[self.n]})
        self.assertFalse(b.proposed(self.graph,p.validation,before,after).alarm_issued)
        self.assertTrue(b.conventional(self.graph,p.validation,before,after).alarm)
        self.assertFalse(b.visible_reference(self.graph,p.validation,before,after).alarm)

    def test_strong_B3_already_catches_non_interference_pointwise_error(self):
        p=self.pair('pair_a_mask');before,after=self.values(p,{self.n:'WRONG'})
        checks=b.run_checks(self.graph,p.validation,before,after)
        self.assertTrue(b.unpack(checks['A'])['alarm'])
        self.assertTrue(b.unpack(checks['B3'])['alarm'])
        self.assertFalse(b.unpack(checks['A_no_NI'])['alarm'])
        self.assertEqual(b.unpack(checks['A_no_NI'])['verdict'],'INCONCLUSIVE')

    def test_original_wrong_does_not_hide_B3_reading_error(self):
        p=self.pair('pair_a_mask');before,after=self.values(p,{self.n:'WRONG'},before={self.n:'WRONG'})
        self.assertEqual(b.proposed(self.graph,p.validation,before,after).verdict,oracle.Verdict.INCONCLUSIVE)
        self.assertTrue(b.visible_reference(self.graph,p.validation,before,after).alarm)

    def test_no_alternative_changes_C2_only(self):
        for kind in ('all_sources_mask','pair_a_mask','geometry_translate'):
            p=self.pair(kind);before,after=self.values(p,{})
            self.assertEqual(b.unpack(b.proposed(self.graph,p.validation,before,after)),b.unpack(b.no_alternative(self.graph,p.validation,before,after)))

    def test_flat_matches_primary_conditioned_relations(self):
        for kind in ('all_sources_mask','single_source_mask','pair_a_mask','geometry_translate'):
            p=self.pair(kind)
            for predicted in (self.truth,{}, {self.n:'WRONG'}):
                for original in (self.truth,{}):
                    before,after=self.values(p,predicted,before=original)
                    a=b.unpack(b.proposed(self.graph,p.validation,before,after))
                    flat=b.unpack(b.flat_contract(self.graph,p.validation,before,after))
                    self.assertEqual((a['verdict'],a['alarm']),(flat['verdict'],flat['alarm']),(kind,predicted,original))

    def test_intent_only_validator_can_raise_an_invalid_context_alarm(self):
        image,graph,a,n=shared_context_fixture()
        p=generator.generate(image,graph,generator.plan(graph,'pair_a_mask',target_key=a,retained_key=n))
        values={f.key:f.reference_value for f in graph.fields}
        before,after=output(values,p.original),output({n:'WRONG'},p.followup)
        self.assertEqual(p.validation.status,Validity.INVALID_TEST)
        self.assertEqual(b.proposed(graph,p.validation,before,after).verdict,oracle.Verdict.INVALID_TEST)
        candidate=b.no_validator(graph,p.validation,before,after)
        self.assertEqual(candidate.verdict,oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertEqual(candidate.test_validity,'UNCHECKED')
        self.assertFalse(candidate.software_fault_confirmed)

    def test_missing_erasure_is_not_silently_validated_by_intent(self):
        p=next(p for name,p in planning.diagnostics() if name=='incomplete_target_erasure')
        before,after=self.values(p,self.truth)
        self.assertEqual(b.proposed(p.graph,p.validation,before,after).verdict,oracle.Verdict.INVALID_TEST)
        self.assertTrue(b.no_validator(p.graph,p.validation,before,after).alarm_issued)

    def test_legacy_functions_are_actual_frozen_implementations(self):
        visibility,score=b.legacy_functions()
        self.assertEqual(visibility.__module__,'research.v3_sources')
        self.assertEqual(score.__module__,'research.v3_metrics')
        p=self.pair('single_source_mask');before,after=self.values(p,self.truth)
        self.assertFalse(b.legacy_v3(self.graph,p.validation,before,after).alarm)

    def test_legacy_gate_is_one_factor_on_invalid_context(self):
        image,graph,a,n=shared_context_fixture()
        p=generator.generate(image,graph,generator.plan(graph,'pair_a_mask',target_key=a,retained_key=n))
        values={f.key:f.reference_value for f in graph.fields}
        before,after=output(values,p.original),output({},p.followup)
        self.assertTrue(b.legacy_v3(graph,p.validation,before,after,gate=False).alarm)
        self.assertEqual(b.legacy_v3(graph,p.validation,before,after,gate=True).verdict,'INVALID_TEST')

    def test_source_agnostic_interface_accepts_no_graph_or_reference(self):
        parameters=set(inspect.signature(b.source_agnostic).parameters)
        self.assertFalse(parameters & {'graph','reference','fields','expected_values','polygon'})

    def test_json_error_is_not_a_successful_refusal_in_baselines(self):
        p=self.pair('all_sources_mask')
        before,after=output(self.truth,p.original),output({},p.followup,usable_text='{broken')
        checks=b.run_checks(self.graph,p.validation,before,after)
        self.assertTrue(all(b.unpack(value)['verdict']=='INCONCLUSIVE' for value in checks.values()))


class SelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.panel=planning.approved_panel()
        cls.originals={name:pixel_sha256(data[0]) for name,data in cls.panel.items()}
        cls.pool=planning.pools(cls.panel)

    def test_equal_candidate_domains_and_fixed_budget_for_both_arms(self):
        for index,seed in enumerate(planning.SEEDS):
            records={}
            for arm in ('A','B1'):
                pairs,records[arm]=planning.select(self.pool,arm=arm,seed=seed,seed_index=index)
                self.assertEqual(len(pairs),10)
                self.assertEqual(len({h for p in pairs for h in (p.validation.before_pixel_sha256,p.validation.after_pixel_sha256)}),10)
                self.assertTrue(all(p.validation.status==Validity.VALID for p in pairs))
            for a,b0 in zip(records['A'],records['B1']):
                for key in ('case','family','area_bin','domain_sha256','domain_size'):
                    self.assertEqual(a[key],b0[key])

    def test_uniform_random_is_over_full_eligible_domain(self):
        _,ledger=planning.select(self.pool,arm='B1',seed=42)
        for record in ledger:
            eligible=sorted([c for c in self.pool if (c.case,c.family,c.area_bin)==(
                record['case'],record['family'],record['area_bin']) and c.eligible],key=lambda c:c.uid)
            rng=random.Random(int(digest(['task5-selector/1',42,record['case'],record['family']])[:16],16))
            self.assertEqual(record['selected_id'],eligible[rng.randrange(len(eligible))].uid)

    def test_source_pool_does_not_limit_random_to_body_only(self):
        candidates=[c for c in self.pool if c.family=='backup' and c.eligible]
        self.assertTrue(any(len(c.pair.mutation.hidden_source_ids)>1 for c in candidates))
        self.assertTrue(any(c.source_signature==('mrz',) for c in candidates))

    def test_deterministic_selection_and_no_original_mutation(self):
        for arm in ('A','B1'):
            first=planning.select(self.pool,arm=arm,seed=42)[1]
            self.assertEqual(first,planning.select(self.pool,arm=arm,seed=42)[1])
        for name,data in self.panel.items():
            self.assertEqual(pixel_sha256(data[0]),self.originals[name])

    def test_test_role_and_personal_data_are_rejected(self):
        for changes in (dict(role='test'),dict(data_policy='personal')):
            image,graph,a,n=self.panel['backup']
            with self.assertRaises(ValueError):
                planning.pools(dict(bad=(image,replace(graph,**changes),a,n)))

    def test_diagnostic_invalid_unknown_attempts_are_retained(self):
        cases=planning.diagnostics()
        self.assertEqual(len(cases),4)
        self.assertEqual(sorted(p.validation.status.value for _,p in cases),['INCONCLUSIVE','INCONCLUSIVE','INVALID_TEST','INVALID_TEST'])


class HistoricalCacheTests(unittest.TestCase):
    def test_readonly_cache_never_appends_event_or_creates_missing_lock(self):
        root=Path(__file__).resolve().parents[1]/'local/task5_unit_tmp'
        root.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as name:
            root=Path(name);image,graph,a,n=backup_fixture()
            path=root/'image.png';path.write_bytes(generator.png_bytes(image))
            request=InputRequest(str(path),sha_file(path),pixel_sha256(image),'fixture','fictional')
            calls=[]
            def loader(_):
                def predict(rgb):
                    calls.append(1)
                    return NativeOutput('{}',.1,.1,{})
                return predict
            runner=Runner(spec(),root/'store',loader)
            original=runner.infer(request)
            log_sha=sha_file(runner.events.path)
            existing={p.relative_to(root).as_posix() for p in root.rglob('*')}
            replay=readonly_cached(runner,request)
            self.assertEqual(original.call_id,replay.call_id)
            self.assertEqual(len(calls),1)
            self.assertEqual(log_sha,sha_file(runner.events.path))
            missing=replace(request,file_sha256='1'*64,pixel_sha256='2'*64,path=str(root/'missing.png'))
            self.assertIsNone(readonly_cached(runner,missing))
            self.assertEqual(existing,{p.relative_to(root).as_posix() for p in root.rglob('*')})


if __name__=='__main__':unittest.main()
