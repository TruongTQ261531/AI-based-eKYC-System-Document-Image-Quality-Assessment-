"""Bounded fixture/development generation audit, with zero model calls.

Execution requires --run and a new output directory. Constructed output packs
exercise the contracts; they are never presented as OCR/VLM predictions.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import time

import numpy as np
from PIL import Image

from .contracts import Status, evaluate
from .fixtures import development_fixtures
from .generator import RESEARCH_ROOT, generate, plan, write_new_run
from .source_graph import State, pixel_sha256

SEEDS = (42, 31415, 20261106)
FAMILIES = ("full", "single_source_mask", "all_sources_mask", "pair_a_mask", "pair_b_mask",
            "geometry_translate", "geometry_rotate90")


def _sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _save(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n")


def artifact_audit(destination):
    """Replay saved bytes, graph/source states and rates without neural inference."""
    destination = Path(destination)
    checks, cases = [], []
    for manifest_path in sorted(destination.glob("seed_*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in manifest["cases"]:
            folder = manifest_path.parent
            for file_key, byte_key, pixel_key in (("original_path", "original_input_sha256", "original_pixel_sha256"),
                                                   ("followup_path", "input_sha256", "input_pixel_sha256")):
                path = (folder / row[file_key]).resolve()
                if not path.is_relative_to(folder.resolve()):
                    raise ValueError("Artifact path escape")
                with Image.open(path) as image:
                    pixels = np.asarray(image.convert("RGB"))
                checks.append(dict(case_id=row["case_id"], file=file_key,
                                   bytes_match=_sha(path) == row[byte_key],
                                   pixels_match=pixel_sha256(pixels) == row[pixel_key]))
            case = json.loads((folder / row["case_id"] / "case.json").read_text(encoding="utf-8"))
            if case != row:
                raise ValueError("Case JSON differs from manifest")
            cases.append(row)
    return dict(images_checked=len(checks), cases_checked=len(cases),
                byte_or_pixel_mismatches=sum(not c["bytes_match"] or not c["pixels_match"] for c in checks),
                checks=checks)


def run(destination, *, seeds=SEEDS):
    destination = Path(destination).resolve()
    if not destination.is_relative_to(RESEARCH_ROOT.resolve()) or destination == RESEARCH_ROOT.resolve():
        raise ValueError("Pilot output must stay within the new research namespace")
    if not seeds or len(seeds) > 3 or len(set(seeds)) != len(seeds):
        raise ValueError("Pilot allows one to three distinct generation seeds")
    destination.mkdir(parents=True, exist_ok=False)
    root = RESEARCH_ROOT.parents[1]
    paths = [RESEARCH_ROOT / name for name in ("source_graph.py", "validity.py", "contracts.py", "generator.py", "fixtures.py", "pilot.py")]
    paths += [root / "research" / name for name in ("v3_sources.py", "hp_data.py", "labels_synth.py", "labels_schema.py")]
    start = dict(started_utc=datetime.now(timezone.utc).isoformat(), seeds=list(seeds),
                 code_sha256={p.relative_to(root).as_posix(): _sha(p) for p in paths},
                 python=platform.python_version(), packages={name: importlib.metadata.version(name)
                     for name in ("numpy", "Pillow", "opencv-python-headless", "pytest")},
                 mode="fixture/development generation; constructed control outputs only",
                 model_calls=0, training_steps=0, confirmatory_inputs_opened=0)
    _save(destination / "start.json", start)
    fixtures = development_fixtures()
    inputs_before = {graph.document_id: pixel_sha256(image) for image, graph, _, _ in fixtures}
    attempts, controls = [], []
    artifacts_written = 0
    for seed in seeds:
        pairs = []
        for image, graph, a, b in fixtures:
            for family in FAMILIES:
                target, retained = (b, a) if family == "pair_b_mask" else (b, None) if family in (
                    "geometry_translate", "geometry_rotate90") else (a, b) if family == "pair_a_mask" else (a, None)
                begun = time.perf_counter()
                attempt = dict(document_id=graph.document_id, physical_id=graph.physical_id,
                               role=graph.role, seed=seed, family=family, contract_id="UNRESOLVED",
                               validity="GENERATION_ERROR", reasons=[], review_required=[])
                attempts.append(attempt)
                try:
                    mutation = plan(graph, family, target_key=target, retained_key=retained, seed=seed)
                    pair = generate(image, graph, mutation)
                    pairs.append(pair)
                    attempt.update(case_id=pair.case_id, contract_id=mutation.contract_id,
                                   validity=pair.validation.status.value, reasons=list(pair.validation.reasons),
                                   review_required=list(pair.validation.review_required))
                    # Explicitly fabricated correct/wrong responses: controls, NOT model observations.
                    before = {f.key: f.reference_value for f in graph.fields}
                    good = {f.key: f.reference_value for f in pair.validation.after_graph.fields
                            if f.state() == State.SUPPORTED} if pair.validation.after_graph else {}
                    tested_key = retained if mutation.contract_id == "C3" else target
                    bad = dict(good)
                    bad[tested_key] = graph.field(tested_key).reference_value if mutation.contract_id == "C1" else "INTENTIONALLY WRONG CONTROL"
                    positive = evaluate(mutation.contract_id, graph, pair.validation, before, good)
                    negative = evaluate(mutation.contract_id, graph, pair.validation, before, bad)
                    controls.append(dict(case_id=pair.case_id, contract_id=mutation.contract_id,
                                         kind="constructed_output_controls_not_model_predictions",
                                         before_output=before, correct_output_pack=good, incorrect_output_pack=bad,
                                         correct_pack_verdict=positive.to_dict(), incorrect_pack_verdict=negative.to_dict()))
                except Exception as exc:
                    attempt.update(validity="GENERATION_ERROR", reasons=[type(exc).__name__ + ":" + str(exc)])
                attempt["wall_seconds"] = time.perf_counter()-begun
        write_new_run(destination / f"seed_{seed}", pairs,
                      run_metadata=dict(seed=seed, planned_attempts=len(fixtures)*len(FAMILIES),
                                        invalid_and_inconclusive_pairs_retained=True))
        artifacts_written += len(pairs)
    inputs_after = {graph.document_id: pixel_sha256(image) for image, graph, _, _ in fixtures}
    _save(destination / "attempts.json", attempts)
    _save(destination / "constructed_controls.json", controls)
    groups = {}
    for contract in ("C1", "C2", "C3", "C4"):
        selected = [a for a in attempts if a["contract_id"] == contract]
        counts = Counter(a["validity"] for a in selected)
        corresponding = [c for c in controls if c["contract_id"] == contract]
        decisions = sum(c["correct_pack_verdict"]["status"] in ("PASS", "VIOLATION") for c in corresponding)
        groups[contract] = dict(attempts=len(selected), validity_counts=dict(counts),
                                validity_yield=counts["VALID"]/len(selected) if selected else None,
                                constructed_control_decisions=decisions,
                                contract_decision_coverage=decisions/len(selected) if selected else None,
                                correct_pack_verdict_counts=dict(Counter(c["correct_pack_verdict"]["status"] for c in corresponding)),
                                incorrect_pack_verdict_counts=dict(Counter(c["incorrect_pack_verdict"]["status"] for c in corresponding)))
    counts = Counter(a["validity"] for a in attempts)
    transformed = [a for a in attempts if a["family"] != "full"]
    transformed_valid = sum(a["validity"] == "VALID" for a in transformed)
    audit = artifact_audit(destination)
    _save(destination / "artifact_audit.json", audit)
    report = dict(started_utc=start["started_utc"], ended_utc=datetime.now(timezone.utc).isoformat(),
                  scope="Fixture/development pilot, not a model benchmark or RQ significance test",
                  seeds=list(seeds), planned_attempts=len(fixtures)*len(FAMILIES)*len(seeds),
                  ledger_attempts=len(attempts), artifacts_written=artifacts_written,
                  constructed_control_packs=len(controls),
                  validity_counts=dict(counts), generation_yield=counts["VALID"]/len(attempts),
                  invalid_test_rate=counts["INVALID_TEST"]/len(attempts),
                  inconclusive_rate=counts["INCONCLUSIVE"]/len(attempts),
                  transformed_attempts_excluding_full=len(transformed),
                  transformed_validity_yield=transformed_valid/len(transformed),
                  graph_instances=len(fixtures), physical_ids=len(set(g.physical_id for _, g, _, _ in fixtures)),
                  unique_original_rasters=len(set(inputs_before.values())),
                  roles=dict(Counter(g.role for _, g, _, _ in fixtures)),
                  by_contract=groups, by_family={f: dict(Counter(a["validity"] for a in attempts if a["family"] == f)) for f in FAMILIES},
                  source_inputs_byte_unchanged=inputs_before == inputs_after,
                  artifact_audit=dict(images_checked=audit["images_checked"], cases_checked=audit["cases_checked"],
                                      mismatches=audit["byte_or_pixel_mismatches"]),
                  review_queue_attempts=sum(bool(a["review_required"]) for a in attempts),
                  neural_model_calls=0, training_steps=0, new_human_reviews=0, confirmatory_inputs_opened=0,
                  limitations=["Construction support is not human readability", "Repeated seeds/annotation variants are not independent identities",
                               "Control predictions are deliberately authored, not OCR outputs", "Natural image and fault recall claims not tested"])
    _save(destination / "report.json", report)
    if (inputs_before != inputs_after or audit["byte_or_pixel_mismatches"] or counts["GENERATION_ERROR"]
            or len(attempts) != report["planned_attempts"] or artifacts_written != len(controls)):
        raise RuntimeError("Pilot integrity/generation errors recorded; inspect the retained ledger")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.run:
        print(json.dumps(dict(action="dry_run", seeds=SEEDS, fixtures=8, families=FAMILIES,
                              planned_pairs=8*len(FAMILIES)*len(SEEDS), model_calls=0)))
        return
    if args.output is None:
        parser.error("--run requires --output pointing to a new directory")
    report = run(args.output)
    compact = {k: report[k] for k in ("planned_attempts", "ledger_attempts", "validity_counts", "generation_yield",
                                     "invalid_test_rate", "inconclusive_rate", "physical_ids", "unique_original_rasters",
                                     "by_contract", "artifact_audit", "neural_model_calls", "training_steps")}
    print(json.dumps(compact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
