"""Offline comparison of the bounded M2 stage pilot and its matched controls."""
from collections import Counter
import json

from ..normalized_output import NativeOutput, ReaderSpec
from ..task55.data import EC, PILOT, digest, log_events, read, save_new, sha
from .intake import EXECUTION, PRIVATE
from .statistics import rate


def raw_receipts(report):
    local = PRIVATE / "stage_pilot"
    reader = report["reader"]
    inputs = {r["pixel_sha256"]: r for r in read(local / "inputs.json")}
    reader_fingerprint = read(PILOT / reader / (reader + ".spec.json"))
    fingerprint = ReaderSpec(**reader_fingerprint).fingerprint
    stores = (local / reader, PILOT / reader, EC / "local/smoke_02" / reader)
    completions = {store: log_events(store / "events.jsonl") for store in stores}
    bindings = {}
    for row in report["provenance"]:
        pixel, call = row["pixel"], row["call_id"]
        req = inputs[pixel]
        key = digest(dict(schema="raw-reader-cache/1", reader=fingerprint, input_file_sha256=req["file_sha256"],
                          input_pixel_sha256=pixel))
        for store in stores:
            path = store / "raw" / (key + ".json")
            if not path.is_file():
                continue
            envelope = read(path)
            data = envelope["payload"]
            if data["call_id"] != call:
                continue
            if (digest(data) != envelope["payload_sha256"] or data["cache_key"] != key
                    or data["input_pixel_sha256"] != pixel or data["input_file_sha256"] != req["file_sha256"]
                    or data["reader_spec"] != reader_fingerprint or sum(
                        e["event"] in ("inference_completed", "inference_recovered") and e.get("call_id") == call
                        and e.get("payload_sha256") == envelope["payload_sha256"] for e in completions[store]) != 1):
                raise ValueError("Changed or incomplete raw reader binding")
            native = NativeOutput.from_dict(data["native"])
            bindings[call] = dict(input_pixel=pixel, native_output_sha256=digest(native.text),
                                  native_payload_sha256=envelope["payload_sha256"],
                                  reader_config_sha256=ReaderSpec(**data["reader_spec"]).config_sha256,
                                  native_metadata_keys=sorted(native.runtime))
            break
        else:
            raise ValueError("Missing bound raw stage output")
    return bindings


def compare(run, replay):
    if (any(report["content_digest"] != digest(report["cases"]) for report in (run, replay))
            or run["content_digest"] != replay["content_digest"] or run["cases"] != replay["cases"] or replay["model_calls"]):
        raise ValueError("Stage score replay mismatch")
    result = {}
    for pair in ("raw_vs_rectified", "rectified_vs_bad_crop"):
        documents = [c["contrasts"][pair] for c in run["cases"]]
        degraded = [f for d in documents for f in d["fields"].values() if f["before_correct"] and not f["after_correct"]]
        result[pair] = dict(clusters=len(documents), aggregate_f1_decline_cases=sum(d["f1_only_delta"] < 0 for d in documents),
                            pointwise_correct_to_wrong=len(degraded),
                            pointwise_wrong_to_correct=sum(d["fields_wrong_to_correct"] for d in documents),
                            earliest_m2_boundary_cases=sum(d["first_observed_boundary"] == "M2_pixels" for d in documents),
                            source_loss_on_degraded_fields=sum(f["all_declared_sources_lost"] for f in degraded),
                            retained_source_degraded_fields=sum(f["retained_source"] for f in degraded),
                            c4_retained_regression_candidates=sum(f["retained_source"] for f in degraded),
                            c4_operator_policy="projective interpolation outside the frozen validated C4 operator panel")
    pooled = {}
    for name in ("author", "raw", "rectified", "bad_crop"):
        views = [c["stages"][name]["end_to_end"] for c in run["cases"]]
        counts = {k: sum(r[k] for r in views) for k in ("correct", "predicted", "reference")}
        pooled[name] = dict(**counts, field_f1=rate(2 * counts["correct"], counts["predicted"] + counts["reference"]))
    return dict(scope="exploratory development only", provenance=dict(Counter(r["origin"] for r in run["provenance"])),
                contrasts=result, pooled=pooled,
                targeted_geometry_loss=sum(c["contrasts"]["rectified_vs_bad_crop"]["fields"][c["target"]]
                                          ["all_declared_sources_lost"] for c in run["cases"]),
                targeted_correct_before_crop=sum(c["contrasts"]["rectified_vs_bad_crop"]["fields"][c["target"]]
                                                 ["before_correct"] for c in run["cases"]),
                baseline_scope="same predictions and authored evidence; strong B3 on controlled mutations, visible-reference comparator on projective variants",
                replay_exact=True, fresh_actual_calls=run["model_calls"], replay_model_calls=replay["model_calls"],
                model_calls=0, software_root_causes_verified=0)


def matched_stage_baselines(run):
    """Complete the planned flat-source and stage-diff comparisons from saved traces."""
    if run["content_digest"] != digest(run["cases"]):
        raise ValueError("Stage content digest mismatch")
    rows = []

    def flat_state(field):
        statuses = [source["status"] for source in field["sources"].values()]
        if "retained" in statuses:
            return "retained"
        if statuses and all(value == "clipped" for value in statuses) and field["scope"] == "complete":
            return "clipped"
        return "uncertain"

    for case in run["cases"]:
        for name, contrast in case["contrasts"].items():
            before, after = name.split("_vs_")
            left, right = case["stages"][before], case["stages"][after]
            for key, field in contrast["fields"].items():
                previous = flat_state(left["geometric_source_state"][key])
                current = flat_state(right["geometric_source_state"][key])
                flat = ("geometry_loss_at_M2" if previous == "retained" and current == "clipped" else
                        "source_retained_error_stage_unresolved" if current == "retained" and not field["after_correct"]
                        else "undetermined_or_no_new_error")
                rows.append(dict(cluster=case["cluster"], contrast=name, field=key,
                                 graph_explanation=field["explanation"], flat_explanation=flat,
                                 pointwise_regression=field["before_correct"] and not field["after_correct"]))
    crops = [case["contrasts"]["rectified_vs_bad_crop"] for case in run["cases"]]
    return dict(scope="same saved development traces and source metadata",
                field_comparisons=len(rows), explanation_agreement=sum(
                    r["graph_explanation"] == r["flat_explanation"] for r in rows),
                degraded_fields=sum(r["pointwise_regression"] for r in rows),
                degraded_explanation_agreement=sum(r["pointwise_regression"] and
                    r["graph_explanation"] == r["flat_explanation"] for r in rows),
                crop_site_ground_truth="M2, from the predeclared supplied-corner intervention",
                stage_diff_intervention_hits=rate(sum(c["first_observed_boundary"] == "M2_pixels" for c in crops), len(crops)),
                graph_intervention_hits=rate(sum(any(
                    f["all_declared_sources_lost"] for f in c["fields"].values()) for c in crops), len(crops)),
                natural_fault_localization_accuracy=None, human_ground_truth_used=False, model_calls=0, rows=rows)


if __name__ == "__main__":
    original = EXECUTION / "ab_execute.json"
    replay = EXECUTION / "ab_replay.json"
    run = read(original)
    result = compare(run, read(replay))
    bindings = raw_receipts(run)
    save_new(EXECUTION / "ab_stage_comparison.json", dict(**result, raw_bindings=bindings,
              execution_sha256=sha(original), replay_sha256=sha(replay)))
    print(json.dumps(result), flush=True)
