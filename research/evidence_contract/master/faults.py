"""Controlled M1–M7 interventions on a transparent fictional pipeline."""
from collections import Counter
import json
import time

import numpy as np

from .. import generator
from ..fixtures import backup_fixture, shared_context_fixture
from ..source_graph import pixel_sha256
from ..task5 import baselines as b
from ..task55.data import digest, save_new, sha
from ..tests.test_runner_oracle import output
from .intake import EXECUTION
from .statistics import rate


def probe(original, observed, component, dx=0, dy=0, fill=(0, 0, 0)):
    """Independent pixel slice for the authored rectangular fixture, no graph scorer."""
    q = np.asarray(component.geometry)
    x, y = np.floor(q.min(axis=0)).astype(int)
    right, bottom = np.ceil(q.max(axis=0)).astype(int)
    region = original[y:bottom, x:right]
    ink = np.all(region < 70, axis=2)
    if not ink.any():
        raise ValueError("Expected authored ink in fixture")
    if right + dx > observed.shape[1] or bottom + dy > observed.shape[0]:
        return "outside_crop"
    after = observed[y + dy:bottom + dy, x + dx:right + dx]
    if np.array_equal(region, after):
        return "preserved"
    if np.all(after[ink] == fill):
        return "erased"
    return "changed_or_partial"


def inspect_sources(pair, image=None):
    image = pair.followup if image is None else image
    dx, dy = (int(pair.mutation.homography[i][2]) for i in range(2))
    return {f.key: {s.source_id: {c.role: probe(pair.original, image, c, dx, dy, pair.mutation.fill)
                                for c in s.components if c.required} for s in f.realizations}
            for f in pair.graph.fields}


def visible_sources(probes):
    return {key: sorted(sid for sid, components in sources.items()
                        if components and all(value == "preserved" for value in components.values()))
            for key, sources in probes.items()}


def constructed_reading(references, sources):
    return {key: references[key] for key, available in sources.items() if available}


def strict_json_object(text):
    def pairs(items):
        values = dict(items)
        if len(values) != len(items):
            raise ValueError("duplicate output key")
        return values

    try:
        value = json.loads(text, object_pairs_hook=pairs)
    except (ValueError, TypeError):
        return False
    return isinstance(value, dict) and all(isinstance(v, str) for v in value.values())


def run_case(case, pair, *, fault="none"):
    start = time.perf_counter()
    if pair.graph.role != "fixture" or pair.graph.data_policy != "fictional":
        raise ValueError("Controlled pipeline only permits fictional fixture inputs")
    key = pair.mutation.target_key
    retained = pair.mutation.retained_key or key
    author = {f.key: f.reference_value for f in pair.graph.fields}
    probes = inspect_sources(pair)
    available = visible_sources(probes)
    intended = constructed_reading(author, available)
    # Independent eligibility decisions for the finite panel.
    valid = not (case == "M3_context_erased")
    if not valid:
        assert any(values.get("semantic_context") == "erased" and values.get("value") == "preserved"
                   for values in probes[retained].values())
    if pair.mutation.contract_id == "C1":
        assert not available[key]
    if pair.mutation.contract_id == "C2":
        assert available[key] and "body/a" not in available[key]
    if pair.mutation.contract_id == "C3" and valid:
        assert not available[key] and available[retained]

    stage2 = pair.followup
    observed_sources = available
    observed = dict(intended)
    trace_stage = None
    if fault == "body_only" and available[key] and "body/a" not in available[key]:
        observed.pop(key)
        trace_stage = "M3_reader_router"
    if fault == "stale_field" and key not in observed:
        observed[key] = author[key]
        trace_stage = "KIE"
    if fault == "coupled_field" and valid and not available[key]:
        observed.pop(retained)
        trace_stage = "KIE"
    if fault == "crop_loses_B":
        dy = int(pair.mutation.homography[1][2])
        stage2 = pair.followup[:170 + dy]
        observed_sources = visible_sources(inspect_sources(pair, stage2))
        assert available[retained] and not observed_sources[retained]
        observed = constructed_reading(author, observed_sources)
        trace_stage = "M2"
    if fault == "semantic_swap":
        other = next(k for k in intended if k != retained)
        observed[retained] = intended[other]
        trace_stage = "KIE"
    if fault == "noop_crop":
        stage2 = pair.followup.copy()
        trace_stage = "M2"

    attribution = {field: ids[0] for field, ids in observed_sources.items() if ids and field in observed}
    reference_attribution = dict(attribution)
    if fault == "stale_attribution":
        attribution[key] = "body/a"
        trace_stage = "Attribution"
    raw = json.dumps(observed, ensure_ascii=False)
    if fault == "broken_json":
        raw = '{"school":'
        trace_stage = "Serialization"
    if fault == "equivalent_json":
        raw = json.dumps(observed, ensure_ascii=False, indent=2)
        trace_stage = "Serialization"
    format_error = not strict_json_object(raw)
    attribution_error = any(sid not in observed_sources.get(field, ()) for field, sid in attribution.items())
    field_change = observed != intended
    observable = field_change or format_error or attribution_error or pixel_sha256(stage2) != pixel_sha256(pair.followup)
    independently_faulty = valid and (field_change or format_error or attribution_error)
    first = output(author, pair.original)
    after = output(observed, pair.followup, usable_text=raw)
    test_results = b.run_checks(pair.graph, pair.validation, first, after)
    scores = {name: b.unpack(check) for name, check in test_results.items()}
    # Reuse hard-pair evaluation as an aggregate-output comparator.
    from research.hp_metrics import scoring
    sample = dict(target=intended, source_refs={k: [dict(kind="body", value=v)] for k, v in intended.items()}, fields=[])
    hp, _ = scoring(sample, raw)
    attribution_replay = bool(reference_attribution != attribution and attribution_error)
    return dict(case_id=case, family=case.split("_")[0], origin="controlled_fixture_only",
                fault_installed=fault != "none", intervention=fault, fault_activated=trace_stage is not None,
                activation_stage=trace_stage, independently_valid=valid, observable_effect=observable,
                normalized_field_changed=field_change, raw_json_changed=raw != json.dumps(intended, ensure_ascii=False),
                attribution_changed=attribution != reference_attribution, independently_faulty=independently_faulty,
                eligibility=("INVALID" if not valid else "ACTIVATED_OBSERVABLE" if independently_faulty else
                             "EQUIVALENT_ON_FIXTURE" if fault != "none" else "NEGATIVE_CONTROL"),
                error_types=[label for yes, label in ((field_change, "FIELD"), (format_error, "JSON"),
                             (attribution_error, "ATTRIBUTION")) if yes],
                before_sha256=pixel_sha256(pair.original), input_sha256=pixel_sha256(pair.followup),
                intended_m2_sha256=pixel_sha256(pair.followup), observed_m2_sha256=pixel_sha256(stage2),
                expected_field_digest=digest(intended), observed_field_digest=digest(observed),
                output_sha256=digest(raw), source_probes=probes, expected_visible_sources=available,
                observed_visible_sources=observed_sources,
                contract=pair.mutation.contract_id, checked_key=retained,
                methods={**{m: {"alarm": row["alarm"], "verdict": row["verdict"], "reason": row["reason"]}
                             for m, row in scores.items()}, "JSON_SCHEMA": {"alarm": format_error},
                         "FLAT_ATTRIBUTION": {"alarm": attribution_replay}},
                hard_pair_field_counters={k: v for k, v in hp.items() if isinstance(v, (int, float, bool))},
                wall_seconds=time.perf_counter() - start)


def experiments():
    im, graph, a, neighbor = backup_fixture()

    def make(kind, key=a, retained=None):
        return generator.generate(im, graph, generator.plan(graph, kind, target_key=key, retained_key=retained))

    m1 = make("single_source_mask")
    m2 = make("all_sources_mask")
    m3 = make("pair_a_mask", retained=neighbor)
    m4 = make("geometry_translate", key=neighbor)
    pic, context, target, kept = shared_context_fixture()
    invalid = generator.generate(pic, context, generator.plan(context, "pair_a_mask", target_key=target, retained_key=kept))
    cases = [
        ("M1_backup_correct", m1, "none"), ("M1_ignore_backup", m1, "body_only"),
        ("M2_clean_refusal", m2, "none"), ("M2_stale_assertion", m2, "stale_field"),
        ("M3_keep_neighbor", m3, "none"), ("M3_drop_neighbor", m3, "coupled_field"),
        ("M3_context_erased", invalid, "none"),
        ("M4_crop_loses_neighbor", m4, "crop_loses_B"), ("M4_noop", m4, "noop_crop"),
        ("M5_wrong_semantic_key", m4, "semantic_swap"),
        ("M6_claim_removed_source", m1, "stale_attribution"), ("M6_correct_source", m1, "none"),
        ("M7_unparseable", m4, "broken_json"), ("M7_format_only", m4, "equivalent_json"),
    ]
    return [run_case(name, pair, fault=fault) for name, pair, fault in cases]


def summarize(cases):
    eligible = [c for c in cases if c["fault_installed"] and c["fault_activated"] and c["independently_faulty"]]
    structured = [c for c in eligible if c["error_types"] == ["FIELD"]]
    methods = ("A", "B3", "B3_V3_gate", "A_flat", "B2", "JSON_SCHEMA", "FLAT_ATTRIBUTION")
    report = {}
    for method in methods:
        alarms = [c for c in cases if c["methods"][method]["alarm"]]
        report[method] = dict(alarms=len(alarms), mutation_score_all_interfaces=rate(
            sum(c["methods"][method]["alarm"] for c in eligible), len(eligible)),
            structured_field_mutation_score=rate(sum(c["methods"][method]["alarm"] for c in structured), len(structured)),
            detected_families=sorted({c["family"] for c in eligible if c["methods"][method]["alarm"]}),
            invalid_alarms=sum(not c["independently_valid"] for c in alarms))
    return dict(records=len(cases), family_counts=dict(Counter(c["family"] for c in cases)),
                status_counts=dict(Counter(c["eligibility"] for c in cases)),
                valid_test_rate=rate(sum(c["independently_valid"] for c in cases), len(cases)),
                installed=sum(c["fault_installed"] for c in cases), activated=sum(c["fault_activated"] for c in cases),
                independently_faulty=len(eligible), structured_field_faults=len(structured),
                results=report, model_calls=0, human_labels=0, natural_model_errors=0)


if __name__ == "__main__":
    cases = experiments()
    report = summarize(cases)
    save_new(EXECUTION / "controlled_faults.json", dict(**report, code_sha256=sha(__file__), cases=cases))
    print(json.dumps(report), flush=True)
