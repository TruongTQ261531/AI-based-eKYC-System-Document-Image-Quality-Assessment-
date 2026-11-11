"""Synthetic oracle injections and fake readers ONLY; no model-error claims."""
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image

from research.evidence_contract import contracts, evaluator, generator, oracle
from research.evidence_contract.fixtures import backup_fixture
from research.evidence_contract.normalized_output import NativeOutput, ReaderSpec, canonical, normalize, parse_fields
from research.evidence_contract.runner import EventLog, InputRequest, Runner, sha_file, write_once
from research.evidence_contract.source_graph import digest, pixel_sha256
from research.evidence_contract.validity import Validity


def spec(**changes):
    values = dict(reader_id="fixture-reader", model_version="injected-test-only/1",
                  model_sha256="a" * 64, config_json=canonical(dict(seed=42)),
                  inference_code_sha256="b" * 64, runtime_json=canonical(dict(runtime="test")),
                  output_origin="oracle_unit_injected")
    values.update(changes)
    return ReaderSpec(**values)


def output(values, image, *, usable_text=None, **changes):
    native = NativeOutput(json.dumps(values) if usable_text is None else usable_text, .2, .1,
                          dict(predictor_receives="pixels_only"))
    result = normalize(spec(), native, input_file_sha256="c" * 64,
                       input_pixel_sha256=pixel_sha256(image), cache_key="d" * 64,
                       call_id=digest([pixel_sha256(image), native.text]))
    return replace(result, **changes)


class NormalizationTests(unittest.TestCase):
    def test_fences_preserve_tolerant_vs_strict(self):
        fields, flags = parse_fields('```json\n{"id_number":"123"}\n```')
        self.assertEqual(fields, {"id_number": "123"})
        self.assertFalse(flags["strict_json_valid"])
        self.assertTrue(flags["usable_for_contracts"])

    def test_invalid_json_not_valid_empty_output(self):
        for text in ('{', '[]', '{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e9999}'):
            with self.subTest(text=text):
                _, flags = parse_fields(text)
                self.assertFalse(flags["usable_for_contracts"])
        self.assertTrue(parse_fields('{}')[1]["usable_for_contracts"])

    def test_bad_types_are_flagged_not_empty_omissions(self):
        self.assertFalse(parse_fields('{"a": ["x"]}')[1]["usable_for_contracts"])
        self.assertFalse(parse_fields('{"a": true}')[1]["usable_for_contracts"])
        self.assertEqual(parse_fields('{"a":123,"b":null,"c":""}')[0], {"a": "123"})

    def test_native_confidence_requires_real_scope(self):
        with self.assertRaises(ValueError):
            NativeOutput('{}', .1, .1, {}, confidence=.9).validate()
        with self.assertRaises(ValueError):
            NativeOutput('{}', .1, .1, {"embedding": [1]}).validate()
        with self.assertRaises(ValueError):
            NativeOutput('{}', float('nan'), .1, {}).validate()
        with self.assertRaises(ValueError):
            NativeOutput('{}', .1, .1, {}, native_tokens=({'text': 'x', 'confidence': True, 'box': []},)).validate()

    def test_no_fabricated_confidence_or_missing_defaults(self):
        record = output({}, np.zeros((4, 5, 3), dtype=np.uint8))
        self.assertIsNone(record.confidence)
        self.assertIsNone(record.missing_fields)
        self.assertNotIn('raw_text', record.public())

    def test_actual_reader_registration_gate(self):
        with self.assertRaises(ValueError):
            spec(output_origin="actual_model")

    def test_schema_required_fields_match_serialized_normalized_record(self):
        path = Path(__file__).resolve().parents[1] / 'normalized_output.schema.json'
        schema = json.loads(path.read_text(encoding='utf-8'))
        record = json.loads(json.dumps(output({}, np.zeros((4, 5, 3), dtype=np.uint8)).to_dict()))
        self.assertEqual(set(record), set(schema['required']))
        self.assertEqual(set(record), set(schema['properties']))
        self.assertEqual(schema['properties']['missing_fields']['type'], 'null')
        self.assertFalse(schema['additionalProperties'])


class RunnerTests(unittest.TestCase):
    def setUp(self):
        # Use the authorized workspace, not Windows' redirected application temp.
        temp_root = Path(__file__).resolve().parents[1] / 'local/unit_tmp'
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=temp_root)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rgb = np.full((14, 18, 3), 190, dtype=np.uint8)
        path = self.root / 'input.png'
        Image.fromarray(self.rgb).save(path)
        self.request = InputRequest(str(path), sha_file(path), pixel_sha256(self.rgb), 'fixture', 'fictional')
        self.loads = self.calls = 0

    def loader(self, _):
        self.loads += 1
        def predict(rgb):
            self.assertIsInstance(rgb, np.ndarray)
            self.assertTrue(np.array_equal(rgb, self.rgb))
            self.calls += 1
            return NativeOutput('{"school":"FICTIONAL"}', .2, .1, {})
        return predict

    def runner(self, **kw):
        return Runner(spec(**kw), self.root / 'store', self.loader)

    def test_resume_no_inference_no_model_load_and_replay_unchanged_log(self):
        runner = self.runner()
        a = runner.infer(self.request)
        b = self.runner().infer(self.request)
        self.assertEqual((self.calls, self.loads), (1, 1))
        self.assertEqual(a.raw_text, b.raw_text)
        self.assertEqual(b.access_mode, 'cache_hit')
        event_sha = sha_file(runner.events.path)
        c = Runner(spec(), runner.store).infer(self.request, replay=True)
        self.assertEqual(c.access_mode, 'replay')
        self.assertEqual(event_sha, sha_file(runner.events.path))
        self.assertEqual(sum(e['event'] == 'inference_begin' for e in runner.events.read()), 1)

    def test_missing_replay_does_not_load_model(self):
        with self.assertRaises(FileNotFoundError):
            self.runner().infer(self.request, replay=True)
        self.assertEqual((self.loads, self.calls), (0, 0))

    def test_cache_key_freezes_all_inference_inputs(self):
        original = self.runner()
        keys = {original.key(self.request)}
        for options in (dict(model_sha256='f' * 64), dict(config_json=canonical(dict(seed=43))),
                        dict(inference_code_sha256='e' * 64), dict(runtime_json=canonical(dict(runtime='other')))):
            keys.add(self.runner(**options).key(self.request))
        keys.add(original.key(replace(self.request, file_sha256='1' * 64)))
        keys.add(original.key(replace(self.request, pixel_sha256='2' * 64)))
        self.assertEqual(len(keys), 7)

    def test_corrupt_cache_preserved_no_extra_call(self):
        runner = self.runner()
        runner.infer(self.request)
        cache = next((runner.store / 'raw').glob('*.json'))
        cache.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError):
            runner.infer(self.request)
        self.assertEqual(self.calls, 1)
        self.assertEqual(cache.read_text(), '{}')

    def test_model_malformed_json_is_cached_not_rerun(self):
        def loader(_):
            def predict(rgb):
                self.calls += 1
                return NativeOutput('{broken', .2, .1, {})
            return predict
        runner = Runner(spec(), self.root / 'store', loader)
        a = runner.infer(self.request)
        b = runner.infer(self.request)
        self.assertFalse(a.json_validity['usable_for_contracts'])
        self.assertEqual((self.calls, b.access_mode), (1, 'cache_hit'))

    def test_forbidden_roles_and_personal_unknown_policy_block_before_loading(self):
        for request in (replace(self.request, role='test'), replace(self.request, data_policy='personal'),
                        replace(self.request, data_policy='unknown')):
            with self.assertRaises(ValueError):
                self.runner().infer(request)
        self.assertEqual(self.loads, 0)

    def test_input_tamper_blocked_before_loading(self):
        Image.fromarray(np.zeros_like(self.rgb)).save(self.request.path)
        with self.assertRaises(ValueError):
            self.runner().infer(self.request)
        self.assertEqual(self.loads, 0)

    def test_two_runners_same_key_invoke_once(self):
        barrier = threading.Barrier(2)
        def work(_):
            runner = self.runner()
            barrier.wait()
            return runner.infer(self.request).call_id
        with ThreadPoolExecutor(max_workers=2) as executor:
            values = list(executor.map(work, range(2)))
        self.assertEqual(len(set(values)), 1)
        self.assertEqual((self.calls, self.loads), (1, 1))

    def test_ambiguous_previous_call_blocks_automatic_retry(self):
        runner = self.runner()
        runner.events.append('inference_begin', cache_key=runner.key(self.request), call_id='crashed',
                             reader_id=spec().reader_id, output_origin='oracle_unit_injected')
        with self.assertRaises(RuntimeError):
            runner.infer(self.request)
        self.assertEqual(self.calls, 0)

    def test_failed_call_requires_explicit_retry_and_keeps_failure(self):
        def bad(_):
            def fail(rgb):
                raise RuntimeError('injected reader failure')
            return fail
        runner = Runner(spec(), self.root / 'store', bad)
        with self.assertRaises(RuntimeError):
            runner.infer(self.request)
        with self.assertRaises(RuntimeError):
            self.runner().infer(self.request)
        self.runner().infer(self.request, retry_failed=True)
        events = runner.events.read()
        self.assertEqual(sum(e['event'] == 'inference_begin' for e in events), 2)
        self.assertEqual(sum(e['event'] == 'inference_failed' for e in events), 1)

    def test_log_tamper_or_truncation_detected(self):
        log = EventLog(self.root / 'audit')
        log.append('cache_hit', call_id='injected')
        data = log.path.read_bytes()
        log.path.write_bytes(data[:-1])
        with self.assertRaises(ValueError):
            log.read()

    def test_crash_after_raw_commit_recovers_without_a_second_call(self):
        runner = self.runner()
        real_append = runner.events.append
        def interrupted(event, **kw):
            if event == 'inference_completed':
                raise RuntimeError('UNIT-INJECTED crash after cache commit')
            return real_append(event, **kw)
        with patch.object(runner.events, 'append', interrupted):
            with self.assertRaises(RuntimeError):
                runner.infer(self.request)
        result = self.runner().infer(self.request)
        self.assertEqual(result.access_mode, 'cache_hit')
        self.assertEqual(self.calls, 1)
        self.assertEqual(sum(e['event'] == 'inference_recovered' for e in runner.events.read()), 1)

    def test_write_once_cannot_replace_prior_artifact(self):
        target = self.root / 'artifact.json'
        write_once(target, dict(a=1))
        with self.assertRaises(FileExistsError):
            write_once(target, dict(a=2))
        self.assertEqual(json.loads(target.read_text()), dict(a=1))


class OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.graph, cls.a, cls.b = backup_fixture()
        cls.values = {f.key: f.reference_value for f in cls.graph.fields}
        cls.pairs = {name: generator.generate(cls.image, cls.graph,
            generator.plan(cls.graph, name, target_key=cls.a, retained_key=cls.b, seed=42))
            for name in ('single_source_mask', 'all_sources_mask', 'pair_a_mask', 'geometry_translate', 'geometry_rotate90')}

    def result(self, name, after=None, *, before=None, raw=None, **kw):
        pair = self.pairs[name]
        return oracle.evaluate(pair.graph, pair.validation,
            output(self.values if before is None else before, pair.original),
            output(self.values if after is None else after, pair.followup, usable_text=raw), **kw)

    def certificate(self, name, **changes):
        pair = self.pairs[name]
        key = pair.mutation.retained_key if pair.mutation.contract_id == 'C3' else pair.mutation.target_key
        data = dict(graph_sha256=pair.graph.sha256, mutation_sha256=pair.mutation.sha256,
            original_pixel_sha256=pair.validation.before_pixel_sha256, followup_pixel_sha256=pair.validation.after_pixel_sha256,
            contract_id=pair.mutation.contract_id, key=key, basis='independent_human_review', provenance='UNIT-INJECTED; not actual human review',
            artifact_sha256='a' * 64, independent_from_sut=True, independent_from_generator=True,
            reviewers=('unit_A', 'unit_B'), reference_verified=True, mutation_verified=True, semantics_verified=True,
            source_universe_complete=True, absence_verified=True, human_readability_verified=True,
            inspected_source_ids=tuple(s.source_id for s in pair.graph.field(key).realizations), origin='oracle_unit_injected')
        data.update(changes)
        return oracle.EvidenceCertificate(**data)

    def test_c1_refusal_pass_but_assertion_only_candidate_without_independent_proof(self):
        self.assertEqual(self.result('all_sources_mask', {}).verdict, oracle.Verdict.PASS)
        d = self.result('all_sources_mask')
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertIn('UNSUPPORTED_DECLARED_SOURCES', d.categories)
        self.assertNotIn('VERIFIED_ABSENCE_OF_EVIDENCE', d.categories)

    def test_c1_independently_verified_absence(self):
        d = self.result('all_sources_mask', certificate=self.certificate('all_sources_mask'))
        self.assertEqual(d.verdict, oracle.Verdict.CONFIRMED_VIOLATION)
        self.assertIn('VERIFIED_ABSENCE_OF_EVIDENCE', d.categories)
        self.assertFalse(d.software_fault_confirmed)

    def test_c2_mrz_backup_correct_not_hallucination(self):
        self.assertEqual(self.result('single_source_mask').verdict, oracle.Verdict.PASS)

    def test_c2_wrong_value_is_reading_error_not_evidence_absence(self):
        d = self.result('single_source_mask', {**self.values, self.a: 'WRONG'})
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertIn('VALUE_MISMATCH_REFERENCE', d.categories)
        self.assertNotIn('UNSUPPORTED_DECLARED_SOURCES', d.categories)

    def test_c2_omission_not_claimed_human_readable_without_review(self):
        d = self.result('single_source_mask', {})
        self.assertIn('OMISSION_DECLARED_SUPPORTED_FIELD', d.categories)
        d = self.result('single_source_mask', {}, certificate=self.certificate('single_source_mask'))
        self.assertIn('OMISSION_READABLE_FIELD', d.categories)
        self.assertEqual(d.verdict, oracle.Verdict.CONFIRMED_VIOLATION)

    def test_c3_unchanged_neighbor_pass_and_changed_neighbor_candidate(self):
        self.assertEqual(self.result('pair_a_mask', {self.b: self.values[self.b]}).verdict, oracle.Verdict.PASS)
        d = self.result('pair_a_mask', {self.b: 'WRONG'})
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertFalse(d.behavior_regression_verified)

    def test_c3_original_wrong_not_version_regression(self):
        d = self.result('pair_a_mask', {}, before={})
        self.assertEqual(d.verdict, oracle.Verdict.INCONCLUSIVE)
        self.assertFalse(d.alarm_issued)

    def test_c4_only_declared_preserving_operator_is_invariant(self):
        self.assertEqual(self.result('geometry_translate').verdict, oracle.Verdict.PASS)
        self.assertEqual(self.result('geometry_translate', {}).verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertEqual(self.result('geometry_rotate90', {}).verdict, oracle.Verdict.INCONCLUSIVE)

    def test_bad_json_not_a_successful_refusal_or_semantic_omission(self):
        for name in ('all_sources_mask', 'single_source_mask', 'pair_a_mask', 'geometry_translate'):
            d = self.result(name, raw='{not-json')
            self.assertEqual(d.verdict, oracle.Verdict.INCONCLUSIVE)
            self.assertFalse(d.alarm_issued)
            self.assertIn('UNDETERMINED_OUTPUT', d.categories)

    def test_unknown_extra_key_not_automatically_hallucination(self):
        d = self.result('single_source_mask', {**self.values, 'unannotated_key': 'text'})
        self.assertEqual(d.verdict, oracle.Verdict.PASS)

    def test_c2_unknown_invalid_mrz_backup_is_inconclusive_not_hallucination(self):
        image, graph, a, b = backup_fixture(bad_checksum=True)
        pair = generator.generate(image, graph, generator.plan(graph, 'single_source_mask', target_key=a))
        d = oracle.evaluate(graph, pair.validation, output(self.values, image), output(self.values, pair.followup))
        self.assertEqual(d.verdict, oracle.Verdict.INCONCLUSIVE)
        self.assertFalse(d.alarm_issued)
        self.assertNotIn('UNSUPPORTED_DECLARED_SOURCES', d.categories)

    def test_c1_wrong_value_and_source_support_are_separate_axes(self):
        d = self.result('all_sources_mask', {self.a: 'WRONG'})
        self.assertIn('VALUE_MISMATCH_REFERENCE', d.categories)
        self.assertIn('UNSUPPORTED_DECLARED_SOURCES', d.categories)
        self.assertNotIn('VERIFIED_ABSENCE_OF_EVIDENCE', d.categories)

    def test_constructed_support_cannot_certify_human_omission(self):
        certificate = self.certificate('single_source_mask', basis='independent_construction_audit',
                                       human_readability_verified=False)
        d = self.result('single_source_mask', {}, certificate=certificate)
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertNotIn('OMISSION_READABLE_FIELD', d.categories)

    def test_version_regression_requires_four_bound_outputs(self):
        pair = self.pairs['pair_a_mask']
        wrong = {self.b: 'WRONG'}
        quad = contracts.RegressionEvidence('a' * 64, 'b' * 64, pair.validation.before_pixel_sha256,
            pair.validation.after_pixel_sha256, self.values, self.values, self.values, wrong, True, 'UNIT-INJECTED unchanged requirement')
        d = self.result('pair_a_mask', wrong, regression=quad)
        self.assertTrue(d.behavior_regression_verified)
        self.assertFalse(d.software_fault_confirmed)
        d = self.result('pair_a_mask', wrong, regression=replace(quad, stability_verified=False))
        self.assertFalse(d.behavior_regression_verified)

    def test_fault_identity_needs_bound_failure_label_and_patch_proof(self):
        initial = self.result('all_sources_mask')
        gold = oracle.GoldLabel(initial.decision_sha256, True, True, 'UNIT-INJECTED fault', 'e' * 64, True,
            defect_id='unit-fault-only', defect_proof_kind='patch_revert_reproduction', defect_proof_sha256='f' * 64,
            origin='oracle_unit_injected')
        d = self.result('all_sources_mask', gold=gold)
        self.assertTrue(d.software_fault_confirmed)
        self.assertEqual(d.verdict, oracle.Verdict.CONFIRMED_VIOLATION)
        d = self.result('all_sources_mask', gold=replace(gold, decision_sha256='0' * 64))
        self.assertFalse(d.software_fault_confirmed)

    def test_invalid_validation_with_no_after_graph_does_not_crash(self):
        pair = self.pairs['all_sources_mask']
        report = replace(pair.validation, status=Validity.INVALID_TEST, after_graph=None)
        d = oracle.evaluate(pair.graph, report, output(self.values, pair.original), output(self.values, pair.followup))
        self.assertEqual(d.verdict, oracle.Verdict.INVALID_TEST)
        self.assertEqual(d.test_validity, 'INVALID_TEST')

    def test_pixel_or_reader_binding_mismatch_is_invalid(self):
        pair = self.pairs['all_sources_mask']
        d = oracle.evaluate(pair.graph, pair.validation, output(self.values, pair.original),
                            replace(output(self.values, pair.followup), input_pixel_sha256='f' * 64))
        self.assertEqual(d.verdict, oracle.Verdict.INVALID_TEST)
        self.assertEqual(d.test_validity, 'INVALID_TEST')
        self.assertEqual(d.mutation_validity, 'VALID')

    def test_certificate_wrong_pair_or_dependent_rejected(self):
        for changes in (dict(followup_pixel_sha256='b' * 64), dict(independent_from_generator=False),
                        dict(reviewers=('same', 'SAME')), dict(inspected_source_ids=())):
            d = self.result('all_sources_mask', certificate=self.certificate('all_sources_mask', **changes))
            self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)

    def test_limited_source_scope_alarm_remains_candidate(self):
        graph = replace(self.graph, fields=tuple(replace(f, coverage='limited') if f.key == self.a else f for f in self.graph.fields))
        pair = generator.generate(self.image, graph, generator.plan(graph, 'all_sources_mask', target_key=self.a))
        d = oracle.evaluate(graph, pair.validation, output(self.values, pair.original), output(self.values, pair.followup))
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertFalse(d.evidence_certificate_accepted)

    def test_bound_negative_gold_preserves_issued_alarm_for_precision(self):
        name = 'all_sources_mask'
        initial = self.result(name)
        gold = oracle.GoldLabel(initial.decision_sha256, False, True, 'UNIT-INJECTED', 'e' * 64, True,
                                 false_alarm_cause='missing_source', origin='oracle_unit_injected')
        d = self.result(name, gold=gold)
        self.assertEqual(d.verdict, oracle.Verdict.INCONCLUSIVE)
        self.assertTrue(d.alarm_issued)
        self.assertIn('FALSE_ALARM_MISSING_SOURCE_OR_GT', d.categories)

    def test_injected_certificate_cannot_confirm_actual_output(self):
        pair = self.pairs['all_sources_mask']
        before = replace(output(self.values, pair.original), output_origin='actual_model')
        after = replace(output(self.values, pair.followup), output_origin='actual_model')
        d = oracle.evaluate(pair.graph, pair.validation, before, after, certificate=self.certificate('all_sources_mask'))
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)

    def test_gold_does_not_migrate_to_a_different_normalizer(self):
        pair = self.pairs['all_sources_mask']
        before, after = output(self.values, pair.original), output(self.values, pair.followup)
        initial = oracle.evaluate(pair.graph, pair.validation, before, after)
        gold = oracle.GoldLabel(initial.decision_sha256, True, True, 'UNIT-INJECTED', 'e' * 64,
                                True, origin='oracle_unit_injected')
        d = oracle.evaluate(pair.graph, pair.validation, before,
                            replace(after, normalization_code_sha256='f' * 64), gold=gold)
        self.assertEqual(d.verdict, oracle.Verdict.CANDIDATE_VIOLATION)
        self.assertTrue(d.diagnostics['gold_present_but_rejected'])

    def test_injected_oracle_failures_excluded_from_model_results(self):
        d = self.result('all_sources_mask', certificate=self.certificate('all_sources_mask'))
        fields = evaluator.observe_fields(self.graph, output(self.values, self.image))
        report = evaluator.summarize([d], fields, [])
        self.assertEqual(report['verified_failure_count'], 0)
        self.assertEqual(report['contract_evaluations'], 0)
        self.assertEqual(report['injected_decisions_excluded'], 1)
        self.assertIsNone(report['alarm_precision']['value'])


class MetricsTests(unittest.TestCase):
    setUpClass = classmethod(OracleTests.setUpClass.__func__)
    result = OracleTests.result
    def test_field_dedup_missing_unjudged_and_cer_denominators(self):
        # Synthetic records marked as an actual-output *metric fixture*, not actual inference.
        prediction = replace(output({self.a: self.values[self.a], 'unannotated': 'x'}, self.image), output_origin='actual_model')
        fields = evaluator.observe_fields(self.graph, prediction)
        report = evaluator.summarize([], fields + fields, [])
        self.assertEqual(report['supported_reference_fields'], 2)
        self.assertEqual(report['field_exact_match']['value'], .5)
        self.assertEqual(report['unjudged_predicted_key_view_count'], 1)
        self.assertEqual(report['unit_counts']['unique_image_reader_views'], 1)
        self.assertEqual(report['field_f1']['value'], 2 / 3)
        self.assertEqual(evaluator.missing_fields(self.graph, prediction)['missing_fields'], [self.b])

    def test_false_alarm_and_recall_include_inconclusive_known_positive(self):
        d = self.result('all_sources_mask')
        positive = dict(decision_sha256=d.decision_sha256, is_failure=True, valid_test=True,
                        provenance='SYNTHETIC METRIC LABEL', artifact_sha256='a' * 64, independent=True)
        tp = replace(d, output_origin='actual_model', verdict=oracle.Verdict.CONFIRMED_VIOLATION, gold=positive)
        fp = replace(tp, decision_sha256='b' * 64, pair_id='b' * 64, verdict=oracle.Verdict.INCONCLUSIVE,
                     gold={**positive, 'is_failure': False})
        fn = replace(tp, decision_sha256='c' * 64, pair_id='c' * 64, verdict=oracle.Verdict.INCONCLUSIVE, alarm_issued=False)
        report = evaluator.summarize([tp, fp, fn], [], [])
        self.assertEqual(report['alarm_precision']['value'], .5)
        self.assertEqual(report['alarm_recall']['value'], .5)
        self.assertEqual(report['false_alarm_rate_valid_known_negatives']['value'], 1.)

    def test_budget_counts_begins_not_cache_or_rescoring(self):
        common = dict(output_origin='actual_model', reader_id='fixture-not-real-model', reader_fingerprint='a' * 64,
                      input_pixel_sha256='b' * 64, run_id='fresh')
        events = [dict(common, event='inference_begin', call_id='one'),
                  dict(common, event='inference_completed', call_id='one', elapsed_seconds=.5),
                  dict(common, event='cache_hit', call_id='one'),
                  dict(common, event='inference_begin', call_id='two'),
                  dict(common, event='inference_failed', call_id='two', elapsed_seconds=.2),
                  dict(common, event='inference_begin', call_id='ambiguous')]
        b = evaluator.budget(events, new_run_ids={'resume'})
        self.assertEqual((b['image_reader_invocations'], b['completed'], b['failed'], b['ambiguous']), (3, 1, 1, 1))
        self.assertEqual(b['new_image_reader_invocations'], 0)
        self.assertFalse(b['runtime_complete'])

    def test_no_label_is_not_zero_false_alarm_rate(self):
        d = replace(self.result('all_sources_mask'), output_origin='actual_model')
        report = evaluator.summarize([d], [], [])
        for metric in ('alarm_precision', 'alarm_recall', 'false_alarm_rate_valid_known_negatives'):
            self.assertIsNone(report[metric]['value'])
            self.assertEqual(report[metric]['denominator'], 0)
        self.assertEqual(report['unlabelled_alarms'], 1)
        self.assertEqual(report['alarm_label_coverage']['value'], 0)

    def test_unusable_output_counts_missed_reference_but_not_semantic_omission(self):
        prediction = replace(output({}, self.image, usable_text='{broken'), output_origin='actual_model')
        report = evaluator.summarize([], evaluator.observe_fields(self.graph, prediction), [])
        self.assertEqual(report['field_exact_match']['value'], 0)
        self.assertEqual(report['unusable_output_reference_fields'], 2)
        self.assertEqual(report['missing_supported_fields'], 0)
        self.assertIsNone(evaluator.missing_fields(self.graph, prediction)['missing_fields'])

    def test_invalid_alarm_counts_precision_burden_not_valid_negative_far(self):
        initial = replace(self.result('all_sources_mask'), output_origin='actual_model')
        gold = dict(is_failure=None, valid_test=False)
        d = replace(initial, gold=gold)
        report = evaluator.summarize([d], [], [])
        self.assertEqual(report['alarm_precision']['value'], 0.)
        self.assertEqual(report['alarm_precision']['denominator'], 1)
        self.assertEqual(report['invalid_test_alarm_rate']['value'], 1.)
        self.assertIsNone(report['false_alarm_rate_valid_known_negatives']['value'])

    def test_conflicting_duplicate_fields_are_not_silently_merged(self):
        prediction = replace(output(self.values, self.image), output_origin='actual_model')
        fields = evaluator.observe_fields(self.graph, prediction)
        with self.assertRaises(ValueError):
            evaluator.summarize([], fields + [replace(fields[0], exact_match=False)], [])


if __name__ == '__main__':
    unittest.main()
