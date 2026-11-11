from copy import deepcopy
import json

from PIL import Image
import numpy as np
import pytest

from research.evidence_contract.master import exposure, ifv_report, prelock, stage_analysis, statistics
from research.evidence_contract.master.intake import EC, EXECUTION, PRIVATE
from research.evidence_contract.source_graph import pixel_sha256
from research.evidence_contract.task55.data import read, sha


def specimen(**changes):
    return dict(dict(role="development", uid="unit/view", physical_id="unit/id", data_policy="fictional",
                     layout="unit layout", lineage="unit generator", image_relpath="view.png", rights_basis="unit fixture",
                     file_sha256="a" * 64, pixel_sha256="b" * 64, content_sha256="c" * 64,
                     reference_verified=True, provenance_verified=True), **changes)


def draft(*rows):
    return dict(schema="evidence-specimen-draft/1", state="DRAFT_ONLY", rows=list(rows))


def test_prospective_manifest_rejects_every_historical_overlap_axis():
    row = specimen()
    history = {axis: {row[axis]: ["historic"]} for axis in exposure.AXES}
    result = exposure.validate_manifest(draft(row), history, require_fixture=True)
    assert result["status"] == "BLOCKED"
    assert {reason["axis"] for reason in result["blockers"]} == set(exposure.AXES)
    assert not result["confirmatory_ready"]


def test_manifest_catches_pixel_duplicate_across_distinct_encodings_and_roles(tmp_path):
    pixels = np.full((64, 24, 3), 230, dtype=np.uint8)
    pixel = pixel_sha256(pixels)
    for name, compression in (("view1.png", 0), ("view2.png", 9)):
        Image.fromarray(pixels).save(tmp_path / name, compress_level=compression)
    a, b = (sha(tmp_path / path) for path in ("view1.png", "view2.png"))
    assert a != b
    one = specimen(image_relpath="view1.png", file_sha256=a, pixel_sha256=pixel)
    two = specimen(image_relpath="view2.png", file_sha256=b, pixel_sha256=pixel, physical_id="another",
                   uid="unit/other", role="prospective_confirmatory")
    pack = draft(one, two)
    exposure.verify_image_files(pack, tmp_path)
    result = exposure.validate_manifest(pack, {})
    assert any(r["axis"] == "pixel_sha256" and r["reason"] == "cross_role_or_identity_duplicate"
               for r in result["blockers"])
    two["pixel_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="decoded-pixel"):
        exposure.verify_image_files(pack, tmp_path)


@pytest.mark.parametrize("path", ["../away.png", r"D:\outside.png", r"c:escape.png"])
def test_manifest_rejects_path_escape(path):
    with pytest.raises(ValueError, match="path"):
        exposure.validate_manifest(draft(specimen(image_relpath=path)), {})


def test_content_hash_uses_normalized_full_author_values():
    assert exposure.content_fingerprint({"Name": " Unit  A "}) == exposure.content_fingerprint({"name": "unit A"})
    assert exposure.content_fingerprint({"name": "unit A"}) != exposure.content_fingerprint(
        {"name": "unit A", "code": "different"})


def test_prelock_refuses_actual_authorization_even_for_schema_valid_fixture():
    proposal = read(EC / "master/test_lock_draft.json")
    good = prelock.draft_preflight(proposal, specimen=draft(specimen()))
    assert good["manifest_check"]["status"] == "DRAFT_SCHEMA_PASS" and not good["confirmatory_executable"]
    with pytest.raises(ValueError, match="cannot authorize"):
        prelock.draft_preflight({**proposal, "allow_confirmatory_execution": True})
    with pytest.raises(ValueError, match="drafts only"):
        prelock.draft_preflight({**proposal, "state": "LOCKED"})


def test_sizing_illustration_serializes_as_assumptions_not_observations():
    result = prelock.sizing_illustration(draws=40)
    copy = json.loads(json.dumps(result, allow_nan=False))
    assert len(copy["rows"]) == 12
    assert copy["scope"].startswith("hypothetical") and not copy["includes_coverage_or_recall_guard"]
    assert all(row["rejection"]["denominator"] == 40 for row in copy["rows"])


def test_paired_interval_keeps_na_and_aggregates_by_id():
    assert statistics.paired_interval([])["reason"] == "zero_denominator"
    same_cluster = [("one", 1, 1, 0, 1)] * 500
    small = statistics.paired_interval(same_cluster)
    assert small["clusters"] == 1 and small["delta"] == 1 and small["ci95"] is None
    inputs = [(str(i), i % 2, 1, 0, 1) for i in range(24)]
    first = statistics.paired_interval(inputs, draws=600)
    assert first == statistics.paired_interval(inputs, draws=600)
    assert first["ci95"][0] < .5 < first["ci95"][1] and first["draws"] == 600


def test_exact_sign_flip_and_holm_include_unavailable_primary_slot():
    assert statistics.sign_flip([1] * 7, direction="greater") is None
    assert statistics.sign_flip([1] * 8, direction="greater") == 1 / 256
    assert statistics.sign_flip([1] * 8, direction="less") == 1
    assert statistics.holm_family({"rq1": .01, "rq2": None, "rq3": .04}) == {
        "rq1": .03, "rq2": None, "rq3": .08}


def test_ifv_reports_distinct_endpoints_with_invalid_and_omission_kept_visible():
    def link(a, b, a_decision="PASS"):
        checks = {m: dict(alarm=b, verdict="CANDIDATE_VIOLATION" if b else "PASS") for m in ifv_report.METHODS}
        checks["A"] = dict(alarm=a, verdict=a_decision)
        return {"row": dict(checks=checks, stratum="primary", contract_id="C3", physical_id_sha256="same_cluster")}

    links = {"regression": link(True, True, "CANDIDATE_VIOLATION"),
             "already_wrong": link(False, True, "INCONCLUSIVE"), "invalid": link(False, True),
             "unknown": link(False, False), "review_not_returned": link(False, False)}
    labels = {
        "regression": dict(pointwise="CONFIRMED_FAULT", relation="CONFIRMED_FAULT"),
        "already_wrong": dict(pointwise="CONFIRMED_FAULT", relation="INCONCLUSIVE"),
        "invalid": dict(pointwise="INVALID_TEST", relation="INVALID_TEST"),
        "unknown": dict(pointwise="INCONCLUSIVE", relation="INCONCLUSIVE"),
    }
    report = ifv_report.summarize(links, labels)
    field = report["pointwise"]["overall"]
    pair = report["relation"]["overall"]
    assert field["A"]["confusion"]["FN"] == 1 and field["B3"]["confusion"]["TP"] == 2
    assert pair["A"]["confusion"]["FN"] == 0 and pair["B3"]["confusion"]["FP"] == 0
    assert pair["B3"]["invalid_alarm_rate"]["value"] == 1 and pair["B3"]["status"]["UNREVIEWED"] == 1
    assert field["A"]["false_alarm_rate_on_reviewed"]["value"] is None
    assert report["pointwise"]["paired_A_minus_B3"]["sensitivity"]["clusters"] == 1
    assert field["A"]["population_recall"] is None
    markdown = ifv_report.format_report(dict(reviewed_cases=4, cases_selected=5, results=report))
    assert "One-person pilot" in markdown and "Pointwise endpoint" in markdown and " NA " in markdown


def test_ifv_rejects_unsealed_paths_before_reading_text(tmp_path):
    with pytest.raises(ValueError, match="sealed copy"):
        ifv_report.sealed_results(tmp_path / "output_observations.json")


def test_latest_exposure_ledger_includes_development_interventions():
    report = read(EXECUTION / "exposure_audit_final.json")
    assert report["index_sha256"] == sha(PRIVATE / "exposure_index_final.json")
    assert report["sources"]["master/M2-M3"]["coverage"]["pixel_sha256"] == 12
    assert "master/M1-M7" in report["sources"]
    assert report["model_pretraining_exposure"] == "unknown"


def test_activated_controlled_faults_stay_separate_from_real_errors():
    values = read(EXECUTION / "controlled_faults.json")
    assert values["records"] == 14 and values["independently_faulty"] == 7
    assert values["results"]["A"]["structured_field_mutation_score"]["numerator"] == 5
    assert values["results"]["A"] == values["results"]["B3"]
    assert values["human_labels"] == values["natural_model_errors"] == 0
    assert values["results"]["JSON_SCHEMA"]["detected_families"] == ["M7"]
    assert values["results"]["FLAT_ATTRIBUTION"]["detected_families"] == ["M6"]


def test_verified_stage_replay_separates_geometry_loss_and_original_error():
    run, replay = (read(EXECUTION / ("ab_" + label + ".json")) for label in ("execute", "replay"))
    report = stage_analysis.compare(run, replay)
    assert report["targeted_geometry_loss"] == 3 and report["targeted_correct_before_crop"] == 0
    crop = report["contrasts"]["rectified_vs_bad_crop"]
    assert crop["pointwise_correct_to_wrong"] == crop["source_loss_on_degraded_fields"] == 4
    assert crop["c4_retained_regression_candidates"] == 0 and report["replay_model_calls"] == 0
    corrupted = deepcopy(replay)
    corrupted["content_digest"] = ""
    with pytest.raises(ValueError, match="replay mismatch"):
        stage_analysis.compare(run, corrupted)
