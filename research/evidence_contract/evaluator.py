"""Replay-only metrics with explicit units, scopes and unknown denominators."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import unicodedata

from .contracts import assessment
from .source_graph import State, digest
from .oracle import Verdict


def rate(numerator, denominator, scale=1):
    return dict(value=scale * numerator / denominator if denominator else None,
                numerator=numerator, denominator=denominator, scale=scale)


def text_norm(value):
    """Literal metric: NFC, whitespace collapse, case-sensitive; no aliases/century guessing."""
    return " ".join(unicodedata.normalize("NFC", value).split())


def distance(left, right):
    previous = list(range(len(right) + 1))
    for i, a in enumerate(left, 1):
        current = [i]
        for j, b in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b)))
        previous = current
    return previous[-1]


@dataclass(frozen=True)
class FieldObservation:
    reader_id: str
    reader_fingerprint: str
    output_origin: str
    call_id: str
    pixel_sha256: str
    physical_id_hash: str
    document_group: str
    source_kinds: tuple[str, ...]
    readability: str
    key: str
    state: str
    reference_basis: str
    parse_usable: bool
    strict_json_valid: bool
    predicted_present: bool
    exact_match: bool | None
    semantic_match: bool | None
    character_edits: int | None
    reference_characters: int | None
    unjudged_prediction_keys: tuple[str, ...]
    latency_seconds: float


def observe_fields(graph, output):
    """Join reference AFTER prediction. No model call and no default required CCCD fields.

    This records declared-support accuracy, not independent human OCR ground truth.
    Fields outside the annotated universe remain unjudged, never automatic FP.
    """
    if graph.input_pixel_sha256 != output.input_pixel_sha256:
        raise ValueError("Field reference is not bound to this output image")
    usable = output.json_validity["usable_for_contracts"]
    predicted = output.fields if usable else {}
    unjudged = tuple(sorted(set(predicted) - {f.key for f in graph.fields}))
    rows = []
    for field in graph.fields:
        supported = field.supported_sources()
        state = field.state()
        components = [c for s in supported for c in s.components if c.required]
        readability = "human_verified" if components and all(
            c.evidence_basis == "human_verified" and c.readability == "readable" for c in components) else (
                "construction_support_only" if components else "unknown_or_removed")
        reference = None
        if state == State.SUPPORTED:
            # Visible precision comes from supported sources, not inaccessible full reference.
            chosen = sorted(supported, key=lambda s: (s.value_kind != "date_full", s.source_id))[0]
            reference = chosen.reference_value
        predicted_value = predicted.get(field.key, "")
        present = bool(predicted_value.strip())
        exact = text_norm(predicted_value) == text_norm(reference) if reference is not None else None
        semantic = assessment(predicted, field) == "correct" if reference is not None else None
        rows.append(FieldObservation(output.reader_id, output.reader_fingerprint, output.output_origin,
            output.call_id, output.input_pixel_sha256, digest(graph.physical_id), graph.source_id,
            tuple(sorted({s.kind for s in field.realizations})), readability, field.key, state.value,
            "declared_source_reference_not_independent_readability", usable,
            output.json_validity["strict_json_valid"], present, exact, semantic,
            distance(text_norm(reference), text_norm(predicted_value)) if reference is not None else None,
            len(text_norm(reference)) if reference is not None else None, unjudged, output.latency_seconds))
    return rows


def missing_fields(graph, output):
    """Scoring-side enrichment; never fed back to reader/prompt/cache key."""
    if graph.input_pixel_sha256 != output.input_pixel_sha256:
        raise ValueError("Reference image mismatch")
    if not output.json_validity["usable_for_contracts"]:
        return dict(missing_fields=None, basis="unknown_due_to_unusable_output")
    return dict(missing_fields=[f.key for f in graph.fields if f.state() == State.SUPPORTED
                               and not output.fields.get(f.key, "").strip()],
                basis="post_inference_declared_supported_fields_only")


def _unique(rows, key):
    result = {}
    for row in rows:
        identity = key(row)
        if identity in result and result[identity] != row:
            raise ValueError("Conflicting duplicate evaluation unit; audit annotations before aggregating")
        result[identity] = row
    return list(result.values())


def budget(events, *, call_ids=None, readers=None, new_run_ids=None, process_runs=None):
    actual = [e for e in events if e.get("output_origin") == "actual_model"]
    if readers is not None:
        actual = [e for e in actual if e.get("reader_id") in readers]
    if call_ids is not None:
        actual = [e for e in actual if e.get("call_id") in call_ids or e["event"].startswith("model_load_")]
    starts = {e["call_id"]: e for e in actual if e["event"] == "inference_begin"}
    complete = {e["call_id"]: e for e in actual if e["event"] in ("inference_completed", "inference_recovered")}
    failed = {e["call_id"]: e for e in actual if e["event"] == "inference_failed"}
    ambiguous = set(starts) - set(complete) - set(failed)
    terminal = {**failed, **complete}
    elapsed = sum(e.get("elapsed_seconds", 0.) for cid, e in terminal.items() if cid in starts)
    load_seconds = sum(e.get("elapsed_seconds", 0.) for e in actual if e["event"] in (
        "model_load_completed", "model_load_failed"))
    processes = None if process_runs is None else [p for p in process_runs
        if p["mode"] == "fresh" and (readers is None or p["reader"] in readers)]
    return dict(image_reader_invocations=len(starts), completed=len(set(starts) & set(complete)),
                failed=len(set(starts) & set(failed)), ambiguous=len(ambiguous),
                originating_unique_input_reader_pairs=len({(e["input_pixel_sha256"], e["reader_fingerprint"])
                                                           for e in starts.values()}),
                new_image_reader_invocations=None if new_run_ids is None else sum(
                    e.get("run_id") in new_run_ids for e in starts.values()),
                invocation_wrapper_seconds=elapsed, cold_load_seconds=load_seconds,
                cold_inclusive_seconds=elapsed + load_seconds,
                worker_process_seconds=None if processes is None else sum(p["elapsed_seconds"] for p in processes),
                worker_process_cost_scope="fresh workers incl. interpreter/import/preflight/loading/inference/cache I/O; excludes separate fixture construction and scoring",
                runtime_complete=not ambiguous and all("elapsed_seconds" in terminal[cid] for cid in starts),
                neural_internal_forward_passes=None,
                inference_unit="one pixels-only predictor invocation; internal detector/recognizer/token forwards uncounted")


def _core(decisions, fields, execution_budget):
    alarms = [d for d in decisions if d.alarm_issued]
    def adjudicated(d):
        return bool(d.gold and (d.gold['valid_test'] is False or d.gold['is_failure'] is False
                                or d.gold['valid_test'] is True and d.gold['is_failure'] is True))
    labelled = [d for d in decisions if adjudicated(d)]
    labelled_alarms = [d for d in labelled if d.alarm_issued]
    tp = sum(d.gold["is_failure"] is True and d.gold["valid_test"] is True for d in labelled_alarms)
    fp = sum(d.gold["is_failure"] is False or d.gold["valid_test"] is False for d in labelled_alarms)
    known_pos = [d for d in labelled if d.gold["is_failure"] is True and d.gold["valid_test"] is True]
    known_neg = [d for d in labelled if d.gold["is_failure"] is False and d.gold["valid_test"] is True]
    invalid_labels = [d for d in decisions if d.gold and d.gold["valid_test"] is False]
    verified = [d for d in decisions if d.verdict == Verdict.CONFIRMED_VIOLATION]
    failure_clusters = {d.gold.get("verified_failure_cluster") if d.gold and d.gold.get("verified_failure_cluster") else
                        digest([d.physical_id_hash, d.contract_id, d.key, d.categories, d.reader_fingerprint])
                        for d in verified}
    defects = {d.gold["defect_id"] for d in verified if d.software_fault_confirmed and d.gold}
    refs = [f for f in fields if f.state == "SUPPORTED"]
    removed = [f for f in fields if f.state == "REMOVED"]
    correct = sum(f.exact_match is True for f in refs)
    field_fn = len(refs) - correct
    field_fp = sum(f.predicted_present and not f.exact_match for f in refs) + sum(f.predicted_present for f in removed)
    chars = sum(f.reference_characters or 0 for f in refs)
    edits = sum(f.character_edits or 0 for f in refs)
    valid_conditional = [f for f in refs if f.parse_usable]
    views = _unique(fields, lambda f: (f.pixel_sha256, f.reader_fingerprint, f.key))
    parsed_views = {(f.pixel_sha256, f.reader_fingerprint): f.parse_usable for f in views}
    strict_views = {(f.pixel_sha256, f.reader_fingerprint): f.strict_json_valid for f in views}
    unjudged = {(f.pixel_sha256, f.reader_fingerprint, k) for f in fields for k in f.unjudged_prediction_keys}
    calls = execution_budget["image_reader_invocations"]
    seconds = execution_budget["cold_inclusive_seconds"] if execution_budget["runtime_complete"] else 0
    worker_seconds = execution_budget["worker_process_seconds"] or 0
    metrics = dict(
        contract_evaluations=len(decisions), alarm_count=len(alarms), verified_failure_count=len(verified),
        unique_behavior_failure_clusters=len(failure_clusters), confirmed_software_defects=len(defects),
        candidate_violation_count=sum(d.verdict == Verdict.CANDIDATE_VIOLATION for d in decisions),
        verdict_counts=dict(Counter(d.verdict.value for d in decisions)),
        alarm_precision=rate(tp, tp + fp),
        alarm_recall=rate(sum(d.alarm_issued for d in known_pos), len(known_pos)),
        false_alarm_rate_valid_known_negatives=rate(sum(d.alarm_issued for d in known_neg), len(known_neg)),
        invalid_test_alarm_rate=rate(sum(d.alarm_issued for d in invalid_labels), len(invalid_labels)),
        alarm_label_coverage=rate(len(labelled_alarms), len(alarms)),
        failure_label_coverage=rate(len(labelled), len(decisions)),
        unlabelled_alarms=sum(not adjudicated(d) for d in alarms),
        valid_test_rate=rate(sum(d.test_validity == "VALID" for d in decisions), len(decisions)),
        inconclusive_rate=rate(sum(d.verdict == Verdict.INCONCLUSIVE for d in decisions), len(decisions)),
        errors_detected_per_100_originating_calls=rate(len(verified), calls, 100),
        verified_behavior_clusters_per_100_originating_calls=rate(len(failure_clusters), calls, 100),
        verified_defects_per_100_originating_calls=rate(len(defects), calls, 100),
        verified_defects_per_cold_inclusive_second=rate(len(defects), seconds),
        verified_defects_per_worker_process_second=rate(len(defects), worker_seconds),
        field_exact_match=rate(correct, len(refs)),
        field_semantic_match=rate(sum(f.semantic_match is True for f in refs), len(refs)),
        field_precision=rate(correct, correct + field_fp), field_recall=rate(correct, correct + field_fn),
        field_f1=rate(2 * correct, 2 * correct + field_fp + field_fn),
        field_cer=rate(edits, chars),
        field_exact_match_conditional_on_usable_output=rate(sum(f.exact_match is True for f in valid_conditional), len(valid_conditional)),
        strict_json_valid_rate=rate(sum(strict_views.values()), len(strict_views)),
        usable_output_rate=rate(sum(parsed_views.values()), len(parsed_views)),
        supported_reference_fields=len(refs), known_removed_fields=len(removed),
        unjudged_reference_fields=sum(f.state == "UNKNOWN" for f in fields),
        unjudged_predicted_key_view_count=len(unjudged),
        missing_supported_fields=sum(not f.predicted_present for f in refs if f.parse_usable),
        unusable_output_reference_fields=sum(not f.parse_usable for f in refs),
        unit_counts=dict(physical_ids=len({d.physical_id_hash for d in decisions} | {f.physical_id_hash for f in fields}),
                        unique_pixel_images=len({f.pixel_sha256 for f in fields}),
                        unique_image_reader_views=len(parsed_views),
                        unique_field_reader_views=len(fields),
                        generated_pairs=len({d.pair_id for d in decisions})),
        budget=execution_budget,
    )
    return metrics


def summarize(decisions, fields, events, *, new_run_ids=None, include_groups=True, process_runs=None):
    """Actual model results only; injected fixtures remain a separate test artifact."""
    injected_d = sum(d.output_origin != "actual_model" for d in decisions)
    injected_f = sum(f.output_origin != "actual_model" for f in fields)
    decisions = _unique([d for d in decisions if d.output_origin == "actual_model"], lambda d: d.decision_sha256)
    fields = _unique([f for f in fields if f.output_origin == "actual_model"],
                     lambda f: (f.pixel_sha256, f.reader_fingerprint, f.key))
    report = _core(decisions, fields, budget(events, new_run_ids=new_run_ids, process_runs=process_runs))
    report.update(schema="contract-evaluation/1", injected_decisions_excluded=injected_d,
                  injected_field_observations_excluded=injected_f,
                  accuracy_scope="declared source references; construction support is not human readability",
                  unjudged_key_policy="outside annotated semantic field universe; not counted as false positives",
                  failure_cluster_policy="behavior fingerprint or independently adjudicated cluster, not a software bug ID")
    pair_validity = defaultdict(set)
    for d in decisions:
        pair_validity[d.pair_id].add(d.mutation_validity)
    if any(len(values) != 1 for values in pair_validity.values()):
        raise ValueError("Model-dependent mutation validity is forbidden")
    report["generated_pair_valid_rate"] = rate(sum("VALID" in values for values in pair_validity.values()), len(pair_validity))
    if include_groups:
        groups = {}
        for dimension, getter in (
            ("contract", lambda d: [d.contract_id]), ("model", lambda d: [d.reader_id]),
            ("source", lambda d: list(d.source_kinds) or ["unknown"]),
            ("readability", lambda d: [d.readability]), ("document_group", lambda d: [d.document_group])):
            buckets = defaultdict(list)
            for d in decisions:
                for value in getter(d):
                    buckets[value].append(d)
            groups[dimension] = {}
            for value, subset in sorted(buckets.items()):
                ids = {x for d in subset for x in (d.before_call_id, d.after_call_id)}
                subset_fields = [f for f in fields if f.call_id in ids]
                subset_budget = budget(events, call_ids=ids, readers={d.reader_id for d in subset},
                                       new_run_ids=new_run_ids, process_runs=process_runs)
                groups[dimension][value] = _core(subset, subset_fields, subset_budget)
        report["groups"] = groups
        report["group_scope"] = "Source/contract/readability groups overlap; field/call totals are non-additive. Cold load charged to each relevant model group."
    return report
