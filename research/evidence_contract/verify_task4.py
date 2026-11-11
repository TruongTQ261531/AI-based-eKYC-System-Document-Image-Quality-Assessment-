"""Auditable, local TASK4 verification; never executes OCR/VLM or training."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

EC = Path(__file__).resolve().parent
ROOT = EC.parents[1]
OUT = EC / "execution/task4_runner"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def code_hashes():
    paths = sorted(list(EC.glob("*.py")) + list((EC / "tests").glob("*.py")))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}


def tests(label):
    prefix = OUT / label
    log, xml = prefix.with_suffix(".log"), prefix.with_suffix(".xml")
    if log.exists() or xml.exists():
        raise FileExistsError("Verification artifacts already exist")
    before = code_hashes()
    command = [sys.executable, "-B", "-m", "pytest", "research/evidence_contract/tests",
               "research/tests/test_v3_sources.py", "research/tests/test_hp_masks.py",
               "research/tests/test_labels_schema.py", "-q", "-p", "no:cacheprovider",
               "--basetemp=" + str(EC / "local" / label), "--junitxml=" + str(xml)]
    if (EC / "local" / label).exists():
        raise FileExistsError("Never reuse an old pytest temporary directory")
    started = datetime.now(timezone.utc).isoformat()
    start = time.perf_counter()
    with log.open("xb") as stream:
        process = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False)
    after = code_hashes()
    suites = ET.parse(xml).getroot().findall("testsuite") if xml.exists() else []
    result = dict(started_utc=started, ended_utc=datetime.now(timezone.utc).isoformat(),
                  command=command, elapsed_seconds=time.perf_counter() - start, exit_code=process.returncode,
                  code_sha256=before, code_unchanged_during_tests=before == after,
                  stdout_sha256=sha(log), junit_sha256=sha(xml) if xml.exists() else None,
                  tests=sum(int(s.get("tests", 0)) for s in suites),
                  failures=sum(int(s.get("failures", 0)) for s in suites),
                  errors=sum(int(s.get("errors", 0)) for s in suites),
                  skipped=sum(int(s.get("skipped", 0)) for s in suites),
                  actual_model_invocations=0, synthetic_output_injections=True,
                  scope="targeted unit/legacy adapter regression tests; no benchmark or confirmatory images")
    save(prefix.with_suffix(".execution.json"), result)
    print(json.dumps({k: result[k] for k in ("exit_code", "tests", "failures", "errors", "skipped", "code_unchanged_during_tests")}))
    if process.returncode or before != after:
        raise SystemExit(process.returncode or 1)


def audit(label):
    snapshot = json.loads((OUT / "preservation_before.json").read_text(encoding="utf-8"))
    changed = []
    for record in snapshot["files"]:
        path = ROOT / record["path"]
        if not path.is_file() or path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
            changed.append(record["path"])
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()
    result = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  checked_preexisting_files=len(snapshot["files"]),
                  checked_preexisting_bytes=sum(r["bytes"] for r in snapshot["files"]),
                  changed_preexisting_paths=changed, head=git("rev-parse", "HEAD"),
                  branch=git("branch", "--show-current"), refs=git("show-ref"),
                  tracked_diff=git("diff", "--stat"), staged_diff=git("diff", "--cached", "--stat"),
                  status=git("status", "--porcelain=v1"), code_sha256=code_hashes(),
                  scope=snapshot["scope"], git_writes=False, production_changes=False)
    result["head_and_refs_unchanged"] = result["head"] == snapshot["head"] and result["refs"] == snapshot["refs"]
    save(OUT / (label + ".json"), result)
    print(json.dumps(dict(checked_files=result["checked_preexisting_files"], changed=len(changed),
                          head_and_refs_unchanged=result["head_and_refs_unchanged"])))
    if changed or not result["head_and_refs_unchanged"] or result["tracked_diff"] or result["staged_diff"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("tests", "audit"))
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if not args.label or not all(c.isalnum() or c in "_-" for c in args.label):
        raise ValueError("Expected an opaque new verification label")
    tests(args.label) if args.action == "tests" else audit(args.label)


if __name__ == "__main__":
    main()
