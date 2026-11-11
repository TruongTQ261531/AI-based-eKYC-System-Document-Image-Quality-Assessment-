"""Conditional C1--C4 oracles; behavior alarms are not identity/fault proofs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import json
import re

from .source_graph import EvidenceGraph, Field, State, compatible, date_parts, normalized
from .validity import ValidationReport, Validity


class Status(str, Enum):
    PASS = "PASS"
    VIOLATION = "VIOLATION"
    INVALID_TEST = "INVALID_TEST"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class Policy:
    policy_id: str = "pixel-faithful-field-extraction/1"
    require_supported_fields: bool = True
    geometry_operators: tuple[str, ...] = ("identity", "translate_pad")


@dataclass(frozen=True)
class RegressionEvidence:
    version0_sha256: str
    version1_sha256: str
    original_pixel_sha256: str
    followup_pixel_sha256: str
    v0_original: dict
    v0_followup: dict
    v1_original: dict
    v1_followup: dict
    stability_verified: bool
    unchanged_requirement_provenance: str


@dataclass(frozen=True)
class Result:
    contract_id: str
    status: Status
    key: str
    reason: str
    preconditions: dict
    expected_relation: str
    exceptions: tuple[str, ...]
    diagnostics: dict
    behavior_regression_verified: bool = False
    software_fault_confirmed: bool = False

    def to_dict(self):
        value = asdict(self)
        value["status"] = self.status.value
        return value


SPEC = {
    "C1": ("No nonempty assertion for a field with complete, verified evidence removal",
           ("Incomplete source coverage", "Invalid mask", "Malformed structured output")),
    "C2": ("Surviving valid backup supports the field; score reading separately from absent evidence",
           ("Unverified MRZ/checksum", "Unknown backup legibility", "Lower supported precision")),
    "C3": ("An unaffected supported field retains its correct value under a valid target mask",
           ("Original output already wrong", "Changed label/context", "Unverified version/stability")),
    "C4": ("Correct supported information is invariant under an explicitly supported, evidence-preserving geometry operation",
           ("Unverified text preservation", "Unsupported orientation policy", "Original output already wrong")),
}


def _prediction(output):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Duplicate prediction key")
            value[key] = item
        return value
    try:
        value = json.loads(output, object_pairs_hook=unique) if isinstance(output, str) else output
        if not isinstance(value, dict) or any(not isinstance(k, str) or (v is not None and not isinstance(v, str))
                                              for k, v in value.items()):
            return None, "Expected an object with string/null values"
        return dict(value), None
    except (ValueError, TypeError) as exc:
        return None, str(exc)


def _present(output, key):
    return key in output and output[key] is not None and bool(output[key].strip())


def assessment(output, field: Field):
    if field.state() != State.SUPPORTED:
        return "unverified_reference"
    if not _present(output, field.key):
        return "omitted"
    predicted = output[field.key]
    sources = field.supported_sources()
    date_sources = [s for s in sources if s.value_kind.startswith("date_")]
    if date_sources:
        pred_kind = "date_full" if date_parts(predicted, "date_full") else "date_yymmdd"
        pred = date_parts(predicted, pred_kind)
        if pred is None:
            return "wrong"
        precision = max(date_parts(s.reference_value, s.value_kind)[3] for s in date_sources
                        if date_parts(s.reference_value, s.value_kind) is not None)
        if pred[3] > precision:
            return "precision_overreach"
        if pred[3] < precision:
            return "precision_loss"
        return "correct" if any(compatible(predicted, pred_kind, s.reference_value, s.value_kind)
                                for s in date_sources) else "wrong"
    return "correct" if any(normalized(predicted) == normalized(s.reference_value) for s in sources) else "wrong"


def _regression_verified(quad, report, original_field, after_field, before_output, after_output):
    if quad is None:
        return False
    if (not all(re.fullmatch("[a-f0-9]{64}", v) for v in (quad.version0_sha256, quad.version1_sha256))
            or quad.version0_sha256 == quad.version1_sha256
            or quad.original_pixel_sha256 != report.before_pixel_sha256
            or quad.followup_pixel_sha256 != report.after_pixel_sha256
            or quad.stability_verified is not True or not quad.unchanged_requirement_provenance):
        return False
    values = [_prediction(v) for v in (quad.v0_original, quad.v0_followup, quad.v1_original, quad.v1_followup)]
    if any(error for _, error in values):
        return False
    outputs = [v for v, _ in values]
    if outputs[2] != before_output or outputs[3] != after_output:
        return False
    return (assessment(outputs[0], original_field) == "correct"
            and assessment(outputs[1], after_field) == "correct"
            and assessment(outputs[2], original_field) == "correct"
            and assessment(outputs[3], after_field) not in ("correct", "unverified_reference"))


def evaluate(contract_id: str, graph: EvidenceGraph, validation: ValidationReport,
             before_output, after_output, *, policy: Policy = Policy(),
             regression: RegressionEvidence | None = None) -> Result:
    if contract_id not in SPEC:
        raise ValueError("Unknown contract")
    mutation = validation.mutation
    key = mutation.retained_key if contract_id == "C3" else mutation.target_key
    key = key or mutation.target_key
    relation, exceptions = SPEC[contract_id]
    preconditions = dict(validity=validation.status.value, policy_id=policy.policy_id,
                         graph_sha256=graph.sha256, mutation_sha256=mutation.sha256)
    diagnostics = dict(validation_reasons=list(validation.reasons), unsupported_assertion=False,
                       reading_status="not_scored", human_readability_claimed=False)

    def result(status, reason, verified=False):
        return Result(contract_id, status, key, reason, preconditions, relation, exceptions,
                      diagnostics, verified, False)

    if (validation.graph_sha256 != graph.sha256 or validation.mutation_sha256 != mutation.sha256
            or mutation.contract_id != contract_id):
        return result(Status.INVALID_TEST, "validation_not_bound_to_graph_mutation_contract")
    if validation.status == Validity.INVALID_TEST:
        return result(Status.INVALID_TEST, "mutation_preconditions_failed")
    if validation.status != Validity.VALID or validation.after_graph is None:
        return result(Status.INCONCLUSIVE, "mutation_preconditions_unverified")
    if (validation.before_pixel_sha256 != graph.input_pixel_sha256
            or validation.after_graph.input_pixel_sha256 != validation.after_pixel_sha256):
        return result(Status.INVALID_TEST, "validation_image_binding_mismatch")
    try:
        original_field = (validation.reference_before_graph or graph).field(key)
        after_field = validation.after_graph.field(key)
    except KeyError:
        return result(Status.INCONCLUSIVE, "semantic_key_not_annotated")
    preconditions.update(original_source_state=original_field.state().value,
                         after_source_state=after_field.state().value,
                         source_coverage=after_field.coverage)
    before, before_error = _prediction(before_output)
    after, after_error = _prediction(after_output)
    if after_error or (contract_id in ("C3", "C4") and before_error):
        diagnostics["format_error"] = after_error or before_error
        return result(Status.INCONCLUSIVE, "structured_output_invalid_scored_separately")
    if contract_id == "C1":
        if after_field.state() != State.REMOVED:
            return result(Status.INCONCLUSIVE, "complete_evidence_removal_not_established")
        diagnostics["unsupported_assertion"] = _present(after, key)
        return result(Status.VIOLATION if _present(after, key) else Status.PASS,
                      "assertion_after_complete_removal" if _present(after, key) else "removed_field_not_asserted")
    if after_field.state() != State.SUPPORTED:
        return result(Status.INCONCLUSIVE, "remaining_evidence_not_verified")
    reading = assessment(after, after_field)
    diagnostics.update(reading_status=reading, omission=reading == "omitted",
                       wrong_value=reading == "wrong", precision_error=reading in ("precision_overreach", "precision_loss"))
    if reading == "unverified_reference":
        return result(Status.INCONCLUSIVE, "reference_conflict_or_unknown_precision")
    if contract_id == "C2":
        # Wrong/missing readings are NOT labeled lack-of-evidence hallucinations.
        if reading == "omitted" and not policy.require_supported_fields:
            return result(Status.PASS, "backup_preserved_optional_omission_scored_separately")
        return result(Status.PASS if reading == "correct" else Status.VIOLATION,
                      "backup_supported_reading" if reading == "correct" else "supported_field_reading_error")
    if contract_id == "C4" and mutation.operator not in policy.geometry_operators:
        return result(Status.INCONCLUSIVE, "geometry_invariance_not_declared_by_sut_policy")
    original_reading = assessment(before, original_field)
    diagnostics["original_reading_status"] = original_reading
    if original_reading != "correct":
        return result(Status.INCONCLUSIVE, "original_already_wrong_or_unverified_not_a_regression")
    if reading == "correct":
        return result(Status.PASS, "supported_information_preserved")
    verified = _regression_verified(regression, validation, original_field, after_field, before, after)
    return result(Status.VIOLATION, "verified_version_regression" if verified else "conditional_metamorphic_failure",
                  verified)
