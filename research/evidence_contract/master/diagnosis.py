"""Re-tabulate frozen decisions. No scorer change, model load or historical rerun."""
from collections import Counter
import json

from ..task55.data import OUT, read, save_new, sha
from .intake import EXECUTION


def agreement(rows, left, right):
    return dict(n=len(rows), verdict_matches=sum(row["checks"][left]["verdict"] == row["checks"][right]["verdict"] for row in rows),
                left_alarms=sum(row["checks"][left]["alarm"] for row in rows),
                right_alarms=sum(row["checks"][right]["alarm"] for row in rows),
                left_only=sum(row["checks"][left]["alarm"] and not row["checks"][right]["alarm"] for row in rows),
                right_only=sum(row["checks"][right]["alarm"] and not row["checks"][left]["alarm"] for row in rows))


def analyze():
    path = OUT / "audit_run_01.json"
    rows = read(path)["rows"]
    primary = [r for r in rows if r["stratum"] == "primary"]
    diagnostic = [r for r in rows if r["stratum"] != "primary"]
    differences = [r for r in primary if r["checks"]["A"]["verdict"] != r["checks"]["B3"]["verdict"]]
    reasons = Counter(r["checks"]["A"]["reason"] for r in differences)
    ablations = ("A_flat", "A_no_alternative", "A_no_validator", "A_no_NI")
    # C1's declared-only wrapper exception belongs to diagnostics, not a
    # matched valid counterexample. In the primary panel, original eligibility
    # accounts for every observed discrepancy.
    if len(differences) != 42 or any(r["contract_id"] not in ("C3", "C4") for r in differences):
        raise ValueError("Revisit the recorded pilot causal accounting")
    return dict(pilot_sha256=sha(path), scope="observed development decisions", primary=agreement(primary, "A", "B3"),
                ablations={name: {"primary": agreement(primary, "A", name), "diagnostic": agreement(diagnostic, "A", name)}
                           for name in ablations},
                sources={name: agreement(primary, "A", name) for name in ("B0", "B2", "B3_V3_gate")},
                by_contract={cid: agreement([r for r in primary if r["contract_id"] == cid], "A", "B3")
                             for cid in ("C1", "C2", "C3", "C4")},
                b3_equals_v3_gate=agreement(primary, "B3", "B3_V3_gate"),
                diagnostics_raw_vs_gated_v3=agreement(diagnostic, "B3_V3", "B3_V3_gate"),
                discordance_reasons=dict(reasons),
                discordance_by_contract=dict(Counter(r["contract_id"] for r in differences)),
                taxonomy=dict(Counter(cat for row in primary for cat in row["checks"]["A"]["categories"])),
                old_inference_executed_again=False, model_calls=0)


if __name__ == "__main__":
    result = analyze()
    save_new(EXECUTION / "method_decision_replay.json", result)
    print(json.dumps({key: result[key] for key in ("primary", "discordance_by_contract", "discordance_reasons", "model_calls")}))
