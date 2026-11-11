"""Development-only M2 interventions with the frozen pixel-only CPU reader."""
from dataclasses import asdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import cv2
import numpy as np

from ekyc.module1_quality import image_metrics
from ekyc.module2_homography import Homography
from ..fixtures import backup_fixture, existing_renderer_development
from ..generator import png_bytes
from ..runner import InputRequest, Runner
from ..normalized_output import ReaderSpec
from ..source_graph import normalized, pixel_sha256
from ..task5.pilot import readonly_cached
from ..task55.data import EC, PILOT, ROOT, digest, read, save_new, sha
from .intake import EXECUTION, PRIVATE
from .statistics import rate

LOCAL = PRIVATE / "stage_pilot"
READER = "rapid_v4"
MAX_CALLS = 12


def component_state(component, crop):
    left, top, right, bottom = crop
    xs, ys = zip(*component.geometry)
    if max(xs) < left or min(xs) > right or max(ys) < top or min(ys) > bottom:
        return "clipped"
    if min(xs) >= left and max(xs) <= right and min(ys) >= top and max(ys) <= bottom:
        return "retained"
    return "partial"


def source_states(graph, crop):
    result = {}
    for field in graph.fields:
        sources = {}
        for source in field.realizations:
            states = {c.component_id: component_state(c, crop) for c in source.components if c.required}
            # Component geometry is construction evidence. Preserve existing source condition checks.
            conditions_ok = all(c.satisfied is True for c in source.conditions)
            if source.kind == "mrz":
                by_name = {c.name: c.satisfied for c in source.conditions}
                conditions_ok = conditions_ok and source.checksum_required is True and all(
                    by_name.get(k) is True for k in ("format_valid", "field_checksum", "composite_checksum"))
            status = ("uncertain" if not states or not conditions_ok else "retained" if all(
                v == "retained" for v in states.values()) else "clipped" if "clipped" in states.values() else "partial")
            sources[source.source_id] = dict(status=status, kind=source.kind, components=states)
        states = {s["status"] for s in sources.values()}
        state = ("retained" if "retained" in states else "clipped" if states == {"clipped"} and
                 field.coverage == "complete" else "uncertain")
        result[field.key] = dict(state=state, scope=field.coverage, sources=sources)
    return result


def crop_to_lose(graph, key):
    values = [point[1] for source in graph.field(key).realizations for component in source.components
              if component.role == "value" for point in component.geometry]
    top = math.ceil(max(values)) + 8
    bottom = math.floor(min(values)) - 8
    candidates = [(0, top, graph.width - 1, graph.height - 1), (0, 0, graph.width - 1, bottom)]
    crop = max(candidates, key=lambda x: x[3] - x[1])
    if crop[3] - crop[1] < 80 or crop[1] < 0 or crop[3] >= graph.height:
        raise ValueError("No bounded crop variant for this fixture")
    return crop


def pixel_request(image, requests, role):
    pixel = pixel_sha256(image)
    if pixel not in requests:
        path = LOCAL / "images" / (pixel + ".png")
        with path.open("xb") as stream:
            stream.write(png_bytes(image))
        requests[pixel] = InputRequest(str(path), sha(path), pixel, role, "fictional")
    return pixel


def code_receipt():
    files = (Path(__file__), ROOT / "ekyc/module2_homography.py", ROOT / "ekyc/module1_quality.py",
             EC / "reader_adapters.py", EC / "runner.py")
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in files}


def prepare():
    (LOCAL / "images").mkdir(parents=True, exist_ok=False)
    requests, rows = {}, []
    panel = (backup_fixture(), existing_renderer_development(0), existing_renderer_development(1))
    for i, (card, graph, _, target) in enumerate(panel):
        if graph.data_policy != "fictional" or graph.role not in ("fixture", "development"):
            raise ValueError("Development only")
        h, w = card.shape[:2]
        full = (0, 0, w - 1, h - 1)
        crop = crop_to_lose(graph, target)
        canonical = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
        perspective = np.float32([[60, 62], [w + 24, 21], [w + 66, h + 41], [29, h + 77]])
        matrix = cv2.getPerspectiveTransform(canonical, perspective)
        raw = cv2.warpPerspective(card, matrix, (w + 112, h + 111), flags=cv2.INTER_LINEAR,
                                  borderValue=(82, 90, 95))
        raw_id = pixel_request(raw, requests, graph.role)
        card_id = pixel_request(card, requests, graph.role)
        quality_raw = image_metrics(cv2.cvtColor(raw, cv2.COLOR_RGB2BGR))
        quality_card = image_metrics(cv2.cvtColor(card, cv2.COLOR_RGB2BGR))
        variants = {}
        for name, crop_window in (("rectified", full), ("bad_crop", crop)):
            left, top, right, bottom = crop_window
            quad = np.float32([[[left, top], [right, top], [right, bottom], [left, bottom]]])
            projected = cv2.perspectiveTransform(quad, matrix)[0]
            start = time.perf_counter()
            rectified, meta = Homography().run(cv2.cvtColor(raw, cv2.COLOR_RGB2BGR), corners=projected)
            variant = cv2.cvtColor(rectified, cv2.COLOR_BGR2RGB)
            variants[name] = dict(pixel=pixel_request(variant, requests, graph.role), external_input=raw_id,
                                  m1_quality=quality_raw, m1_mode="diagnostic_only", m2_geometry=meta,
                                  m2_wall_seconds=time.perf_counter() - start, canonical_crop=crop_window,
                                  geometric_source_state=source_states(graph, crop_window))
        full_sources = source_states(graph, full)
        for name, pixel, quality in (("author", card_id, quality_card), ("raw", raw_id, quality_raw)):
            variants[name] = dict(pixel=pixel, external_input=pixel, m1_quality=quality, m1_mode="diagnostic_only",
                                  m2_geometry=dict(method="bypass"), m2_wall_seconds=0., canonical_crop=full,
                                  geometric_source_state=full_sources)
        references = {f.key: f.reference_value for f in graph.fields}
        rows.append(dict(cluster=f"fixture_{i+1}", physical_id_sha256=digest(graph.physical_id),
                         target=target, references=references, variants=variants))
    if len(requests) > MAX_CALLS:
        raise ValueError("Development budget exceeded")
    save_new(LOCAL / "inputs.json", [asdict(requests[k]) for k in sorted(requests)])
    save_new(LOCAL / "analysis.json", rows)
    plan = dict(scope="development_only", confirmatory=False, max_reader_calls=MAX_CALLS, reader=READER,
                reader_spec_sha256=sha(PILOT / READER / (READER + ".spec.json")),
                clusters=len(rows), unique_requests=len(requests), code_sha256=code_receipt(),
                private_manifest_sha256={k: sha(LOCAL / k) for k in ("inputs.json", "analysis.json")})
    save_new(EXECUTION / "ab_development_plan.json", plan)
    return plan


def matches(fields, key, value):
    return normalized(fields.get(key, "")) == normalized(value)


def correctness(fields, reference, keys=None):
    subset = set(reference) if keys is None else set(keys)
    correct = sum(matches(fields, key, reference[key]) for key in subset)
    predicted = sum(bool(value.strip()) for key, value in fields.items() if keys is None or key in subset)
    return dict(correct=correct, predicted=predicted, reference=len(subset), f1=rate(2 * correct, len(subset) + predicted))


def pair_summary(left, right, first, second, reference):
    fields_a, fields_b = first.fields, second.fields
    source_a, source_b = left["geometric_source_state"], right["geometric_source_state"]
    states = {}
    for key, value in reference.items():
        before, after = matches(fields_a, key, value), matches(fields_b, key, value)
        lost = source_a[key]["state"] == "retained" and source_b[key]["state"] == "clipped"
        retained = source_b[key]["state"] == "retained"
        states[key] = dict(before_correct=before, after_correct=after,
                           all_declared_sources_lost=lost, retained_source=retained,
                           explanation=("geometry_loss_at_M2" if lost else "source_retained_error_stage_unresolved"
                                        if retained and not after else "undetermined_or_no_new_error"))
    left_f1, right_f1 = correctness(fields_a, reference)["f1"]["value"], correctness(fields_b, reference)["f1"]["value"]
    return dict(input_same=left["external_input"] == right["external_input"], m2_pixels_changed=left["pixel"] != right["pixel"],
                fields_correct_to_wrong=sum(s["before_correct"] and not s["after_correct"] for s in states.values()),
                fields_wrong_to_correct=sum(not s["before_correct"] and s["after_correct"] for s in states.values()),
                f1_only_delta=right_f1 - left_f1 if right_f1 is not None and left_f1 is not None else None,
                raw_field_difference_keys=sorted(k for k in fields_a.keys() | fields_b.keys() if fields_a.get(k) != fields_b.get(k)),
                first_observed_boundary=("M2_pixels" if left["external_input"] == right["external_input"]
                                         and left["pixel"] != right["pixel"] else "input_or_no_stage_change"),
                fields=states)


def examine(outputs, cases):
    traces = []
    for case in cases:
        refs, variants = case["references"], case["variants"]
        trace = {}
        for name, view in variants.items():
            output = outputs[view["pixel"]]
            visible = [key for key, src in view["geometric_source_state"].items() if src["state"] == "retained"]
            trace[name] = dict(**view, m3_call_id=output.call_id, m3_output_digest=digest(output.fields),
                               m3_reader_seconds=output.latency_seconds, output_usable=output.json_validity["usable_for_contracts"],
                               end_to_end=correctness(output.fields, refs),
                               retained_field_exact=correctness(output.fields, refs, visible),
                               visible_reference_errors=sum(not matches(output.fields, k, refs[k]) for k in visible),
                               output_fields_count=len(output.fields))
        contrasts = {left + "_vs_" + right: pair_summary(
            variants[left], variants[right], outputs[variants[left]["pixel"]], outputs[variants[right]["pixel"]], refs)
                     for left, right in (("raw", "rectified"), ("rectified", "bad_crop"))}
        traces.append(dict(cluster=case["cluster"], target=case["target"], stages=trace, contrasts=contrasts))
    return traces


def run(*, replay=False):
    from ..reader_adapters import specification, load_predictor
    from ..task5.resources import ResourceMonitor
    plan = read(EXECUTION / "ab_development_plan.json")
    if plan["scope"] != "development_only" or plan["code_sha256"] != code_receipt():
        raise ValueError("Changed development intervention plan/code")
    for filename, expected in plan["private_manifest_sha256"].items():
        if sha(LOCAL / filename) != expected:
            raise ValueError("Changed stage pilot manifest")
    spec_path = PILOT / READER / (READER + ".spec.json")
    if sha(spec_path) != plan["reader_spec_sha256"]:
        raise ValueError("Changed pinned reader spec")
    spec = ReaderSpec(**read(spec_path))
    if not replay and specification(READER) != spec:
        raise ValueError("Frozen CPU runtime differs. No new calls were made.")
    stores = [PILOT / READER, EC / "local/smoke_02" / READER]
    history = [Runner(spec, path) for path in stores
               if (path / (READER + ".spec.json")).is_file() and read(path / (READER + ".spec.json")) == spec.to_dict()]
    old_hashes = {str(r.events.path): sha(r.events.path) for r in history}
    runner = Runner(spec, LOCAL / READER, None if replay else load_predictor)
    requests = [InputRequest(**item) for item in read(LOCAL / "inputs.json")]
    if any(r.role not in ("fixture", "development") or r.data_policy != "fictional" for r in requests):
        raise ValueError("Stage pilot request policy")
    prior = len(runner.events.read())
    monitor = ResourceMonitor(gpu=False).start()
    outputs, provenance = {}, []
    try:
        for request in requests:
            result = None
            for old in history:
                cached = readonly_cached(old, request)
                if cached is None:
                    continue
                key = old.key(request)
                envelope = read(old.store / "raw" / (key + ".json"))
                completed = [e for e in old.events.read() if e["event"] in ("inference_completed", "inference_recovered")
                             and e.get("call_id") == cached.call_id and e.get("payload_sha256") == envelope["payload_sha256"]]
                if len(completed) != 1:
                    raise ValueError("Historical cache lacks exact completion binding")
                result = cached
                break
            if result is None:
                key = runner.key(request)
                if not (runner.store / "raw" / (key + ".json")).is_file() and sum(
                        e["event"] == "inference_begin" for e in runner.events.read()) >= plan["max_reader_calls"]:
                    raise RuntimeError("Development call cap reached")
                result = runner.infer(request, replay=replay)
                origin = result.access_mode
            else:
                origin = "historical_cache"
            outputs[request.pixel_sha256] = result
            provenance.append(dict(pixel=request.pixel_sha256, origin=origin, call_id=result.call_id))
    finally:
        resources = monitor.finish()
    if any(sha(path) != expected for path, expected in old_hashes.items()):
        raise ValueError("Historical event log changed")
    events = runner.events.read()
    cases = examine(outputs, read(LOCAL / "analysis.json"))
    report = dict(mode="replay" if replay else "execute", scope="development_only",
                  reader=READER, provenance=provenance, cases=cases,
                  model_calls=sum(e["event"] == "inference_begin" for e in events[prior:]),
                  prior_and_current_calls=sum(e["event"] == "inference_begin" for e in events),
                  new_gpu_calls=0, human_labels=0, historical_cache_read_only=True,
                  stats={key: value for key, value in resources.items() if key not in ("samples", "gpu_samples")},
                  content_digest=digest(cases), test_set_opened=False)
    save_new(EXECUTION / ("ab_replay.json" if replay else "ab_execute.json"), report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "execute", "replay"))
    args = parser.parse_args()
    result = prepare() if args.action == "prepare" else run(replay=args.action == "replay")
    print(json.dumps({k: result[k] for k in ("mode", "model_calls", "content_digest", "unique_requests") if k in result}),
          flush=True)
