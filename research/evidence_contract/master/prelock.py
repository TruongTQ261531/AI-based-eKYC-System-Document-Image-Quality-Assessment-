"""Draft-only protocol preflight and a clearly synthetic sizing illustration."""
from math import comb, sqrt
from pathlib import Path, PureWindowsPath
import json

import numpy as np

from ..task55.data import read, save_new, sha
from .exposure import validate_manifest
from .intake import EXECUTION, EC, PRIVATE, current_review_status
from .statistics import rate

REQUIRED = (
    "new_go_decision", "claims_and_endpoints_approved", "independent_exposure_audit",
    "independent_fault_references", "verified_reviewer_provenance", "adequacy_and_power_review",
    "specimen_manifest", "dataset_and_code_hashes", "reader_and_prompt_hashes",
    "perturbations_and_budget", "baseline_and_ablations", "exclusions_and_analysis",
)


def verify_bindings(bindings, root):
    """Check draft file/hash references, without issuing a lock or scientific GO."""
    root = Path(root).resolve()
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError("Expected named file bindings")
    checked = {}
    for key, record in bindings.items():
        if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
            raise ValueError("Expected path and SHA256 binding")
        name = record["path"]
        if not isinstance(name, str):
            raise ValueError("Expected relative binding path")
        relative = PureWindowsPath(name)
        if relative.drive or relative.root or ".." in relative.parts or not relative.parts:
            raise ValueError("Binding path must remain inside the artifact root")
        from .exposure import sha_token
        if not sha_token(record["sha256"]):
            raise ValueError("Expected a SHA256 binding")
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Binding resolves outside the artifact root")
        state = "MISSING" if not path.is_file() else "MATCH" if sha(path) == record["sha256"] else "HASH_MISMATCH"
        checked[key] = state
    return dict(status="PASS" if all(s == "MATCH" for s in checked.values()) else "BLOCKED", files=checked)


def draft_preflight(proposal, *, specimen=None, exposure=None, artifact_root=None):
    if proposal.get("schema") != "evidence-test-lock-draft/1" or proposal.get("state") != "DRAFT_ONLY":
        raise ValueError("Master 6A validates drafts only")
    if proposal.get("allow_confirmatory_execution") is not False:
        raise ValueError("6A cannot authorize execution")
    entries = proposal.get("future_requirements")
    if not isinstance(entries, dict) or set(entries) != set(REQUIRED):
        raise ValueError("Missing pre-lock requirements")
    if any(value not in ("PENDING", "PREPARED_DRAFT", "BLOCKED") for value in entries.values()):
        raise ValueError("Draft status cannot certify scientific readiness")
    checked = None if specimen is None else validate_manifest(specimen, exposure or {})
    bindings = None
    if "file_bindings" in proposal:
        if artifact_root is None:
            raise ValueError("File bindings require their explicit artifact root")
        bindings = verify_bindings(proposal["file_bindings"], artifact_root)
    return dict(status="BLOCKED", unmet=[k for k, v in entries.items() if v != "PREPARED_DRAFT"],
                schema_check="PASS", manifest_check=checked, binding_check=bindings, confirmatory_executable=False)


def sizing_illustration(*, draws=4000, seed=7195):
    """One independent binary no-fault pair/cluster. No empirical power claim."""
    rng = np.random.default_rng(seed)
    alpha = .05 / 3
    assumptions = [(.06, .09), (.04, .14), (.02, .22)]
    rows = []
    for n in (24, 48, 96, 192):
        tails = {(d, k): sum(comb(d, x) for x in range(k, d + 1)) / (2 ** d)
                 for d in range(n + 1) for k in range(d // 2 + 1, d + 1)}
        for a_only, b_only in assumptions:
            a, b, _ = rng.multinomial(n, [a_only, b_only, 1 - a_only - b_only], size=draws).T
            significant = sum(tails.get((int(x + y), int(y)), 1.) <= alpha and int(x + y) >= 8 for x, y in zip(a, b))
            probability = significant / draws
            rows.append(dict(clusters=n, P_A_only_alarm=a_only, P_B_only_alarm=b_only,
                             assumed_far_delta=a_only - b_only, rejection=rate(significant, draws),
                             monte_carlo_standard_error=sqrt(probability * (1 - probability) / draws)))
    return dict(scope="hypothetical paired no-fault cluster power only", draws=draws, seed=seed,
                worst_case_holm_alpha=alpha, includes_coverage_or_recall_guard=False, rows=rows)


if __name__ == "__main__":
    draft = read(EC / "master/test_lock_draft.json")
    result = draft_preflight(draft)
    result.update(review=current_review_status(), proposal_sha256=sha(EC / "master/test_lock_draft.json"),
                  exposure_audit_sha256=sha(EXECUTION / "exposure_audit_final.json"),
                  exposure_index_sha256=sha(PRIVATE / "exposure_index_final.json"), model_calls=0)
    sizing = sizing_illustration()
    json.dumps(sizing, allow_nan=False)
    save_new(EXECUTION / "prelock_readiness_v2.json", result)
    save_new(EXECUTION / "sizing_illustration_v2.json", sizing)
    print(json.dumps(result), flush=True)
