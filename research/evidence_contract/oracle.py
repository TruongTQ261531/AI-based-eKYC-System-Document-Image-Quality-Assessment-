"""Five-state oracle: a declared-source alarm is not independently proven absence.

Certificates/labels are separate inputs, not manufactured from generator intent,
parser success, aggregate OCR score or the SUT's own outputs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from . import contracts
from .normalized_output import NormalizedOutput, require_sha
from .source_graph import State, digest, normalized
from .validity import Validity


class Verdict(str, Enum):
    PASS = "PASS"
    CONFIRMED_VIOLATION = "CONFIRMED_VIOLATION"
    CANDIDATE_VIOLATION = "CANDIDATE_VIOLATION"
    INVALID_TEST = "INVALID_TEST"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class EvidenceCertificate:
    """Externally adjudicated evidence, with explicit trust assumptions.

    Hashes establish binding, not reviewer honesty. Artifact provenance must be
    audited before confirmatory use. Construction audits do NOT assert human
    readability. No certificate is automatically issued by this package.
    """
    graph_sha256: str
    mutation_sha256: str
    original_pixel_sha256: str
    followup_pixel_sha256: str
    contract_id: str
    key: str
    basis: str
    provenance: str
    artifact_sha256: str
    independent_from_sut: bool
    independent_from_generator: bool
    reviewers: tuple[str, ...] = ()
    reference_verified: bool = False
    mutation_verified: bool = False
    semantics_verified: bool = False
    source_universe_complete: bool = False
    absence_verified: bool = False
    human_readability_verified: bool = False
    inspected_source_ids: tuple[str, ...] = ()
    origin: str = "external_review"

    def usable(self, graph, validation, contract_id, key):
        hashes = (self.graph_sha256, self.mutation_sha256, self.original_pixel_sha256,
                  self.followup_pixel_sha256, self.artifact_sha256)
        try:
            for value in hashes:
                require_sha(value)
        except ValueError:
            return False
        if (self.graph_sha256 != graph.sha256 or self.mutation_sha256 != validation.mutation_sha256
                or self.original_pixel_sha256 != validation.before_pixel_sha256
                or self.followup_pixel_sha256 != validation.after_pixel_sha256
                or (self.contract_id, self.key) != (contract_id, key)
                or not self.provenance or self.independent_from_sut is not True
                or self.independent_from_generator is not True):
            return False
        if self.basis == "independent_human_review":
            return len({v.strip().casefold() for v in self.reviewers if v.strip()}) >= 2
        return self.basis == "independent_construction_audit" and not self.human_readability_verified


@dataclass(frozen=True)
class GoldLabel:
    """Blind per-output-pair failure label. Unknowns remain None, never negative.

    Root-cause defect identity additionally needs a patch/revert or seeded fault
    activation artifact; neural output anomalies are behavior failures only.
    """
    decision_sha256: str
    is_failure: bool | None
    valid_test: bool | None
    provenance: str
    artifact_sha256: str
    independent: bool
    false_alarm_cause: str | None = None
    verified_failure_cluster: str | None = None
    defect_id: str | None = None
    defect_proof_sha256: str | None = None
    defect_proof_kind: str | None = None
    origin: str = "external_review"

    def usable(self, decision_sha256, output_origin):
        try:
            require_sha(self.artifact_sha256)
            require_sha(self.decision_sha256)
        except ValueError:
            return False
        return (self.independent is True and bool(self.provenance)
                and self.decision_sha256 == decision_sha256
                and (self.origin != "oracle_unit_injected" or output_origin == "oracle_unit_injected")
                and (self.is_failure is None or type(self.is_failure) is bool)
                and (self.valid_test is None or type(self.valid_test) is bool)
                and not (self.is_failure is True and self.valid_test is False))

    def defect_verified(self):
        try:
            require_sha(self.defect_proof_sha256)
        except ValueError:
            return False
        return (self.is_failure is True and self.valid_test is True and bool(self.defect_id)
                and self.defect_proof_kind in ("patch_revert_reproduction", "seeded_fault_activation"))


@dataclass(frozen=True)
class Decision:
    contract_id: str
    key: str
    verdict: Verdict
    alarm_issued: bool
    categories: tuple[str, ...]
    reason: str
    pair_id: str
    decision_sha256: str
    graph_sha256: str
    mutation_sha256: str
    original_pixel_sha256: str
    followup_pixel_sha256: str
    reader_id: str
    reader_fingerprint: str
    output_origin: str
    mutation_validity: str
    test_validity: str
    source_kinds: tuple[str, ...]
    readability: str
    document_group: str
    physical_id_hash: str
    before_call_id: str
    after_call_id: str
    evidence_certificate_accepted: bool
    gold: dict | None
    diagnostics: dict
    behavior_regression_verified: bool = False
    software_fault_confirmed: bool = False

    def to_dict(self):
        result = asdict(self)
        result["verdict"] = self.verdict.value
        return result


def decision_binding(graph, validation, before, after, policy):
    # Includes exact raw output/version/policy, so labels cannot migrate to another model/output.
    return digest(dict(graph=graph.sha256, mutation=validation.mutation_sha256,
                       original=validation.before_pixel_sha256, followup=validation.after_pixel_sha256,
                       reader_before=before.reader_fingerprint, reader_after=after.reader_fingerprint,
                       before_text_sha256=digest(before.raw_text), after_text_sha256=digest(after.raw_text),
                       before_normalizer_sha256=before.normalization_code_sha256,
                       after_normalizer_sha256=after.normalization_code_sha256,
                       before_normalized_sha256=digest([before.fields, before.json_validity]),
                       after_normalized_sha256=digest([after.fields, after.json_validity]),
                       policy=asdict(policy)))


def evaluate(graph, validation, before: NormalizedOutput, after: NormalizedOutput, *,
             policy=contracts.Policy(), certificate: EvidenceCertificate | None = None,
             gold: GoldLabel | None = None, regression=None):
    """Score an already executed pair; never loads or calls any reader."""
    contract_id = validation.mutation.contract_id
    key = validation.mutation.retained_key if contract_id == "C3" else validation.mutation.target_key
    key = key or validation.mutation.target_key
    pair_id = digest([graph.sha256, validation.mutation_sha256,
                      validation.before_pixel_sha256, validation.after_pixel_sha256])
    binding = decision_binding(graph, validation, before, after, policy)
    categories, diag = [], {}
    alarm = confirmed = regression_verified = False
    verdict, reason = Verdict.INCONCLUSIVE, "unassessed"
    target = next((f for f in graph.fields if f.key == key), None)
    state_graph = validation.after_graph
    after_field = next((f for f in state_graph.fields if f.key == key), None) if state_graph else None
    source_kinds = tuple(sorted({s.kind for s in after_field.realizations})) if after_field else ()
    components = [c for s in after_field.supported_sources() for c in s.components if c.required] if after_field else []
    readability = "human_verified" if components and all(
        c.evidence_basis == "human_verified" and c.readability == "readable" for c in components) else (
            "construction_support_only" if components else "unknown_or_removed")
    cert_ok = bool(certificate and certificate.usable(graph, validation, contract_id, key)
                   and (certificate.origin != "oracle_unit_injected" or after.output_origin == "oracle_unit_injected"))
    if cert_ok and certificate.human_readability_verified and certificate.mutation_verified:
        readability = "external_human_verified"
    gold_ok = bool(gold and gold.usable(binding, after.output_origin))
    common = dict(contract_id=contract_id, key=key, pair_id=pair_id, decision_sha256=binding,
                  graph_sha256=graph.sha256, mutation_sha256=validation.mutation_sha256,
                  original_pixel_sha256=validation.before_pixel_sha256,
                  followup_pixel_sha256=validation.after_pixel_sha256,
                  reader_id=after.reader_id, reader_fingerprint=after.reader_fingerprint,
                  output_origin=after.output_origin, mutation_validity=validation.status.value,
                  test_validity=validation.status.value,
                  source_kinds=source_kinds, readability=readability, document_group=graph.source_id,
                  physical_id_hash=digest(graph.physical_id), before_call_id=before.call_id,
                  after_call_id=after.call_id, evidence_certificate_accepted=cert_ok,
                  gold=asdict(gold) if gold_ok else None)

    output_binding_ok = (before.input_pixel_sha256 == validation.before_pixel_sha256
                         and after.input_pixel_sha256 == validation.after_pixel_sha256
                         and before.reader_fingerprint == after.reader_fingerprint
                         and before.output_origin == after.output_origin)
    if not output_binding_ok:
        verdict, reason = Verdict.INVALID_TEST, "output_image_or_reader_binding_mismatch"
        common["test_validity"] = "INVALID_TEST"
    else:
        usable_after = after.json_validity["usable_for_contracts"]
        usable_before = before.json_validity["usable_for_contracts"]
        base = contracts.evaluate(contract_id, graph, validation,
                                  before.fields if usable_before else "not structured output",
                                  after.fields if usable_after else "not structured output",
                                  policy=policy, regression=regression)
        diag = base.to_dict()
        reason, regression_verified = base.reason, base.behavior_regression_verified
        verdict = {contracts.Status.PASS: Verdict.PASS, contracts.Status.VIOLATION: Verdict.CANDIDATE_VIOLATION,
                   contracts.Status.INVALID_TEST: Verdict.INVALID_TEST,
                   contracts.Status.INCONCLUSIVE: Verdict.INCONCLUSIVE}[base.status]
        alarm = base.status == contracts.Status.VIOLATION
        if base.status == contracts.Status.INVALID_TEST:
            common["test_validity"] = "INVALID_TEST"
        # A limited source universe may motivate an explicitly unverified alarm.
        # Never bypass another failed precondition or a malformed output.
        if (contract_id == "C1" and verdict == Verdict.INCONCLUSIVE and usable_after
                and set(validation.reasons) == {"exhaustive_removal_not_proven_by_annotation_scope"}
                and graph.sha256 == validation.graph_sha256
                and validation.mutation_sha256 == validation.mutation.sha256
                and after_field is not None and after_field.realizations
                and all(s.state() == State.REMOVED for s in after_field.realizations)
                and after.fields.get(key, "").strip()):
            verdict, alarm, reason = Verdict.CANDIDATE_VIOLATION, True, "assertion_after_declared_sources_removed_scope_unknown"
        if not usable_after or contract_id in ("C3", "C4") and not usable_before:
            categories.append("UNDETERMINED_OUTPUT")
        if alarm and contract_id == "C1":
            categories.append("UNSUPPORTED_DECLARED_SOURCES")
            if target is not None:
                matches = normalized(after.fields.get(key, "")) == normalized(target.reference_value)
                diag["full_reference_literal_match"] = matches
                diag["full_reference_comparison_is_not_visible_evidence_proof"] = True
                if not matches:
                    categories.append("VALUE_MISMATCH_REFERENCE")
        elif alarm:
            reading = base.diagnostics.get("reading_status")
            if reading == "omitted":
                categories.append("OMISSION_READABLE_FIELD" if cert_ok and certificate.human_readability_verified
                                  else "OMISSION_DECLARED_SUPPORTED_FIELD")
            elif reading in ("wrong", "precision_overreach", "precision_loss"):
                categories.append("VALUE_MISMATCH_REFERENCE")
            else:
                categories.append("UNDETERMINED_OUTPUT")
        if alarm and cert_ok and validation.status == Validity.VALID:
            inspected = set(certificate.inspected_source_ids)
            needed = {s.source_id for s in (after_field.realizations if after_field else ())}
            common_proof = (certificate.mutation_verified and certificate.semantics_verified
                            and certificate.reference_verified and needed <= inspected)
            if contract_id == "C1":
                confirmed = bool(common_proof and certificate.source_universe_complete and certificate.absence_verified
                                 and after_field and after_field.state() == State.REMOVED)
                if confirmed:
                    categories.append("VERIFIED_ABSENCE_OF_EVIDENCE")
            else:
                # Support-by-construction alone is not evidence that humans can read a retained field.
                confirmed = bool(common_proof and certificate.human_readability_verified)
        if gold_ok and gold.valid_test is True and gold.is_failure is True and alarm:
            # A bound independent failure adjudication is another explicit verification route.
            confirmed = True
        if confirmed:
            verdict = Verdict.CONFIRMED_VIOLATION
        if gold_ok and (gold.valid_test is False or gold.is_failure is False):
            if gold.valid_test is False:
                common["test_validity"] = "INVALID_TEST"
            if alarm:
                categories.append("FALSE_ALARM_MISSING_SOURCE_OR_GT" if gold.false_alarm_cause in (
                    "missing_source", "incorrect_gt", "incorrect_semantic_mapping") else "INDEPENDENTLY_REJECTED_ALARM")
                verdict, reason = Verdict.INCONCLUSIVE, "alarm_rejected_by_independent_adjudication"
            elif gold.valid_test is False:
                verdict, reason = Verdict.INVALID_TEST, "independent_review_rejects_test_validity"
            confirmed = False
    if verdict == Verdict.INCONCLUSIVE and not categories:
        categories.append("UNDETERMINED_OUTPUT")
    diag["certificate_present_but_rejected"] = certificate is not None and not cert_ok
    diag["gold_present_but_rejected"] = gold is not None and not gold_ok
    return Decision(**common, verdict=verdict, alarm_issued=alarm, categories=tuple(categories), reason=reason,
                    diagnostics=diag, behavior_regression_verified=regression_verified,
                    software_fault_confirmed=bool(confirmed and gold_ok and gold.defect_verified()))
