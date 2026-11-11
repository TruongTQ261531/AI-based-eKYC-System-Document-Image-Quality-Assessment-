"""Matched-output testing baselines. None of these functions invokes a reader.

B0 evaluates outputs; B1 is a selector in planning.py; B2 is a graph-blind
relation oracle; B3 includes both the actual frozen V3 scorer and a strong
flat-source-availability checker. They are not asserted to share one objective.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import itertools
from pathlib import Path

from .. import contracts, oracle
from ..source_graph import State, digest, normalized
from ..validity import Validity

POLICY = contracts.Policy()


@dataclass(frozen=True)
class Check:
    method: str
    contract_id: str
    key: str
    verdict: str
    alarm: bool
    category: str
    reason: str
    source_information: str
    raw_test_validity: str
    confirmed: bool = False

    def to_dict(self):
        return asdict(self)


def key_for(report):
    mutation = report.mutation
    return (mutation.retained_key if mutation.contract_id == "C3" else mutation.target_key) or mutation.target_key


def _check(method, report, verdict, category="", reason="", source_information="none"):
    return Check(method, report.mutation.contract_id, key_for(report), verdict,
                 verdict in ("CANDIDATE_VIOLATION", "CONFIRMED_VIOLATION"), category, reason,
                 source_information, report.status.value)


def _gate(method, report, before, after, *, gate=True, before_required=False):
    if (before.input_pixel_sha256 != report.before_pixel_sha256
            or after.input_pixel_sha256 != report.after_pixel_sha256
            or before.reader_fingerprint != after.reader_fingerprint):
        return _check(method, report, "INVALID_TEST", reason="output_binding")
    if gate and report.status != Validity.VALID:
        return _check(method, report, "INVALID_TEST" if report.status == Validity.INVALID_TEST else "INCONCLUSIVE",
                      reason="common_mutation_gate")
    if not after.json_validity["usable_for_contracts"] or before_required and not before.json_validity["usable_for_contracts"]:
        return _check(method, report, "INCONCLUSIVE", reason="unusable_structured_output")
    return None


def conventional(graph, report, before, after, *, gate=True):
    """B0 full-reference per-key checks; same normalization as A, no new-fault claim."""
    method = "B0_full_reference" if gate else "B0_full_reference_raw"
    blocked = _gate(method, report, before, after, gate=gate)
    if blocked:
        return blocked
    field = graph.field(key_for(report))
    reading = contracts.assessment(after.fields, field)
    if reading == "unverified_reference":
        return _check(method, report, "INCONCLUSIVE", reason=reading, source_information="full_reference")
    return _check(method, report, "PASS" if reading == "correct" else "CANDIDATE_VIOLATION",
                  "OMISSION" if reading == "omitted" else "VALUE_MISMATCH" if reading != "correct" else "",
                  "full_reference_result_evaluation_not_fault_discovery", "full_reference")


def source_agnostic(contract_id, target_key, retained_key, operator, before, after, *,
                    validity="VALID", gate=True, method="B2_source_agnostic"):
    """Graph-free relation interface: only nominal mutation keys, outputs and gate.

    Masked target absent, retained key invariant, padding translation invariant.
    Global invariance is deliberately not imposed on fields intentionally masked.
    A common external gate is an information-matched control, not graph-free generation.
    """
    key = retained_key if contract_id == "C3" else target_key
    def result(verdict, category="", reason=""):
        return Check(method, contract_id, key, verdict, verdict == "CANDIDATE_VIOLATION",
                     category, reason, "no_graph_or_reference_in_relation", validity)
    if gate and validity != "VALID":
        return result("INVALID_TEST" if validity == "INVALID_TEST" else "INCONCLUSIVE", reason="common_mutation_gate")
    if before.reader_fingerprint != after.reader_fingerprint:
        return result("INVALID_TEST", reason="reader_binding")
    if not after.json_validity["usable_for_contracts"] or contract_id in ("C3", "C4") and not before.json_validity["usable_for_contracts"]:
        return result("INCONCLUSIVE", reason="unusable_structured_output")
    if contract_id in ("C1", "C2"):
        bad = bool(after.fields.get(key, "").strip())
        return result("CANDIDATE_VIOLATION" if bad else "PASS", "NOMINAL_MASK_REMOVAL" if bad else "",
                      "does_not_model_alternative_sources")
    if contract_id == "C4" and operator not in POLICY.geometry_operators:
        return result("INCONCLUSIVE", reason="operator_policy_not_declared")
    if not before.fields.get(key, "").strip():
        return result("INCONCLUSIVE", reason="no_original_value_for_relation")
    bad = normalized(before.fields[key]) != normalized(after.fields.get(key, ""))
    return result("CANDIDATE_VIOLATION" if bad else "PASS", "OUTPUT_CHANGE" if bad else "",
                  "pairwise_change_not_verified_version_regression")


def b2(report, before, after, *, gate=True):
    mutation = report.mutation
    blocked = _gate("B2_source_agnostic", report, before, after, gate=gate, before_required=mutation.contract_id in ("C3", "C4"))
    if blocked:
        return blocked
    return source_agnostic(mutation.contract_id, mutation.target_key, mutation.retained_key, mutation.operator,
                           before, after, validity=report.status.value, gate=gate)


def visible_reference(graph, report, before, after, *, method="B3_visible_reference"):
    """Strong B3: flat visible availability, typed matching, same common gate.

    It checks the post-image reference without the original-correctness requirement.
    It is intentionally capable of detecting every pointwise error detectable by A.
    """
    blocked = _gate(method, report, before, after)
    if blocked:
        return blocked
    if report.after_graph is None:
        return _check(method, report, "INCONCLUSIVE", reason="no_source_state")
    field = report.after_graph.field(key_for(report))
    if field.state() == State.UNKNOWN:
        return _check(method, report, "INCONCLUSIVE", reason="unknown_reference_or_source_scope")
    if field.state() == State.REMOVED:
        bad = bool(after.fields.get(field.key, "").strip())
        category = "UNSUPPORTED_DECLARED_SOURCES"
    else:
        reading = contracts.assessment(after.fields, field)
        if reading == "unverified_reference":
            return _check(method, report, "INCONCLUSIVE", reason=reading)
        bad = reading != "correct"
        category = "OMISSION" if reading == "omitted" else "VALUE_MISMATCH"
    return _check(method, report, "CANDIDATE_VIOLATION" if bad else "PASS", category if bad else "",
                  "post_image_visible_reference_not_temporal_fault_proof", "flat_visible_reference_and_availability")


def legacy_nodes(graph):
    """Adapt explicit values/regions to frozen V3's existing node schema.

    Legacy V3 has no readability/semantic-context/completeness gate here. This is
    an adapted input schema, not a claim to reproduce its historical dataset run.
    """
    return [dict(key=f.key, value=s.reference_value,
                 kind=s.value_kind if s.value_kind != "text" else "body",
                 author_source=s.kind, priority=i,
                 components=[c.geometry for c in s.components if c.required and c.role == "value"])
            for i, (f, s) in enumerate((f, s) for f in graph.fields for s in f.realizations)]


@lru_cache(maxsize=1)
def legacy_functions():
    # Imported only for replay scoring. No VLM is constructed by these functions.
    from research.v3_sources import visible_realizations
    from research.v3_metrics import score
    return visible_realizations, score


def legacy_v3(graph, report, before, after, *, gate=False):
    method = "B3_legacy_v3_gated" if gate else "B3_legacy_v3"
    blocked = _gate(method, report, before, after, gate=gate)
    if blocked:
        return blocked
    import numpy as np
    visibility, score = legacy_functions()
    mutation = report.mutation
    w, h = mutation.output_size
    refs, _, masked = visibility(legacy_nodes(graph), np.asarray(mutation.homography, float),
                                [np.asarray(q, np.float32) for q in mutation.mask_geometry], w, h)
    key = key_for(report)
    target = {key: refs[key][0]["value"]} if key in refs else {}
    prediction = {key: after.fields[key]} if after.fields.get(key, "").strip() else {}
    sample = dict(source_refs={key: refs[key]} if key in refs else {}, target=target, masked_keys=[key])
    outcome = score(sample, prediction, True)  # The actual unchanged legacy scorer.
    bad = bool(outcome["unsupported_nonempty"] or outcome["visible_omissions"] or outcome["wrong_visible_values"])
    category = "UNSUPPORTED" if outcome["unsupported_nonempty"] else "OMISSION" if outcome["visible_omissions"] else "VALUE_MISMATCH"
    return _check(method, report, "CANDIDATE_VIOLATION" if bad else "PASS", category if bad else "",
                  "frozen_v3_geometry_visible_refs_and_precision_scorer", "legacy_OR_sources_geometry_visibility")


def proposed(graph, report, before, after):
    return oracle.evaluate(graph, report, before, after)


def flat_contract(graph, report, before, after):
    """Representation ablation: no explicit graph in the relation checker.

    Upstream availability/typed reference/validity are deliberately retained.
    Therefore this tests graph representation at the oracle boundary, not the
    cost or necessity of collecting source information upstream.
    """
    base = visible_reference(graph, report, before, after, method="A_flat_oracle")
    if base.verdict in ("INVALID_TEST", "INCONCLUSIVE"):
        return base
    contract_id = report.mutation.contract_id
    if contract_id == "C4" and report.mutation.operator not in POLICY.geometry_operators:
        return _check("A_flat_oracle", report, "INCONCLUSIVE", reason="operator_policy_not_declared")
    if contract_id in ("C3", "C4"):
        field = (report.reference_before_graph or graph).field(key_for(report))
        if not before.json_validity["usable_for_contracts"] or contracts.assessment(before.fields, field) != "correct":
            return _check("A_flat_oracle", report, "INCONCLUSIVE", reason="original_already_wrong_or_unverified")
    return base


def no_alternative(graph, report, before, after):
    if report.mutation.contract_id != "C2":
        return proposed(graph, report, before, after)
    return replace(b2(report, before, after), method="A_no_alternative", reason="only_C2_backup_handling_removed")


def nominal_report(graph, report):
    """Replace the validator with an intent-only state updater, not pixel proof.

    Assumes named sources removed and all others preserved. This intentionally
    cannot establish collateral-context preservation or complete actual erasure.
    """
    from ..validity import project
    import numpy as np
    hidden = set(report.mutation.hidden_source_ids)
    matrix = np.asarray(report.mutation.homography, float)
    fields = []
    for field in graph.fields:
        sources = []
        for source in field.realizations:
            components = []
            for component in source.components:
                components.append(replace(component, availability="removed") if source.source_id in hidden else
                    replace(component, geometry=project(component.geometry, matrix),
                            glyphs=tuple(project(g, matrix) for g in component.glyphs)))
            sources.append(replace(source, components=tuple(components)))
        fields.append(replace(field, realizations=tuple(sources)))
    w, h = report.mutation.output_size
    after = replace(graph, width=w, height=h, input_pixel_sha256=report.after_pixel_sha256,
                    input_file_sha256=None, fields=tuple(fields))
    return replace(report, status=Validity.VALID, reasons=(), after_graph=after,
                   measurements=dict(intent_only_not_validation=True), review_required=(), reference_before_graph=graph)


def no_validator(graph, report, before, after):
    result = proposed(graph, nominal_report(graph, report), before, after)
    return replace(result, test_validity="UNCHECKED", mutation_validity=report.status.value)


def run_checks(graph, report, before, after):
    """One fixed execution pack for all oracle comparisons/ablations."""
    a = proposed(graph, report, before, after)
    result = {"A": a, "B0": conventional(graph, report, before, after),
              "B2": b2(report, before, after),
              "B3": visible_reference(graph, report, before, after),
              "B3_V3": legacy_v3(graph, report, before, after),
              "B3_V3_gate": legacy_v3(graph, report, before, after, gate=True),
              "A_flat": flat_contract(graph, report, before, after),
              "A_no_alternative": no_alternative(graph, report, before, after),
              "A_no_validator": no_validator(graph, report, before, after)}
    if report.mutation.contract_id == "C3":
        result["A_no_NI"] = _check("A_no_NI", report, "INCONCLUSIVE", reason="C3_disabled")
    else:
        result["A_no_NI"] = a
    return result


def unpack(value):
    if isinstance(value, oracle.Decision):
        return dict(verdict=value.verdict.value, alarm=value.alarm_issued,
                    categories=list(value.categories), reason=value.reason,
                    confirmed=value.verdict == oracle.Verdict.CONFIRMED_VIOLATION,
                    fault=value.software_fault_confirmed)
    return dict(verdict=value.verdict, alarm=value.alarm, categories=[value.category] if value.category else [],
                reason=value.reason, confirmed=value.confirmed, fault=False)
