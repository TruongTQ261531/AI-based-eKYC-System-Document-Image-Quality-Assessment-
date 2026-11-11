"""Read-only recovery verification and a before/after record for master_01."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

from ..task55.data import EC, OUT, ROOT, FrozenPilot, read, save_new, sha
from ..task55.review import PACKET_ROOT

EXECUTION = EC / "execution/master_01"
PRIVATE = EC / "local/master_01"
PLAN = Path(r"D:\App\EASE2027_EVIDENCE_CONTRACT_RECOVERY_MASTER_PLAN.md")


def git(*args, root=ROOT):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=root, encoding="utf-8").strip()


def pinned_asset(row):
    path = ROOT / row["path"]
    if path.stat().st_size != row["bytes"]:
        raise ValueError("Historical checkpoint size changed: " + row["path"])
    if row["algorithm"] == "sha256":
        value = sha(path)
    elif row["algorithm"] == "git_blob_sha1":
        checksum = hashlib.sha1(f"blob {row['bytes']}\0".encode("ascii"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                checksum.update(chunk)
        value = checksum.hexdigest()
    else:
        raise ValueError("Unknown historical checkpoint checksum")
    if value != row["hash"]:
        raise ValueError("Historical checkpoint hash changed: " + row["path"])


def recovery_paths():
    inventory = read(EC / "execution/task55_recovery/resume_snapshot.json")
    names = {row["path"] for row in inventory["files"]}
    skip = {"__pycache__", "master", "master_01"}
    for path in EC.rglob("*"):
        if not path.is_file() or set(path.relative_to(EC).parts) & skip or path.name == "MASTER_EXECUTION_STATUS.md":
            continue
        if path.is_relative_to(EC / "local"):
            continue
        names.add(path.relative_to(ROOT).as_posix())
    review = read(OUT / "review_packet_preparation.json")
    names.update((PACKET_ROOT / name).relative_to(ROOT).as_posix() for name in review["file_hashes"])
    return sorted(names)


def current_review_status():
    phase1 = EC / "local/task55_human_submissions"
    phase2 = EC / "local/task55_output_review"
    return dict(phase1_files=len(list(phase1.glob("*/observations.json"))),
                phase2_packets=len(list(phase2.glob("*/publication.json"))),
                phase2_files=len(list(phase2.glob("*/submissions/*/output_observations.json"))))


def start():
    original = read(EC / "RECOVERY_EVIDENCE.json")
    handover = PLAN.read_text(encoding="utf-8-sig")
    audit = read(OUT / "audit_run_01.json")
    rows = [row for row in audit["rows"] if row["stratum"] == "primary"]
    summary = dict(rows=len(rows), a_b3=sum(r["checks"]["A"]["verdict"] == r["checks"]["B3"]["verdict"] for r in rows),
                   a_flat=sum(r["checks"]["A"]["verdict"] == r["checks"]["A_flat"]["verdict"] for r in rows),
                   a_alarms=sum(r["checks"]["A"]["alarm"] for r in rows), b3_alarms=sum(r["checks"]["B3"]["alarm"] for r in rows),
                   a_only=sum(r["checks"]["A"]["alarm"] and not r["checks"]["B3"]["alarm"] for r in rows))
    if summary != dict(rows=120, a_b3=78, a_flat=120, a_alarms=17, b3_alarms=58, a_only=0):
        raise ValueError("Historical pilot summary differs from handover")
    verified_cache = FrozenPilot()
    verified_cache.assert_read_only()
    assets = original["checkpoints"]["verified_assets"]
    for asset in assets:
        pinned_asset(asset)
    files = {name: sha(ROOT / name) for name in recovery_paths()}
    save_new(EXECUTION / "intake_hashes.json", files)
    report = dict(branch=git("rev-parse", "--abbrev-ref", "HEAD"), head=git("rev-parse", "HEAD"),
                  refs=git("show-ref"), status=git("status", "--short").splitlines(),
                  tracked=git("diff", "--name-only"), staged=git("diff", "--cached", "--name-only"),
                  mentor=git("status", "--short", root=ROOT.parent / "mentor-ekyc-v3.2.0"),
                  handover_sha256=sha(PLAN), handover_lines=len(handover.splitlines()),
                  input_files_hashed=len(files), checkpoint_assets_checked=len(assets), 
                  valid_historical_cache=len(verified_cache.outputs),
                  original_inference_log_hashes=verified_cache.log_hashes, review=current_review_status(),
                  verified_audit=summary, model_calls=0)
    save_new(EXECUTION / "intake.json", report)
    return report


def finish():
    report = read(EXECUTION / "intake.json")
    expected = read(EXECUTION / "intake_hashes.json")
    changed = [name for name, checksum in expected.items() if not (ROOT / name).is_file() or sha(ROOT / name) != checksum]
    refs_unchanged = report["refs"] == git("show-ref")
    tracked = git("diff", "--name-only") or git("diff", "--cached", "--name-only")
    if changed or not refs_unchanged or tracked != (report["tracked"] or report["staged"]):
        raise ValueError("Preservation verification failed: " + repr(changed[:5]))
    for path, checksum in report["original_inference_log_hashes"].items():
        if sha(path) != checksum:
            raise ValueError("Historical inference log changed")
    if any((EC / name).exists() for name in ("TEST_LOCK.json", "TEST_MANIFEST.json")):
        raise ValueError("Unexpected confirmatory publication")
    result = dict(files_matching=len(expected), refs_unchanged=True, changed_files=changed,
                  inference_log_matches=len(report["original_inference_log_hashes"]),
                  confirmatory_published=False, review=current_review_status())
    save_new(EXECUTION / "preservation_after.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("start", "finish"))
    options = parser.parse_args()
    print(json.dumps(start() if options.action == "start" else finish(), ensure_ascii=False))
