"""Read-only delivery audit; no predictor is constructed or invoked."""
import ast
from dataclasses import asdict
import json
from pathlib import Path
import re
import subprocess

from research.evidence_contract.normalized_output import NativeOutput, ReaderSpec
from research.evidence_contract.runner import EventLog, InputRequest, Runner, sha_file, write_once
from research.evidence_contract.source_graph import digest

OUT = Path(__file__).resolve().parent
EC = OUT.parents[1]
ROOT = EC.parents[1]
PUBLIC = OUT / "smoke_02"
LOCAL = EC / "local/smoke_02"
READERS = ("rapid_v4", "rapid_latin_v5", "partial_42")

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

tests = read(OUT / "pytest_run_06.execution.json")
assert tests["exit_code"] == tests["failures"] == tests["errors"] == tests["skipped"] == 0
assert tests["tests"] == 152 and tests["actual_model_invocations"] == 0
assert tests["code_unchanged_during_tests"]
for name, expected in tests["code_sha256"].items():
    assert sha_file(ROOT / name) == expected, ("code_changed_after_tests", name)
for path in EC.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
schema = read(EC / "normalized_output.schema.json")
assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

preservation = read(OUT / "preservation_final.json")
assert not preservation["changed_preexisting_paths"]
assert preservation["head_and_refs_unchanged"] and not preservation["tracked_diff"] and not preservation["staged_diff"]
assert preservation["checked_preexisting_files"] == 2523
prep = read(PUBLIC / "preparation.json")
assert sha_file(LOCAL / "inputs.json") == prep["inputs_manifest_sha256"]
assert sha_file(LOCAL / "scoring.json") == prep["scoring_manifest_sha256"]
inputs = [InputRequest(**r) for r in read(LOCAL / "inputs.json")["inputs"]]
for request in inputs:
    request.load()  # Verify all four original pixels. No inference.
assert len(inputs) == 4 and prep["physical_ids"] == 1 and prep["generated_pairs"] == 4
assert all(row["validity"] == "VALID" for row in prep["contract_validity"])

events_public, reader_checks = {}, []
total_begins = total_raw = 0
inference_core = {p.relative_to(ROOT).as_posix(): sha_file(p) for p in (ROOT / "research").glob("*.py")}
for p in (ROOT / "ekyc").rglob("*.py"):
    inference_core[p.relative_to(ROOT).as_posix()] = sha_file(p)
inference_core["reader_adapters.py"] = sha_file(EC / "reader_adapters.py")
inference_core["runner.py"] = sha_file(EC / "runner.py")
identity_keys = ("cache_key", "call_id", "reader_fingerprint", "model_sha256", "config_sha256",
                 "inference_code_sha256", "runtime_sha256", "input_file_sha256", "input_pixel_sha256",
                 "latency_seconds", "cpu_seconds", "output_origin")
for reader in READERS:
    fresh, resume, replay = [read(PUBLIC / (mode + "_" + reader + ".json")) for mode in ("fresh", "resume", "replay")]
    assert (fresh["new_inference_calls"], resume["new_inference_calls"], replay["new_inference_calls"]) == (4, 0, 0)
    assert (fresh["model_loads"], resume["model_loads"], replay["model_loads"]) == (1, 0, 0)
    assert fresh["reader"] == resume["reader"] == replay["reader"]
    baseline_rows = {o["input_pixel_sha256"]: o for o in fresh["outputs"]}
    assert set(baseline_rows) == {r.pixel_sha256 for r in inputs}
    for mode in (resume, replay):
        for row in mode["outputs"]:
            assert all(row[k] == baseline_rows[row["input_pixel_sha256"]][k] for k in identity_keys)
    spec = ReaderSpec(**fresh["reader"])
    closure = dict(inference_core)
    if reader == "partial_42":
        for p in (ROOT / "research/cache/vlm_lora_v1/model").glob("*.py"):
            closure["reviewed_model/" + p.name] = sha_file(p)
    assert digest(closure) == spec.inference_code_sha256
    runner = Runner(spec, LOCAL / reader)  # No loader, and infer() is not called.
    rows = runner.events.read()
    starts = [r for r in rows if r["event"] == "inference_begin"]
    complete = [r for r in rows if r["event"] == "inference_completed"]
    assert len(starts) == len(complete) == 4
    assert len(rows) == 14 and all(r["output_origin"] == "actual_model" for r in rows)
    assert not any(r["event"] in ("inference_failed", "inference_recovered") for r in rows)
    assert sha_file(runner.events.path) == resume["event_log_sha256"] == replay["event_log_sha256"]
    assert replay["event_count_before"] == replay["event_count_after"] == 14
    caches = list((runner.store / "raw").glob("*.json"))
    assert len(caches) == 4
    cached_ids = set()
    for cache in caches:
        envelope = read(cache)
        payload = envelope["payload"]
        assert envelope["payload_sha256"] == digest(payload)
        assert payload["reader_spec"] == spec.to_dict()
        native = NativeOutput.from_dict(payload["native"])
        request = next(r for r in inputs if r.pixel_sha256 == payload["input_pixel_sha256"])
        assert payload["cache_key"] == cache.stem == runner.key(request)
        assert payload["input_file_sha256"] == request.file_sha256
        cached_ids.add(payload["call_id"])
    assert cached_ids == {r["call_id"] for r in starts} == {r["call_id"] for r in complete}
    events_public[reader] = dict(log_sha256=sha_file(runner.events.path), events=rows)
    reader_checks.append(dict(reader=reader, raw_records=len(caches), actual_calls=4,
                              resume_new_calls=0, replay_new_calls=0, replay_model_loads=0,
                              inference_code_matches_fresh=True, cache_payload_bindings_valid=True,
                              replay_event_log_unchanged=True))
    total_begins += len(starts)
    total_raw += len(caches)
assert total_begins == total_raw == 12
assert not list((EC / "local/smoke_01").rglob("events.jsonl"))

final, replayed = PUBLIC / "evaluation_final.json", PUBLIC / "evaluation_replayed.json"
assert final.read_bytes() == replayed.read_bytes()
evaluation = read(final)
assert evaluation["verdict_counts"] == dict(PASS=5, CANDIDATE_VIOLATION=3, INCONCLUSIVE=4)
assert evaluation["verified_failure_count"] == evaluation["confirmed_software_defects"] == 0
assert evaluation["budget"]["image_reader_invocations"] == 12
assert evaluation["budget"]["new_image_reader_invocations"] == evaluation["new_actual_model_invocations_during_scoring"] == 0
assert evaluation["budget"]["failed"] == evaluation["budget"]["ambiguous"] == 0
assert evaluation["unit_counts"] == dict(generated_pairs=4, physical_ids=1, unique_field_reader_views=24,
                                         unique_image_reader_views=12, unique_pixel_images=4)
for name in ("alarm_precision", "alarm_recall", "false_alarm_rate_valid_known_negatives"):
    assert evaluation[name]["value"] is None and evaluation[name]["denominator"] == 0
for name, expected in evaluation["scorer_code_sha256"].items():
    assert sha_file(EC / name) == expected
for decision in evaluation["decisions"]:
    assert decision["gold"] is None and not decision["evidence_certificate_accepted"]
assert set(evaluation["event_log_sha256"]) == set(events_public)
for reader, row in events_public.items():
    assert evaluation["event_log_sha256"][reader] == row["log_sha256"]

event_path = PUBLIC / "actual_events.json"
if event_path.exists():
    assert read(event_path) == events_public
else:
    write_once(event_path, events_public)
assert subprocess.run(["git", "check-ignore", "-q", str(LOCAL / "inputs.json")], cwd=ROOT).returncode == 0
assert subprocess.run(["git", "check-ignore", "-q", str(final)], cwd=ROOT).returncode == 1

destination = OUT / "final_checks.json"
documents = []
for name in ("ORACLE_VALIDITY.md", "EVALUATION_METRICS.md", "TASK4_RESULTS_VI.md"):
    path = EC / name
    text = path.read_text(encoding="utf-8")
    assert '\ufffd' not in text
    links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', text)
    missing = [link for link in links if not link.startswith(('https://', 'http://', '#'))
               and not (EC / link.split('#')[0]).is_file()
               and (EC / link.split('#')[0]).resolve() != destination.resolve()]
    assert not missing, (name, missing)
    documents.append(dict(path=name, sha256=sha_file(path), links_checked=len(links), broken_links=missing))

before = read(OUT / "preservation_before.json")
old_paths = {r["path"] for r in before["files"]}
current = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                                  cwd=ROOT, text=True, encoding="utf-8").splitlines()
new_paths = sorted(set(current) - old_paths - {destination.relative_to(ROOT).as_posix()})
assert all(p.startswith("research/evidence_contract/") for p in new_paths), 'Unexpected new path outside research area'
result = dict(task="TASK 4", all_checks_passed=True, head=preservation["head"],
              tested_cases_including_subtests=tests["tests"], test_functions_or_parametrized_cases=146, subtests=6,
              actual_model_invocations=12, checker_model_invocations=0,
              fresh_raw_outputs=total_raw, independent_failure_labels=0,
              synthetic_faults_in_actual_model_totals=0, readers=reader_checks,
              score_replay_byte_identical=True, score_sha256=sha_file(final),
              scoring_new_calls=0, old_files_unchanged=2523, head_and_refs_unchanged=True,
              documents=documents, normalized_schema_full_draft_validator_run=False,
              normalized_schema_required_field_test_passed=True,
              verification_script_sha256=sha_file(__file__),
              test_execution_sha256=sha_file(OUT / 'pytest_run_06.execution.json'),
              preservation_audit_sha256=sha_file(OUT / 'preservation_final.json'),
              new_public_artifacts={p: sha_file(ROOT / p) for p in new_paths if (ROOT / p).is_file()},
              actual_inference_event_snapshots_sha256=sha_file(event_path),
              no_full_benchmark=True, no_training=True, no_production_changes=True,
              limitations="One fictional ID; no independent fault/readability gold; no H1-H3 or paper effectiveness claim")
write_once(destination, result)
assert destination.is_file()
print(json.dumps(dict(all_checks_passed=True, unit_cases=146, subtests=6, actual_calls=12,
                      replay_new_calls=0, checked_preexisting_files=2523, changed_preexisting_files=0)))
