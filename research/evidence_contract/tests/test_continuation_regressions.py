"""Regression checks on fixtures and existing development receipts, without inference."""
from copy import deepcopy

import pytest

from research.evidence_contract.master import exposure, ifv_report, prelock, stage_analysis, statistics
from research.evidence_contract.master.intake import EXECUTION
from research.evidence_contract.normalized_output import ReaderSpec
from research.evidence_contract.task55.data import PILOT, digest, read, sha
from research.evidence_contract.tests.test_master_evidence import draft, specimen


def test_windows_file_aliases_are_one_specimen_path():
    one = specimen(image_relpath="Folder/View.png")
    another = specimen(uid="unit/2", image_relpath=r"folder\view.png")
    with pytest.raises(ValueError, match="duplicate image path"):
        exposure.validate_manifest(draft(one, another), {})


def test_one_identity_with_conflicting_full_author_content_blocks():
    one = specimen()
    another = specimen(uid="unit/2", image_relpath="other.png", content_sha256="d" * 64)
    result = exposure.validate_manifest(draft(one, another), {})
    assert result["status"] == "BLOCKED"
    assert any(r["reason"] == "conflicting_author_content_for_identity" for r in result["blockers"])


def test_content_key_collision_and_pixel_metadata_conflict_rejected():
    with pytest.raises(ValueError, match="normalized semantic"):
        exposure.content_fingerprint({"Name": "ONE", " name ": "TWO"})
    rows = [dict(input_sha256="a" * 64, pixel_sha256=p * 64) for p in ("b", "c")]
    with pytest.raises(ValueError, match="records conflict"):
        exposure.pixel_hash_index(rows)


def test_draft_binding_detects_change_and_missing_file(tmp_path):
    path = tmp_path / "evidence.json"
    path.write_text("fixture", encoding="utf-8")
    binding = {"evidence": dict(path=path.name, sha256=sha(path))}
    assert prelock.verify_bindings(binding, tmp_path)["status"] == "PASS"
    path.write_text("changed", encoding="utf-8")
    assert prelock.verify_bindings(binding, tmp_path)["files"]["evidence"] == "HASH_MISMATCH"
    binding["evidence"]["path"] = "missing.json"
    assert prelock.verify_bindings(binding, tmp_path)["files"]["evidence"] == "MISSING"
    binding["evidence"]["path"] = "../outside.json"
    with pytest.raises(ValueError, match="inside"):
        prelock.verify_bindings(binding, tmp_path)


@pytest.mark.parametrize("counter", [True, .5, float("nan")])
def test_cluster_counts_are_explicit_finite_integers(counter):
    with pytest.raises(ValueError, match="coherent counts"):
        statistics.paired_interval([("one", counter, 1, 0, 1)])


def test_precision_ci_needs_cluster_support_in_each_arm():
    records = [(str(i), int(i == 0), int(i == 0), 1, 1) for i in range(24)]
    result = statistics.paired_interval(records, draws=100)
    assert result["clusters"] == result["clusters_B"] == 24 and result["clusters_A"] == 1
    assert result["ci95"] is None and result["reason"] == "insufficient_independent_clusters"


def test_statistical_interfaces_reject_wrong_sampling_shapes():
    with pytest.raises(ValueError):
        statistics.paired_interval([("one", 0, 1, 0, 1)], draws=2.5)
    with pytest.raises(ValueError):
        statistics.sign_flip([[1, 2], [3, 4]], direction="greater")
    with pytest.raises(ValueError):
        statistics.holm_family({"primary": True})


def test_partial_phase1_keeps_entire_selected_frame_unreviewed():
    # Explicit in-memory unit controls. No human submission is created.
    checks = {method: dict(alarm=False, verdict="PASS") for method in ifv_report.METHODS}
    frame = {"frame": [dict(identity_sha256=f"unit-{i}", selected=True, row=dict(
        stratum="primary", checks=checks, contract_id="C1", physical_id_sha256=f"unit-id-{i}")) for i in range(3)]}
    links = ifv_report.sample_frame_links(frame, "unit-snapshot")
    one = next(iter(links))
    labels = {one: dict(pointwise="NO_FAULT", relation="NO_FAULT")}
    result = ifv_report.summarize(links, labels)["relation"]
    assert result["primary_cases"] == 3
    assert result["overall"]["A"]["status"]["UNREVIEWED"] == 2
    assert result["overall"]["A"]["labeled_cases"] == 1
    with pytest.raises(ValueError, match="outside"):
        ifv_report.summarize(links, {"unknown-case": labels[one]})


def test_saved_stage_content_digest_is_verified_before_replay():
    run = read(EXECUTION / "ab_execute.json")
    replay = read(EXECUTION / "ab_replay.json")
    for data in (run, replay):
        data["cases"][0]["stages"]["author"]["end_to_end"]["correct"] += 1
    with pytest.raises(ValueError, match="replay mismatch"):
        stage_analysis.compare(run, replay)


def test_stage_baselines_have_equal_source_information_on_saved_panel():
    run = read(EXECUTION / "ab_execute.json")
    result = stage_analysis.matched_stage_baselines(run)
    assert result["field_comparisons"] == result["explanation_agreement"] == 24
    assert result["degraded_fields"] == result["degraded_explanation_agreement"] == 4
    assert result["stage_diff_intervention_hits"]["value"] == result["graph_intervention_hits"]["value"] == 1
    assert result["natural_fault_localization_accuracy"] is None


def test_raw_stage_configuration_hash_matches_reader_spec():
    run = read(EXECUTION / "ab_execute.json")
    records = stage_analysis.raw_receipts(run)
    spec = ReaderSpec(**read(PILOT / "rapid_v4/rapid_v4.spec.json"))
    assert len(records) == 12
    assert {r["reader_config_sha256"] for r in records.values()} == {spec.config_sha256}
