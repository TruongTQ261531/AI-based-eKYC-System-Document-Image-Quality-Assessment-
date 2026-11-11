"""Build a local anonymous development replication candidate from existing evidence."""
from importlib import metadata
import argparse
import json
import re
import subprocess
import sys
import zipfile

from ..task55.data import EC, OUT, ROOT, FrozenPilot, read, save_new, sha
from .intake import EXECUTION, PRIVATE

SOURCE = (
    "research/evidence_contract/contracts.py", "research/evidence_contract/source_graph.py",
    "research/evidence_contract/validity.py", "research/evidence_contract/oracle.py",
    "research/evidence_contract/normalized_output.py", "research/evidence_contract/task5/baselines.py",
    "research/labels_schema.py",
)
SKELETONS = ("research/__init__.py", "research/evidence_contract/__init__.py",
             "research/evidence_contract/task5/__init__.py")
METHODS = ("A", "B0", "B2", "B3", "A_flat")

README = """# Development replication candidate

This local candidate verifies saved development observations and replays five original
test oracles against fictional specimen graphs and existing reader outputs.

Run "python -I -B verify_results.py" for the standard-library aggregate and hash check.
Run "python -I -B verify_results.py --oracle" in the existing research environment to
replay A, B0, B2, B3 and A_flat. The second command requires NumPy, Pillow and OpenCV.
Exact package versions are recorded in ENVIRONMENT.json. Both modes make zero model calls.

The data contain 132 scheduled development comparisons, constructed fault results,
and stage-pilot observations. Graph values and reader outputs refer to authored,
fictional specimens. Source code is copied byte-for-byte for the scored methods.
All input references and eligibility decisions come from the frozen development study.
The archive does not independently establish human legibility or completeness of
the original validation inventory. It contains no human IFV submissions.

An exact result replay demonstrates computational reproducibility of the stored
decisions. Independent replication, confirmatory evidence, model-inference
reproduction, dataset rights review and final anonymous release review remain pending.
Model weights, customer information, training data, machine paths and author metadata
are outside this candidate. The copied source is supplied for inspection and the
documented score-only entry point. License and third-party redistribution review must
be completed before an external release. No archive has been published.
"""


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def build(name):
    if not re.fullmatch(r"candidate_[0-9]{8}_[0-9]{2}", name):
        raise ValueError("Use an opaque candidate date and number")
    public = EXECUTION / "continuation_20261111"
    folder = PRIVATE / "continuation_20261111" / name
    archive = EC / "paper" / (name + ".zip")
    if folder.exists() or archive.exists():
        raise FileExistsError("Candidate exists. Inspect the previous receipt before selecting a new attempt")
    folder.mkdir(parents=True)
    pilot = FrozenPilot()
    audit = read(OUT / "audit_run_01.json")
    row_map = {(row["pack_id"], row["reader"]): row for row in audit["rows"]}
    cases = []
    for pack, graph, report, before, after in pilot.instances():
        if graph.role not in ("fixture", "development") or graph.data_policy != "fictional":
            raise ValueError("Release candidate contains an unsupported input policy")
        row = row_map[pack["pack_id"], after.reader_id]
        cases.append(dict(graph=graph.to_dict(), validation=report.to_dict(),
                          before=before.to_dict(), after=after.to_dict(),
                          checks={key: row["checks"][key] for key in METHODS}))
    save_new(folder / "data/oracle_cases.json", cases)
    save_new(folder / "data/decisions.json",
             [dict(stratum=r["stratum"], contract=r["contract_id"], checks=r["checks"]) for r in audit["rows"]])
    controls = read(EXECUTION / "controlled_faults.json")
    keys = ("family", "fault_installed", "fault_activated", "independently_faulty",
            "error_types", "methods", "eligibility")
    save_new(folder / "data/controls.json", [{k: row[k] for k in keys} for row in controls["cases"]])
    stages = read(EXECUTION / "ab_execute.json")
    safe_stages = [dict(cluster=case["cluster"], target=case["target"], contrasts=case["contrasts"],
                        stages={name: dict(end_to_end=view["end_to_end"]) for name, view in case["stages"].items()})
                   for case in stages["cases"]]
    save_new(folder / "data/stages.json", safe_stages)
    aggregate = read(EXECUTION / "ab_stage_comparison.json")
    primary = audit["primary"]
    expected = dict(primary=primary["n"], A_B3_verdict_matches=primary["verdict_agreement"],
                    A_flat_verdict_matches=primary["A_flat_verdict_agreement"], A_alarms=primary["A_alarms"],
                    B3_alarms=primary["B3_alarms"], A_exclusive=primary["A_exclusive_alarms"],
                    controlled_cases=controls["records"], controlled_observable_faults=controls["independently_faulty"],
                    structured_faults=controls["structured_field_faults"],
                    structured_detected={key: controls["results"][key]["structured_field_mutation_score"]["numerator"]
                                         for key in ("A", "B3")},
                    stage_f1={name: [row["field_f1"]["numerator"], row["field_f1"]["denominator"]]
                              for name, row in aggregate["pooled"].items()},
                    crop_correct_to_wrong=aggregate["contrasts"]["rectified_vs_bad_crop"]["pointwise_correct_to_wrong"])
    save_new(folder / "EXPECTED.json", expected)
    for name_source in SOURCE:
        target = folder / "source" / name_source
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write((ROOT / name_source).read_bytes())
    for name_source in SKELETONS:
        write_text(folder / "source" / name_source, '"""Anonymous development score replay package."""\n')
    with (folder / "verify_results.py").open("xb") as handle:
        handle.write((EC / "paper/verify_results.py").read_bytes())
    write_text(folder / "README.md", README)
    save_new(folder / "ENVIRONMENT.json", dict(python=sys.version.split()[0], purpose="existing CPU research environment",
        dependencies={package: metadata.version(package) for package in ("numpy", "Pillow", "opencv-python-headless")}))
    forbidden = re.compile(r"(?:[A-Za-z]:[\\/]|/Users/|/home/|Truong|laptrinhcuatao|@gmail\.com)", re.I)
    for path in folder.rglob("*"):
        if path.is_file() and forbidden.search(path.read_text(encoding="utf-8")):
            raise ValueError("Identifying content found in release candidate: " + path.relative_to(folder).as_posix())
    files = {p.relative_to(folder).as_posix(): sha(p) for p in folder.rglob("*") if p.is_file()}
    save_new(folder / "MANIFEST.json", dict(scope="development score replay only", files=files))
    command = [sys.executable, "-I", "-B", str(folder / "verify_results.py"), "--oracle"]
    completed = subprocess.run(command, cwd=folder, capture_output=True, text=True, encoding="utf-8", check=False)
    write_text(public / (name + "_verification.log"), completed.stdout + completed.stderr)
    if completed.returncode:
        raise RuntimeError("Candidate verification failed. Preserve the folder and log before repairing.")
    verification = json.loads(completed.stdout)
    pilot.assert_read_only()
    with zipfile.ZipFile(archive, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            info = zipfile.ZipInfo(path.relative_to(folder).as_posix(), date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes(), compresslevel=9)
    receipt = dict(status="LOCAL_CANDIDATE_VERIFIED", archive_name=archive.name, archive_sha256=sha(archive),
                   archive_bytes=archive.stat().st_size, files=len(files) + 1,
                   automatic_identity_scan="PASS", fixed_zip_timestamps=True,
                   verification=verification, model_calls=0, human_labels=0,
                   release_readiness="PENDING_RIGHTS_AND_HUMAN_REVIEW", published=False)
    save_new(public / (name + "_receipt.json"), receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="candidate_20261111_01")
    args = parser.parse_args()
    print(json.dumps(build(args.name)), flush=True)
