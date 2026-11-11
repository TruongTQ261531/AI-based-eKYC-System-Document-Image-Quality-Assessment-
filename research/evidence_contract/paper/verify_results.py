"""Verify the development replication candidate using saved evidence, without model calls."""
from pathlib import Path
import argparse
import hashlib
import json
import sys


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def checksum(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def summary(root):
    decisions = read(root / "data/decisions.json")
    primary = [r for r in decisions if r["stratum"] == "primary"]
    controls = read(root / "data/controls.json")
    faulty = [r for r in controls if r["fault_installed"] and r["fault_activated"] and r["independently_faulty"]]
    structured = [r for r in faulty if r["error_types"] == ["FIELD"]]
    stages = read(root / "data/stages.json")
    result = dict(primary=len(primary),
                  A_B3_verdict_matches=sum(r["checks"]["A"]["verdict"] == r["checks"]["B3"]["verdict"] for r in primary),
                  A_flat_verdict_matches=sum(r["checks"]["A"]["verdict"] == r["checks"]["A_flat"]["verdict"] for r in primary),
                  A_alarms=sum(r["checks"]["A"]["alarm"] for r in primary),
                  B3_alarms=sum(r["checks"]["B3"]["alarm"] for r in primary),
                  A_exclusive=sum(r["checks"]["A"]["alarm"] and not r["checks"]["B3"]["alarm"] for r in primary),
                  controlled_cases=len(controls), controlled_observable_faults=len(faulty),
                  structured_faults=len(structured),
                  structured_detected={m: sum(c["methods"][m]["alarm"] for c in structured) for m in ("A", "B3")},
                  stage_f1={})
    for name in ("author", "raw", "rectified", "bad_crop"):
        views = [case["stages"][name]["end_to_end"] for case in stages]
        correct = sum(v["correct"] for v in views)
        denominator = sum(v["predicted"] + v["reference"] for v in views)
        result["stage_f1"][name] = [2 * correct, denominator]
    result["crop_correct_to_wrong"] = sum(
        f["before_correct"] and not f["after_correct"] for case in stages
        for f in case["contrasts"]["rectified_vs_bad_crop"]["fields"].values())
    return result


def oracle_replay(root):
    # The original A/B3 implementation is shipped under source/. Dependencies
    # are NumPy, Pillow and OpenCV. No reader, checkpoint or loader is present.
    sys.path.insert(0, str(root / "source"))
    from research.evidence_contract.normalized_output import NormalizedOutput
    from research.evidence_contract.source_graph import EvidenceGraph
    from research.evidence_contract.validity import Mutation, ValidationReport, Validity
    from research.evidence_contract.task5 import baselines

    def output(raw):
        record = dict(raw)
        record["predicted_fields"] = tuple(record["predicted_fields"])
        record["native_tokens"] = tuple(record["native_tokens"])
        return NormalizedOutput(**record)

    def validation(raw):
        # Schema adapter matching the frozen report serialization.
        mutation = dict(raw["mutation"])
        for key in ("hidden_source_ids", "output_size", "fill", "expected_source_state", "homography", "mask_geometry"):
            mutation[key] = tuple(mutation[key])
        return ValidationReport(Validity(raw["status"]), tuple(raw["reasons"]), raw["graph_sha256"],
            raw["mutation_sha256"], raw["before_pixel_sha256"], raw["after_pixel_sha256"], Mutation(**mutation),
            EvidenceGraph.from_dict(raw["after_graph"]) if raw["after_graph"] else None,
            raw["measurements"], tuple(raw.get("review_required", ())),
            EvidenceGraph.from_dict(raw["reference_before_graph"]) if raw.get("reference_before_graph") else None)

    methods = dict(A=baselines.proposed, B0=baselines.conventional, B2=baselines.b2,
                   B3=baselines.visible_reference, A_flat=baselines.flat_contract)
    checks = 0
    records = read(root / "data/oracle_cases.json")
    for record in records:
        graph = EvidenceGraph.from_dict(record["graph"])
        if graph.data_policy != "fictional" or graph.role not in ("fixture", "development"):
            raise ValueError("Bundle is limited to fictional development specimens")
        report = validation(record["validation"])
        before, after = output(record["before"]), output(record["after"])
        for name, function in methods.items():
            arguments = (report, before, after) if name == "B2" else (graph, report, before, after)
            if baselines.unpack(function(*arguments)) != record["checks"][name]:
                raise ValueError("Scorer replay differs from saved decision")
            checks += 1
    return dict(cases=len(records), verified_method_decisions=checks, model_calls=0)


def verify(root, *, replay=False):
    manifest = read(root / "MANIFEST.json")
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    if actual != set(manifest["files"]) | {"MANIFEST.json"}:
        raise ValueError("Missing or unexpected package files")
    for name, expected in manifest["files"].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or checksum(path) != expected:
            raise ValueError("Package file hash mismatch")
    result = summary(root)
    if result != read(root / "EXPECTED.json"):
        raise ValueError("Aggregate counts differ from evidence ledger")
    return dict(status="PASS", summary=result, oracle=oracle_replay(root) if replay else None, model_calls=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", action="store_true")
    options = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parent, replay=options.oracle), sort_keys=True))
