"""Known-answer fixture tests. No OCR/VLM or confirmatory data is loaded."""
from dataclasses import replace
import hashlib
import json

import numpy as np
import pytest

from research.evidence_contract.contracts import Policy, RegressionEvidence, Status, assessment, evaluate
from research.evidence_contract.fixtures import (backup_fixture, development_fixtures, existing_renderer_development,
                                                multiline_fixture, shared_context_fixture)
from research.evidence_contract.generator import RESEARCH_ROOT, generate, plan, suite, write_new_run
from research.evidence_contract.source_graph import (Condition, EvidenceGraph, State, digest, from_hp_full,
                                                     from_label_record, from_v3_source, pixel_sha256)
from research.evidence_contract.validity import Mutation, ReviewEvidence, Validity, raster, validate_pair


@pytest.fixture(scope="module")
def backup():
    return backup_fixture()


def paired(fixture, kind, *, seed=42):
    image, graph, a, b = fixture
    return generate(image, graph, plan(graph, kind, target_key=a, retained_key=b if kind.startswith("pair_") else None, seed=seed))


def truth(graph):
    return {f.key: f.reference_value for f in graph.fields}


def change_sources(graph, key, function):
    return replace(graph, fields=tuple(replace(f, realizations=tuple(function(s) for s in f.realizations))
                                       if f.key == key else f for f in graph.fields))


def unknown_readability(source):
    return replace(source, components=tuple(replace(c, evidence_basis="geometry_only", readability="unassessed")
                                            for c in source.components))


def test_graph_or_and_and_round_trip(backup):
    image, graph, a, b = backup
    assert len(graph.field(a).realizations) == 3
    assert graph.field(a).state() == State.SUPPORTED
    restored = EvidenceGraph.from_dict(json.loads(json.dumps(graph.to_dict())))
    assert restored == graph and restored.sha256 == graph.sha256
    _, multi, address, _ = multiline_fixture()
    source = multi.field(address).realizations[0]
    changed = replace(source, components=(replace(source.components[0], availability="removed"), *source.components[1:]))
    assert changed.state() == State.REMOVED
    assert replace(source, components=tuple(replace(c, evidence_basis="geometry_only") for c in source.components)).state() == State.UNKNOWN


def test_single_mask_preserves_duplicate_and_mrz(backup):
    pair = paired(backup, "single_source_mask")
    assert pair.validation.status == Validity.VALID
    field = pair.validation.after_graph.field(backup[2])
    assert field.state() == State.SUPPORTED
    states = {s.kind: s.state() for s in field.realizations}
    assert states == {"body": State.REMOVED, "duplicated_body": State.SUPPORTED, "mrz": State.SUPPORTED}


@pytest.mark.parametrize("assertion, expected", [(False, Status.PASS), (True, Status.VIOLATION)])
def test_c1_complete_removal_known_answers(backup, assertion, expected):
    pair = paired(backup, "all_sources_mask")
    after = truth(backup[1]); after.pop(backup[2])
    if assertion:
        after[backup[2]] = backup[1].field(backup[2]).reference_value
    result = evaluate("C1", pair.graph, pair.validation, truth(pair.graph), after)
    assert result.status == expected
    assert result.diagnostics["unsupported_assertion"] is assertion
    assert not result.software_fault_confirmed


def test_c1_incomplete_annotation_cannot_pass_even_with_empty_output():
    pair = paired(backup_fixture(limited=True), "all_sources_mask")
    assert pair.validation.status == Validity.INCONCLUSIVE
    assert evaluate("C1", pair.graph, pair.validation, {}, {}).status == Status.INCONCLUSIVE


@pytest.mark.parametrize("prediction", ["{broken", "[]", '{"id_number":"a","id_number":"b"}', {"id_number": 123}])
def test_c1_malformed_output_is_not_empty_abstention(backup, prediction):
    pair = paired(backup, "all_sources_mask")
    assert evaluate("C1", pair.graph, pair.validation, {}, prediction).status == Status.INCONCLUSIVE


@pytest.mark.parametrize("value, reading, expected", [("DEMO12345", "correct", Status.PASS),
                                                     ("WRONG", "wrong", Status.VIOLATION),
                                                     (None, "omitted", Status.VIOLATION)])
def test_c2_backup_correctness_is_separate_from_absence(backup, value, reading, expected):
    pair = paired(backup, "single_source_mask")
    output = {} if value is None else {backup[2]: value}
    result = evaluate("C2", pair.graph, pair.validation, truth(pair.graph), output)
    assert result.status == expected and result.diagnostics["reading_status"] == reading
    assert not result.diagnostics["unsupported_assertion"]


def test_c2_optional_omission_has_explicit_policy_and_diagnostic(backup):
    pair = paired(backup, "single_source_mask")
    result = evaluate("C2", pair.graph, pair.validation, {}, {}, policy=Policy(require_supported_fields=False))
    assert result.status == Status.PASS and result.diagnostics["omission"]


def test_bad_mrz_checksum_cannot_be_valid_backup():
    fixture = backup_fixture(bad_checksum=True)
    source = fixture[1].source("mrz/a")
    assert not source.valid_conditions() and source.state() == State.UNKNOWN
    pair = paired(fixture, "single_source_mask")
    assert pair.validation.status == Validity.INCONCLUSIVE
    assert evaluate("C2", pair.graph, pair.validation, truth(pair.graph), truth(pair.graph)).status == Status.INCONCLUSIVE


@pytest.mark.parametrize("missing", ["field_checksum", "composite_checksum", "format_valid", "semantic_link"])
def test_mrz_requires_all_relevant_conditions(backup, missing):
    source = backup[1].source("mrz/a")
    source = replace(source, conditions=tuple(c for c in source.conditions if c.name != missing))
    assert source.state() == State.UNKNOWN


def test_mrz_checksum_policy_itself_cannot_be_unspecified(backup):
    assert replace(backup[1].source("mrz/a"), checksum_required=None).state() == State.UNKNOWN


def test_numeric_mrz_cannot_opt_out_of_required_field_checksum(backup):
    source = backup[1].source("mrz/a")
    source = replace(source, checksum_required=False,
                     conditions=tuple(c for c in source.conditions if c.name != "field_checksum"))
    assert source.state() == State.UNKNOWN


def test_date_precision_does_not_invent_a_century(backup):
    field = backup[1].field(backup[2])
    source = replace(field.realizations[0], reference_value="990101", value_kind="date_yymmdd")
    field = replace(field, reference_value="01/01/1999", value_kind="date_full", realizations=(source,))
    assert field.state() == State.SUPPORTED
    assert assessment({field.key: "01/01/1999"}, field) == "precision_overreach"
    assert assessment({field.key: "990101"}, field) == "correct"


def test_conflicting_sources_do_not_select_prediction_friendly_reference(backup):
    field = backup[1].field(backup[2])
    wrong = replace(field.realizations[1], reference_value="OTHER NUMBER")
    assert replace(field, realizations=(field.realizations[0], wrong)).state() == State.UNKNOWN


@pytest.mark.parametrize("bad", [False, True])
def test_c3_neighbor_behavior_failure_is_not_automatically_version_regression(backup, bad):
    pair = paired(backup, "pair_a_mask")
    output = truth(pair.graph)
    if bad:
        output[backup[3]] = "WRONG SCHOOL"
    result = evaluate("C3", pair.graph, pair.validation, truth(pair.graph), output)
    assert result.status == (Status.VIOLATION if bad else Status.PASS)
    assert not result.behavior_regression_verified and not result.software_fault_confirmed


def quad_for(pair, b, *, stable=True):
    original = truth(pair.graph)
    bad = dict(original); bad[b] = "WRONG SCHOOL"
    return RegressionEvidence(digest("old_version"), digest("new_version"), pair.validation.before_pixel_sha256,
                              pair.validation.after_pixel_sha256, original, original, original, bad,
                              stable, "fixture spec: retained school behavior unchanged")


def test_c3_bound_quad_verifies_only_behavior_regression(backup):
    pair = paired(backup, "pair_a_mask")
    quad = quad_for(pair, backup[3])
    result = evaluate("C3", pair.graph, pair.validation, quad.v1_original, quad.v1_followup, regression=quad)
    assert result.status == Status.VIOLATION and result.behavior_regression_verified
    assert not result.software_fault_confirmed


@pytest.mark.parametrize("change", ["unstable", "same_version", "wrong_hash", "old_already_wrong", "output_disagrees"])
def test_incomplete_quad_cannot_confirm_version_regression(backup, change):
    pair = paired(backup, "pair_a_mask"); quad = quad_for(pair, backup[3])
    if change == "unstable": quad = replace(quad, stability_verified=False)
    if change == "same_version": quad = replace(quad, version1_sha256=quad.version0_sha256)
    if change == "wrong_hash": quad = replace(quad, followup_pixel_sha256="0"*64)
    if change == "old_already_wrong": quad = replace(quad, v0_followup={})
    if change == "output_disagrees": quad = replace(quad, v1_followup={})
    output = truth(pair.graph); output[backup[3]] = "WRONG SCHOOL"
    result = evaluate("C3", pair.graph, pair.validation, truth(pair.graph), output, regression=quad)
    assert result.status == Status.VIOLATION and not result.behavior_regression_verified


def test_preexisting_neighbor_error_is_inconclusive(backup):
    pair = paired(backup, "pair_a_mask")
    assert evaluate("C3", pair.graph, pair.validation, {}, {}).status == Status.INCONCLUSIVE


def test_a_quality_unknown_does_not_hide_valid_retained_b_test(backup):
    image, graph, a, b = backup
    graph = change_sources(graph, a, unknown_readability)
    pair = paired((image, graph, a, b), "pair_a_mask")
    assert pair.validation.status == Validity.VALID
    assert evaluate("C3", graph, pair.validation, truth(graph), truth(graph)).status == Status.PASS


def test_b_unassessed_readability_cannot_confirm_regression(backup):
    image, graph, a, b = backup
    graph = change_sources(graph, b, unknown_readability)
    pair = paired((image, graph, a, b), "pair_a_mask")
    assert evaluate("C3", graph, pair.validation, truth(graph), {}).status == Status.INCONCLUSIVE


def test_b_context_loss_invalidates_even_unchanged_value_pixels():
    fixture = shared_context_fixture()
    pair = paired(fixture, "pair_a_mask")
    assert pair.validation.status == Validity.INVALID_TEST
    assert pair.validation.measurements["components"]["code/value"]["actual_changed_pixels"] == 0
    assert any("code/context" in r for r in pair.validation.reasons)
    assert evaluate("C3", pair.graph, pair.validation, truth(pair.graph), {}).status == Status.INVALID_TEST


@pytest.mark.parametrize("bad", [False, True])
def test_c4_exact_geometry_known_answers(backup, bad):
    pair = paired(backup, "geometry_translate")
    output = truth(pair.graph)
    if bad: output[backup[2]] = "WRONG"
    assert pair.validation.status == Validity.VALID
    result = evaluate("C4", pair.graph, pair.validation, truth(pair.graph), output)
    assert result.status == (Status.VIOLATION if bad else Status.PASS)
    assert not result.software_fault_confirmed


def test_c4_rotation_requires_an_explicit_sut_policy(backup):
    pair = paired(backup, "geometry_rotate90")
    assert pair.validation.status == Validity.VALID
    outputs = truth(pair.graph)
    assert evaluate("C4", pair.graph, pair.validation, outputs, outputs).status == Status.INCONCLUSIVE
    assert evaluate("C4", pair.graph, pair.validation, outputs, outputs,
                    policy=Policy(geometry_operators=("rotate90",))).status == Status.PASS


def test_c4_different_ocr_on_bad_original_is_not_regression(backup):
    pair = paired(backup, "geometry_translate")
    assert evaluate("C4", pair.graph, pair.validation, {}, truth(pair.graph)).status == Status.INCONCLUSIVE


def test_c4_geometry_only_reference_remains_inconclusive(backup):
    image, graph, a, b = backup
    graph = change_sources(graph, a, unknown_readability)
    pair = paired((image, graph, a, b), "geometry_translate")
    assert pair.validation.status == Validity.INCONCLUSIVE
    assert evaluate("C4", graph, pair.validation, truth(graph), truth(graph)).status == Status.INCONCLUSIVE


def test_actual_raster_mask_speck_cannot_leave_one_character_pixel(backup):
    pair = paired(backup, "all_sources_mask")
    altered = pair.followup.copy()
    component = pair.graph.source("body/a").components[0]
    ys, xs = np.where(raster(component.geometry, pair.graph.width, pair.graph.height))
    y, x = next((int(y), int(x)) for y, x in zip(ys, xs) if not np.array_equal(pair.original[y, x], pair.mutation.fill))
    altered[y, x] = pair.original[y, x]
    report = validate_pair(pair.original, altered, pair.graph, pair.mutation)
    assert report.status == Validity.INVALID_TEST
    assert any("target_characters_not_fully_removed" in r for r in report.reasons)


def test_partial_component_mask_invalidates_claimed_all_source_removal(backup):
    pair = paired(backup, "all_sources_mask")
    mutation = replace(pair.mutation, mask_geometry=pair.mutation.mask_geometry[:1])
    altered = generate(pair.original, pair.graph, mutation)
    assert altered.validation.status == Validity.INVALID_TEST


def test_pixel_tampering_outside_mask_is_not_ignored(backup):
    pair = paired(backup, "all_sources_mask")
    changed = pair.followup.copy(); changed[0, 0] = (0, 0, 0)
    report = validate_pair(pair.original, changed, pair.graph, pair.mutation)
    assert report.status == Validity.INVALID_TEST and report.measurements["changes_outside_mask"] == 1


def test_geometry_pixel_corruption_is_invalid_not_ocr_failure(backup):
    pair = paired(backup, "geometry_translate")
    changed = pair.followup.copy(); changed[0, 0] = (0, 0, 0)
    report = validate_pair(pair.original, changed, pair.graph, pair.mutation)
    assert report.status == Validity.INVALID_TEST


@pytest.mark.parametrize("matrix", [((0., 0., 0.),)*3,
                                     ((float("nan"), 0., 0.), (0., 1., 0.), (0., 0., 1.))])
def test_bad_homography_is_auditable_invalid_test(backup, matrix):
    image, graph, a, _ = backup
    mutation = Mutation("external", "C4", 42, a, homography=matrix,
                        output_size=(graph.width, graph.height), operator="external_warp")
    report = validate_pair(image, image, graph, mutation)
    assert report.status == Validity.INVALID_TEST
    json.dumps(report.to_dict(), allow_nan=False)


def test_interpolated_external_warp_is_not_automatically_invariant(backup):
    image, graph, a, _ = backup
    mutation = Mutation("external", "C4", 42, a, homography=((.99, 0., 1.), (0., .99, 1.), (0., 0., 1.)),
                        output_size=(graph.width, graph.height), operator="external_warp")
    report = validate_pair(image, image, graph, mutation)
    assert report.status == Validity.INCONCLUSIVE


def test_human_review_is_hash_bound_and_two_real_identities_required(backup):
    image, graph, a, b = backup
    graph = change_sources(graph, b, unknown_readability)
    pair = paired((image, graph, a, b), "pair_a_mask")
    source = graph.field(b).realizations[0]
    review = ReviewEvidence(pair.validation.before_pixel_sha256, pair.validation.after_pixel_sha256,
                            ("person1", "person1"), True, ((source.source_id, source.reference_value, source.reference_value),),
                            "unit-test simulated review; not an actual participant")
    assert validate_pair(image, pair.followup, graph, pair.mutation, review).status == Validity.INCONCLUSIVE
    review = replace(review, reviewer_ids=("person1", "person2"))
    verified = validate_pair(image, pair.followup, graph, pair.mutation, review)
    assert verified.status == Validity.VALID
    assert evaluate("C3", graph, verified, truth(graph), truth(graph)).status == Status.PASS
    assert validate_pair(image, pair.followup, graph, pair.mutation,
                         replace(review, after_pixel_sha256="0"*64)).status == Validity.INCONCLUSIVE


def test_generator_expectation_is_not_its_own_oracle(backup):
    pair = paired(backup, "all_sources_mask")
    mutation = replace(pair.mutation, expected_source_state=((backup[2], "SUPPORTED"),))
    report = validate_pair(pair.original, pair.followup, pair.graph, mutation)
    assert report.after_graph.field(backup[2]).state() == State.REMOVED


def test_wrong_graph_contract_or_binding_is_invalid(backup):
    pair = paired(backup, "all_sources_mask")
    assert evaluate("C2", pair.graph, pair.validation, {}, {}).status == Status.INVALID_TEST
    assert evaluate("C1", replace(pair.graph, physical_id="different"), pair.validation, {}, {}).status == Status.INVALID_TEST


def test_image_hash_mismatch_is_invalid(backup):
    pair = paired(backup, "all_sources_mask")
    original = pair.original.copy(); original[0, 0] = 0
    assert validate_pair(original, pair.followup, pair.graph, pair.mutation).status == Validity.INVALID_TEST


@pytest.mark.parametrize("role", ["train", "test", "confirmatory", "calibration"])
def test_generator_role_gate_blocks_confirmatory_before_transform(backup, role):
    image, graph, a, _ = backup
    with pytest.raises(ValueError, match="only"):
        plan(replace(graph, role=role), "full", target_key=a)


def test_no_positional_semantic_guess_for_native_fields(backup):
    image, _, _, _ = backup
    record = dict(uid="unmapped", physical_id="unmapped", role="development", source="specimen",
                  fields=[dict(raw_key="field01", semantic_key=None, polygon=((1, 1), (20, 1), (20, 20), (1, 20)),
                               reference_text="TEXT")])
    graph = from_label_record(record, image)
    assert not graph.fields and graph.unmapped_fields == ("field01",)


def test_v3_adapter_keeps_checksum_and_geometry_uncertainty(backup):
    from research.tests.test_v3_sources import specimen
    first, second = specimen()
    second = second[:9] + str((int(second[9])+1) % 10) + second[10:]
    q = ((10, 10), (450, 10), (450, 40), (10, 40))
    source = dict(physical_id="legacy-specimen", fields=[dict(author_key="number", value="DEMO12345", quad=q),
                  dict(author_key="mrz_line0", value=first, quad=q), dict(author_key="mrz_line1", value=second, quad=q)])
    graph = from_v3_source(source, backup[0])
    assert graph.field("id_number").coverage == "limited"
    assert graph.field("id_number").state() == State.UNKNOWN
    mrz = next(s for s in graph.field("id_number").realizations if s.kind == "mrz")
    assert not mrz.valid_conditions()
    assert any(c.name == "field_checksum" and c.satisfied is False for c in mrz.conditions)


def test_hp_adapter_preserves_label_as_semantic_context(backup):
    image, _, _, _ = backup
    full = dict(uid="hp-fixture", physical_id="hp-fixture", role="development", fields=[
        dict(key="explicit_key", value="A", quad=((30, 30), (60, 30), (60, 50), (30, 50)), label_box=(30, 10, 60, 25))])
    graph = from_hp_full(full, image)
    source = graph.field("explicit_key").realizations[0]
    assert [c.role for c in source.components] == ["value", "semantic_context"]
    assert source.state() == State.UNKNOWN


def test_suite_is_reproducible_and_original_is_immutable(backup):
    image, graph, a, b = backup
    original_hash = pixel_sha256(image)
    first = suite(image, graph, a, b, seed=42)
    second = suite(image, graph, a, b, seed=42)
    assert [p.metadata() for p in first] == [p.metadata() for p in second]
    assert pixel_sha256(image) == original_hash
    assert all(not p.original.flags.writeable and not p.followup.flags.writeable for p in first)


def test_run_write_hashes_and_refuses_overwrite_and_old_namespace(backup, tmp_path):
    pair = paired(backup, "all_sources_mask")
    destination = tmp_path / "new_run"
    manifest = write_new_run(destination, (pair,))
    row = manifest["cases"][0]
    assert hashlib.sha256((destination/row["followup_path"]).read_bytes()).hexdigest() == row["input_sha256"]
    assert hashlib.sha256((destination/row["original_path"]).read_bytes()).hexdigest() == row["original_input_sha256"]
    with pytest.raises(FileExistsError): write_new_run(destination, (pair,))
    with pytest.raises(ValueError, match="new child"): write_new_run(RESEARCH_ROOT.parent / "forbidden", (pair,))
    with pytest.raises(ValueError, match="policy"): write_new_run(tmp_path / "private", (
        replace(pair, graph=replace(pair.graph, data_policy="personal")),))
    assert not (tmp_path / "private").exists()


def test_existing_renderer_reused_without_build_or_old_data_writes(monkeypatch):
    from research import hp_data, labels_synth
    def forbid(*args, **kwargs):
        raise AssertionError("Completed dataset builder/writer was called")
    for module, names in ((hp_data, ("build", "write_capture", "write_capture", "preserve")),
                          (labels_synth, ("build", "save", "progress"))):
        for name in names: monkeypatch.setattr(module, name, forbid)
    image, graph, a, b = existing_renderer_development(0)
    pairs = suite(image, graph, a, b, seed=42)
    assert len(pairs) == 6 and graph.role == "development"
    with pytest.raises(ValueError, match="development"): existing_renderer_development(8)


def test_too_narrow_annotation_cannot_leave_unmasked_glyphs(backup):
    image, graph, a, b = backup
    def narrowed(source):
        if source.source_id != "body/a": return source
        component = source.components[0]
        q = np.asarray(component.geometry).copy()
        q[1:3, 0] = q[0, 0] + 2
        return replace(source, components=(replace(component, geometry=tuple(map(tuple, q))), *source.components[1:]))
    graph = change_sources(graph, a, narrowed)
    pair = paired((image, graph, a, b), "all_sources_mask")
    assert pair.validation.status == Validity.INVALID_TEST
    assert any("excludes_declared_glyph" in r for r in pair.validation.reasons)


def no_glyph_extent(source):
    return replace(source, components=tuple(replace(c, glyphs=(), evidence_basis="geometry_only")
                                            if c.role == "value" else c for c in source.components))


def test_full_bbox_coverage_alone_cannot_prove_all_characters_removed(backup):
    image, graph, a, b = backup
    graph = change_sources(graph, a, no_glyph_extent)
    pair = paired((image, graph, a, b), "all_sources_mask")
    assert pair.validation.status == Validity.INCONCLUSIVE
    assert "target_ink_extent_requires_independent_review" in pair.validation.reasons
    assert evaluate("C1", graph, pair.validation, {}, {}).status == Status.INCONCLUSIVE


def test_independent_hash_bound_removal_review_can_resolve_extent(backup):
    image, graph, a, b = backup
    graph = change_sources(graph, a, no_glyph_extent)
    pair = paired((image, graph, a, b), "all_sources_mask")
    review = ReviewEvidence(pair.validation.before_pixel_sha256, pair.validation.after_pixel_sha256,
                            ("person1", "person2"), True,
                            tuple((s.source_id, s.reference_value, "") for s in graph.field(a).realizations),
                            "simulated unit-test attestation; no real human labels collected", "removed")
    report = validate_pair(image, pair.followup, graph, pair.mutation, review)
    assert report.status == Validity.VALID
    assert evaluate("C1", graph, report, {}, {}).status == Status.PASS


def test_geometry_that_loses_a_source_is_invalid(backup):
    image, graph, a, _ = backup
    mutation = Mutation("cropped", "C4", 42, a,
                        homography=((1., 0., -800.), (0., 1., 0.), (0., 0., 1.)),
                        output_size=(graph.width, graph.height), operator="external_warp")
    assert validate_pair(image, image, graph, mutation).status == Validity.INVALID_TEST


def test_invalid_and_inconclusive_attempts_are_written_not_filtered(tmp_path):
    invalid = paired(shared_context_fixture(), "pair_a_mask")
    uncertain = paired(backup_fixture(limited=True), "all_sources_mask")
    manifest = write_new_run(tmp_path / "failed_preconditions", (invalid, uncertain))
    assert len(manifest["cases"]) == 2
    assert {r["validation"]["status"] for r in manifest["cases"]} == {"INVALID_TEST", "INCONCLUSIVE"}


def test_duplicate_case_ids_are_rejected_before_output_creation(backup, tmp_path):
    pair = paired(backup, "full")
    with pytest.raises(ValueError, match="Duplicate case IDs"):
        write_new_run(tmp_path / "duplicates", (pair, pair))
    assert not (tmp_path / "duplicates").exists()


def test_annotation_variants_keep_same_physical_identity(backup):
    limited = backup_fixture(limited=True)
    assert backup[1].physical_id == limited[1].physical_id
    assert pixel_sha256(backup[0]) == pixel_sha256(limited[0])
    assert backup[1].document_id != limited[1].document_id


def test_v3_adapter_does_not_default_unknown_source_to_development_or_public(backup):
    source = dict(physical_id="unassigned-source", fields=[])
    graph = from_v3_source(source, backup[0])
    assert graph.role == "unassigned" and graph.data_policy == "unknown"
    with pytest.raises(ValueError, match="relabel"):
        from_v3_source(dict(source, role="test"), backup[0], role="development")


def test_adapters_cannot_promote_personal_data_to_public_or_fictional(backup):
    source = dict(physical_id="private-source", fields=[], role="development", data_policy="personal")
    with pytest.raises(ValueError, match="relabel"):
        from_v3_source(source, backup[0], data_policy="public_specimen")
    record = dict(uid="private", physical_id="private", role="development", fields=[], data_policy="personal")
    with pytest.raises(ValueError, match="fictional"):
        from_label_record(record, backup[0], construction_scope="Cannot create a fictional attestation by naming it")
