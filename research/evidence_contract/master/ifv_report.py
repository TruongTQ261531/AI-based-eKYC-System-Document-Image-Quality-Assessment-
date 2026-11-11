"""Read-only replay of a sealed human IFV submission and paired descriptive report."""
from collections import Counter
from pathlib import Path
import argparse
import json

from ..task55 import ifv
from ..task55.data import digest, read, save_new, sha
from ..task55.ifv_sampling import SAMPLE, RECOVERY
from .intake import EXECUTION, current_review_status
from .statistics import paired_interval, rate

METHODS = ("A", "B3", "B3_V3_gate", "A_flat", "B0", "B2")
KNOWN = {"CONFIRMED_FAULT", "NO_FAULT"}
DECIDED = {"PASS", "CANDIDATE_VIOLATION", "CONFIRMED_VIOLATION"}
LABELS = KNOWN | {"INVALID_TEST", "INCONCLUSIVE"}


def method_summary(cases, method):
    confusion = Counter({k: 0 for k in ("TP", "FP", "FN", "TN")})
    status = Counter()
    alarms_by_status = Counter()
    decisions = 0
    for row, label in cases:
        check = row["checks"][method]
        status[label] += 1
        if check["alarm"]:
            alarms_by_status[label] += 1
        if label == "CONFIRMED_FAULT":
            confusion["TP" if check["alarm"] else "FN"] += 1
        elif label == "NO_FAULT":
            confusion["FP" if check["alarm"] else "TN"] += 1
        decisions += label in KNOWN and check["verdict"] in DECIDED
    tp, fp, fn, tn = (confusion[k] for k in ("TP", "FP", "FN", "TN"))
    return dict(confusion=dict(confusion), labeled_cases=tp + fp + fn + tn,
                status=dict(status), alarms_by_status=dict(alarms_by_status),
                precision=rate(tp, tp + fp), sensitivity_on_reviewed=rate(tp, tp + fn),
                false_alarm_rate_on_reviewed=rate(fp, fp + tn),
                decision_coverage_on_reviewed=rate(decisions, tp + fp + fn + tn),
                invalid_alarm_rate=rate(alarms_by_status["INVALID_TEST"], status["INVALID_TEST"]),
                population_recall=None)


def paired_summary(cases):
    def row_count(item, method, metric):
        row, label = item
        check = row["checks"][method]
        eligible = {"FAR": label == "NO_FAULT", "sensitivity": label == "CONFIRMED_FAULT",
                    "coverage": label in KNOWN, "precision": label in KNOWN and check["alarm"]}[metric]
        success = {"coverage": check["verdict"] in DECIDED, "FAR": check["alarm"],
                   "sensitivity": check["alarm"], "precision": label == "CONFIRMED_FAULT"}[metric]
        return int(success and eligible), int(eligible)

    return {metric: paired_interval([(row["physical_id_sha256"], *row_count((row, label), "A", metric),
                                      *row_count((row, label), "B3", metric))
                                     for row, label in cases])
            for metric in ("FAR", "sensitivity", "coverage", "precision")}


def summarize(links, labels):
    if set(labels) - set(links):
        raise ValueError("Review labels contain cases outside the sealed sample")
    if any(set(value) != {"pointwise", "relation"} or set(value.values()) - LABELS for value in labels.values()):
        raise ValueError("Unknown or incomplete endpoint labels")
    result = {}
    for endpoint in ("pointwise", "relation"):
        cases = [(case["row"], labels.get(key, {}).get(endpoint, "UNREVIEWED"))
                 for key, case in links.items() if case["row"]["stratum"] == "primary"]
        by_contract = {contract: {method: method_summary(
            [(row, label) for row, label in cases if row["contract_id"] == contract], method) for method in METHODS}
                       for contract in ("C1", "C2", "C3", "C4")}
        clusters = sorted({row["physical_id_sha256"] for row, _ in cases})
        by_cluster = {}
        for i, cluster in enumerate(clusters, start=1):
            cluster_cases = [(row, label) for row, label in cases if row["physical_id_sha256"] == cluster]
            by_cluster[f"cluster_{i}"] = {method: method_summary(cluster_cases, method) for method in ("A", "B3")}
        result[endpoint] = dict(primary_cases=len(cases), cluster_count=len(clusters),
                                overall={m: method_summary(cases, m) for m in METHODS}, by_contract=by_contract,
                                by_physical_id=by_cluster, paired_A_minus_B3=paired_summary(cases),
                                diagnostics=dict(Counter(labels.get(key, {}).get(endpoint, "UNREVIEWED")
                                                         for key, case in links.items() if case["row"]["stratum"] != "primary")))
    return result


def sample_frame_links(frame, snapshot):
    """Keep selected cases without phase-1 evidence visible as UNREVIEWED."""
    return {"CASE-" + digest([snapshot, case["identity_sha256"]])[:16]: case
            for case in frame["frame"] if case["selected"]}


def sealed_results(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ifv.STAGE2.resolve()) or path.name != "output_observations.json":
        raise ValueError("Import a real phase-2 JSON first and provide its sealed copy under local/")
    folder = path.parents[2]
    if path.parent.parent.name != "submissions":
        raise ValueError("Unexpected submission path")
    ifv.verify_publication(folder)
    packet = read(folder / "packet.json")
    phase1, _, reviewer = ifv.sealed_phase1(packet["phase1_snapshot"], close_partial=True)
    export = read(path)
    labels = ifv.validate_stage2(export, packet)
    receipt = read(path.parent / "descriptive_summary.json")
    if (receipt["status"] != "SINGLE_REVIEW_UNADJUDICATED" or digest(export) != path.parent.name
            or labels != read(path.parent / "labels.json") or receipt["phase2_export_sha256"] != digest(export)
            or receipt["phase1_snapshot"] != packet["phase1_snapshot"]
            or folder.name != digest(["reviewer-id/1", reviewer["reviewer_id"].strip().casefold()])):
        raise ValueError("Submission replay differs from frozen labels")
    links = read(ifv.JOINS / (folder.name + ".json"))
    frame = read(SAMPLE)
    if sha(SAMPLE) != read(RECOVERY / "ifv_sampling_summary.json")["sample_file_sha256"]:
        raise ValueError("Historical sampling frame changed")
    selected = {case["identity_sha256"]: case for case in frame["frame"] if case["selected"]}
    if set(links) != {case["case_id"] for case in packet["cases"]} or any(
            selected.get(case["identity_sha256"]) != case or key != "CASE-" + digest(
                [packet["phase1_snapshot"], case["identity_sha256"]])[:16] for key, case in links.items()):
        raise ValueError("Analyst join does not match the sealed sampling frame")
    complete_frame = sample_frame_links(frame, packet["phase1_snapshot"])
    if (len(complete_frame) != receipt["frame_selected_cases"]
            or len(complete_frame) - len(links) != receipt["selected_missing_evidence"]):
        raise ValueError("Review sample denominator differs from the frozen selection")
    return dict(status="SINGLE_REVIEW_UNADJUDICATED", phase1_packet_id=phase1["packet_id"],
                reviewers=1, inter_rater_agreement=None, independence_verified=False,
                reviewer_role=reviewer["role"], declared_prior_output_exposure=reviewer["output_exposure"],
                declared_phase1_slot_exposure=dict(Counter(evidence["prior_exposure"] for case in packet["cases"]
                    for evidence in (case["before_evidence"], case["after_evidence"]))),
                cases_selected=receipt["frame_selected_cases"], selected_missing_evidence=receipt["selected_missing_evidence"],
                reviewed_cases=len(labels), frame_scope="development, stratified sample, no population inference",
                results=summarize(complete_frame, labels), model_calls=0)


def waiting():
    records = current_review_status()
    if records["phase2_files"]:
        raise ValueError("Use --submission for a sealed phase-2 file")
    status = "WAITING_FOR_PHASE2_REVIEW" if records["phase1_files"] else "WAITING_FOR_HUMAN_REVIEW"
    return dict(status=status, **records, real_metrics=None, ci=None, inter_rater_agreement=None, model_calls=0)


def format_report(report):
    def cell(value):
        if value["value"] is None:
            return "NA"
        return f"{value['numerator']}/{value['denominator']} ({value['value']:.1%})"

    lines = ["# Independent fault validation · development report", "",
             "One-person pilot. Independence and agreement remain unverified.", "",
             f"Reviewed {report['reviewed_cases']} of {report['cases_selected']} selected comparisons.",
             "Metrics apply to the reviewed subset. Invalid, inconclusive and unreviewed comparisons are tracked separately.", ""]
    for endpoint, result in report["results"].items():
        lines.extend([f"## {endpoint.title()} endpoint", "",
                      "| Method | TP | FP | FN | TN | Precision | Sensitivity | FAR | Decision coverage |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---:|"])
        for method, value in result["overall"].items():
            counts = [str(value["confusion"][label]) for label in ("TP", "FP", "FN", "TN")]
            ratios = [cell(value[key]) for key in ("precision", "sensitivity_on_reviewed",
                       "false_alarm_rate_on_reviewed", "decision_coverage_on_reviewed")]
            lines.append("| " + " | ".join([method, *counts, *ratios]) + " |")
        lines.extend(["", "Paired intervals, exclusions, per-contract counts and anonymized ID groups are in the companion JSON.", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path)
    args = parser.parse_args()
    report = sealed_results(args.submission) if args.submission else waiting()
    name = "ifv_descriptive_" + digest(report)[:16] if args.submission else "ifv_waiting"
    save_new(EXECUTION / (name + ".json"), report)
    if args.submission:
        with (EXECUTION / (name + ".md")).open("x", encoding="utf-8", newline="\n") as output:
            output.write(format_report(report))
    print(json.dumps(dict(status=report["status"], model_calls=0)))
