"""Reproducible Module 2 diagnostics; no Module 1 gate or model downloads.

Synthetic metrics measure recovery of injected image boundaries, NOT accuracy on
real photographed documents. Real captures require human/MIDV corner annotations
for geometric accuracy; successful return alone is never called correct.

python scripts/evaluate_module2.py --mode synthetic --split val --baseline PATH
python scripts/evaluate_module2.py --mode real --split test --per-label 8

Optional annotations JSON: {"relative/image/path.tif": [[x,y], ... four points]}.
Coordinates are pixels in the decoded ORIGINAL image, not thumbnails.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ekyc.io import StageError, read_image, write_image, write_json
from ekyc.module2_homography import Homography

LABELS = ("Clean", "Blur", "Cropped", "Dark", "Distorted")
VARIANTS = ("perspective", "dark", "low_contrast", "rotated", "glare")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cyclic_quad(points):
    quad = np.asarray(points, dtype=np.float32).reshape(4, 2)
    if not np.isfinite(quad).all():
        raise ValueError("Nonfinite annotation")
    center = quad.mean(axis=0)
    quad = quad[np.argsort(np.arctan2(quad[:, 1] - center[1], quad[:, 0] - center[0]))]
    if not cv2.isContourConvex(quad) or abs(cv2.contourArea(quad)) < 1:
        raise ValueError("Degenerate annotation quadrilateral")
    return quad


def geometry_metrics(predicted, expected, image_shape):
    """Full quadrilateral IoU, visible IoU, cyclic/reversal invariant corner error."""
    pred, truth = cyclic_quad(predicted), cyclic_quad(expected)
    h, w = image_shape[:2]
    a, b = abs(cv2.contourArea(pred)), abs(cv2.contourArea(truth))
    intersection = max(0.0, float(cv2.intersectConvexConvex(pred, truth)[0]))
    iou = intersection / max(a + b - intersection, 1e-9)
    errors = [float(np.linalg.norm(pred - np.roll(order, shift, axis=0), axis=1).mean())
              for order in (truth, truth[::-1]) for shift in range(4)]
    in_frame = bool(((truth[:, 0] >= 0) & (truth[:, 0] < w) &
                     (truth[:, 1] >= 0) & (truth[:, 1] < h)).all())
    bounds = np.float32([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
    visible_area, visible = cv2.intersectConvexConvex(truth, bounds)
    visible_iou = None
    if visible is not None and visible_area > 0:
        visible = visible.reshape(-1, 2).astype(np.float32)
        overlap = max(0.0, float(cv2.intersectConvexConvex(pred, visible)[0]))
        visible_iou = overlap / max(a + float(visible_area) - overlap, 1e-9)
    return dict(polygon_iou=float(iou), visible_polygon_iou=visible_iou,
                corner_error_normalized=min(errors) / float(np.hypot(w, h)),
                gt_in_frame=in_frame)


def select_real(rows, split, per_label, seed):
    """Round robin by physical document; selection independent of detector outcomes."""
    chosen = []
    for label in LABELS:
        buckets = defaultdict(list)
        for row in rows:
            if row["split"] == split and row["label"] == label and row["is_reference"] != "1":
                buckets[row["document"]].append(row)
        for doc, items in buckets.items():
            items.sort(key=lambda r: digest(f"{seed}:{r['relative_path']}"))
        docs = sorted(buckets, key=lambda d: digest(f"{seed}:{label}:{d}"))
        count, offset = 0, 0
        while count < per_label and any(offset < len(buckets[d]) for d in docs):
            for doc in docs:
                if offset < len(buckets[doc]) and count < per_label:
                    chosen.append(buckets[doc][offset])
                    count += 1
            offset += 1
    return chosen


def synthetic_capture(reference, variant, seed):
    """Place a reference on a background with a known projective transformation."""
    rng = np.random.default_rng(seed)
    h, w = 720, 960
    yy, xx = np.mgrid[:h, :w]
    background = np.clip(48 + 14 * xx / w + 9 * yy / h, 0, 255).astype(np.uint8)
    canvas = np.repeat(background[:, :, None], 3, axis=2)
    rh, rw = reference.shape[:2]
    scale = min(640 / rw, 470 / rh)
    card_w, card_h = rw * scale, rh * scale
    x0, y0 = (w - card_w) / 2, (h - card_h) / 2
    quad = np.float32([[x0 + .10 * card_w, y0 + .06 * card_h],
                       [x0 + .88 * card_w, y0 + .18 * card_h],
                       [x0 + card_w, y0 + .92 * card_h],
                       [x0, y0 + card_h]])
    quad += rng.uniform(-8, 8, (4, 2)).astype(np.float32)
    src = np.float32([[0, 0], [rw - 1, 0], [rw - 1, rh - 1], [0, rh - 1]])
    matrix = cv2.getPerspectiveTransform(src, quad)
    warped = cv2.warpPerspective(reference, matrix, (w, h))
    mask = cv2.warpPerspective(np.full((rh, rw), 255, np.uint8), matrix, (w, h))
    if variant == "low_contrast":
        # Reduce card/background contrast while preserving some text detail.
        warped = np.clip(warped.astype(np.float32) * .32 + canvas * .68, 0, 255).astype(np.uint8)
    alpha = (mask.astype(np.float32) / 255)[:, :, None]
    result = np.clip(warped * alpha + canvas * (1 - alpha), 0, 255).astype(np.uint8)
    if variant == "dark":
        result = np.clip(result.astype(np.float32) * .28, 0, 255).astype(np.uint8)
    elif variant == "rotated":
        # Rotate the complete input, including known corners, to test portrait frames.
        result = cv2.rotate(result, cv2.ROTATE_90_CLOCKWISE)
        quad = np.column_stack((h - 1 - quad[:, 1], quad[:, 0])).astype(np.float32)
    elif variant == "glare":
        cx, cy = .72 * quad[1] + .28 * quad[3]
        radius_x, radius_y = max(12, card_w * .09), max(12, card_h * .07)
        glow = np.exp(-(((xx - cx) / radius_x) ** 2 + ((yy - cy) / radius_y) ** 2) * 2)
        result = np.clip(result.astype(np.float32) + glow[:, :, None] * 240 * alpha, 0, 255).astype(np.uint8)
    return result, quad


def samples(rows, args, annotations):
    if args.mode == "real":
        for row in select_real(rows, args.split, args.per_label, args.seed):
            path = row["relative_path"]
            yield dict(id=row["image_name"], path=path, document=row["document"],
                       group=row["label"], kind="real", source_label=row["label"]), read_image(ROOT / path), annotations.get(path)
        return
    refs = sorted((r for r in rows if r["split"] == args.split and r["is_reference"] == "1"),
                  key=lambda r: r["document"])
    for row in refs:
        reference = read_image(ROOT / row["relative_path"])
        for variant in VARIANTS:
            sample_id = f"doc{row['document']}_{variant}"
            sample_seed = int(digest(f"{args.seed}:{sample_id}")[:8], 16)
            image, quad = synthetic_capture(reference, variant, sample_seed)
            yield dict(id=sample_id, path=row["relative_path"], document=row["document"],
                       group=variant, kind="synthetic"), image, quad
    # Negative controls report false accepts separately; they are not card accuracy.
    for name, image in (("blank", np.full((720, 960, 3), 100, np.uint8)),
                        ("gradient", np.repeat(np.tile(np.linspace(30, 180, 960, dtype=np.uint8), (720, 1))[:, :, None], 3, axis=2))):
        yield dict(id=name, path=None, document=None, group="negative", kind="negative"), image, None


def load_detector(path):
    if path is None:
        return Homography()
    spec = importlib.util.spec_from_file_location("ekyc._module2_evaluation_baseline", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Homography()


def evaluate(detector, image, truth):
    started = time.perf_counter()
    try:
        warped, geo = detector.run(image)
        result = dict(status="returned", geometry=geo)
        if truth is not None:
            result.update(geometry_metrics(geo["corners"], truth, image.shape))
    except StageError as error:
        result, warped = dict(status="rejected", reason=str(error)), None
    except Exception as error:
        result, warped = dict(status="error", reason=f"{type(error).__name__}: {error}"), None
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result, warped


def evaluate_oracle(detector, image, truth):
    """Provided-corners diagnostic only; deliberately omit accuracy metrics."""
    started = time.perf_counter()
    try:
        warped, geo = detector.run(image, corners=truth)
        result = dict(status="returned", output_shape=list(warped.shape),
                      method=geo.get("method"), rectified_metrics=geo.get("rectified_metrics"))
    except StageError as error:
        result, warped = dict(status="rejected", reason=str(error)), None
    except Exception as error:
        result, warped = dict(status="error", reason=f"{type(error).__name__}: {error}"), None
    result.update(elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
                  interpretation="Independent corners supplied to isolate warp from localization; a returned image does not establish readability.")
    return result, warped


def geometric_pass(result):
    return result.get("polygon_iou", 0) >= .90 and result.get("corner_error_normalized", 1) <= .03


def thumbnail(image, max_side=640):
    scale = min(1.0, max_side / max(image.shape[:2]))
    return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)


def summarize(records, detector):
    groups = {}
    for group in sorted({r["group"] for r in records} | {"all_documents"}):
        selected = [r for r in records if (r["kind"] != "negative" if group == "all_documents" else r["group"] == group)]
        values = [r[detector] for r in selected]
        annotated = [r for r in selected if r["gt_quad"] is not None and r["gt_in_frame"]]
        correct = sum(r[detector].get("polygon_iou", 0) >= .90 and
                      r[detector].get("corner_error_normalized", 1) <= .03 for r in annotated)
        times = [v["elapsed_ms"] for v in values]
        groups[group] = dict(count=len(values), statuses=dict(Counter(v["status"] for v in values)),
                             annotated_in_frame=len(annotated), geometric_success=correct if annotated else None,
                             annotated_out_of_frame=sum(r["gt_quad"] is not None and not r["gt_in_frame"] for r in selected),
                             false_accepts=sum(v["status"] == "returned" for v in values) if group == "negative" else None,
                             geometric_success_rate=correct / len(annotated) if annotated else None,
                             median_ms=float(np.median(times)) if times else None,
                             p95_ms=float(np.percentile(times, 95)) if times else None)
    return groups


def report(args, records, detectors, source_hashes, runner_hash):
    summary = {name: summarize(records, name) for name in detectors}
    oracle_records = [r for r in records if "oracle" in r]
    oracle_summary = dict(
        enabled=args.oracle, evaluated=len(oracle_records),
        statuses=dict(Counter(r["oracle"]["status"] for r in oracle_records)),
        automatic_geometry_failed_or_rejected_but_oracle_returned=sum(
            not geometric_pass(r["current"]) and r["oracle"]["status"] == "returned" for r in oracle_records),
        interpretation="Provided-corners transform diagnostic. Excluded from detector accuracy and latency summaries; OCR/readability not assessed.")
    limitation = ("Synthetic geometry diagnostic on transformed reference image boundaries. "
                  "Not a real-camera accuracy benchmark, not OCR accuracy, and not proof that information hidden by glare is recovered."
                  if args.mode == "synthetic" else
                  "Real captures: successful return means only that the detector returned a quadrilateral. "
                  "Geometric accuracy is unavailable for images without independent corner annotations.")
    data = dict(mode=args.mode, split=args.split, seed=args.seed, limitation=limitation,
                criteria=dict(polygon_iou_min=.90, corner_error_normalized_max=.03,
                              normalization="mean best cyclic/reversed corner distance / image diagonal"),
                sample_fingerprint=digest(json.dumps([{k: r[k] for k in ("id", "path", "group")} for r in records], sort_keys=True)),
                input_fingerprint=digest(json.dumps([{k: r[k] for k in ("id", "input_sha256")} for r in records], sort_keys=True)),
                manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
                implementation_sha256=source_hashes, evaluation_script_sha256=runner_hash,
                runtime=dict(python=sys.version, opencv=cv2.__version__, numpy=np.__version__, opencv_threads=1),
                summary=summary, oracle_diagnostic=oracle_summary, records=records)
    write_json(args.output / "report.json", data)
    lines = [f"# Module 2 diagnostic: {args.mode} / {args.split}", "", limitation, "",
             "No Module 1 gate was used. Thresholds are diagnostic criteria, not calibrated production guarantees.", "",
             "| Detector | Group | Samples | Returned | Rejected | Error | Geometry pass / annotated in-frame | Median ms |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for name, groups in summary.items():
        for group, s in groups.items():
            geometry = f"{s['geometric_success']}/{s['annotated_in_frame']}" if s['annotated_in_frame'] else "unavailable"
            st = s["statuses"]
            lines.append(f"| {name} | {group} | {s['count']} | {st.get('returned',0)} | {st.get('rejected',0)} | {st.get('error',0)} | {geometry} | {s['median_ms']:.1f} |")
    if args.oracle:
        lines += ["", "Provided-corners diagnostic (excluded from detector accuracy):",
                  f"- Evaluated: {oracle_summary['evaluated']}; statuses: {oracle_summary['statuses']}.",
                  f"- Automatic geometry failed/rejected but provided-corners warp returned: {oracle_summary['automatic_geometry_failed_or_rejected_but_oracle_returned']}.",
                  "- This isolates localization from transform execution; it does not prove OCR readability."]
    (args.output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    body = ["<!doctype html><meta charset='utf-8'><title>Module 2 diagnostic</title>",
            "<style>body{font:16px system-ui;margin:24px;background:#f3f5f7}article{background:white;margin:20px 0;padding:16px}img{max-width:32%;max-height:350px;object-fit:contain;vertical-align:top}pre{white-space:pre-wrap}code{font-size:12px}</style>",
            f"<h1>Module 2: {args.mode} / {args.split}</h1><p>{html.escape(limitation)}</p>",
            "<p>Overlay: green = supplied ground truth (if available), red = baseline, blue = current. Image boundaries are ground truth only in synthetic mode.</p>"]
    for r in records:
        if not r.get("artifacts"):
            continue
        body.append(f"<article><h2>{html.escape(r['id'])} · {html.escape(r['group'])}</h2>")
        for caption, path in r["artifacts"].items():
            body.append(f"<img src='{html.escape(path)}' alt='{caption}' title='{caption}'>")
        details = {name: {k: v for k, v in r[name].items() if k != "geometry"} for name in detectors}
        if "oracle" in r:
            details["oracle_provided_corners_not_accuracy"] = r["oracle"]
        body.append("<pre>" + html.escape(json.dumps(details, ensure_ascii=False, indent=2)) + "</pre></article>")
    (args.output / "gallery.html").write_text("\n".join(body), encoding="utf-8")
    print(json.dumps(dict(output=str(args.output), summary=summary), ensure_ascii=False, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("synthetic", "real"), default="synthetic")
    parser.add_argument("--split", choices=("val", "test"), default="val")
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/manifest.csv")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--annotations", type=Path)
    parser.add_argument("--oracle", action="store_true", help="Diagnose warp using independent in-frame corners; never count as detector accuracy")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/module2_review/evaluation")
    parser.add_argument("--per-label", type=int, default=8)
    parser.add_argument("--seed", type=int, default=20261025)
    parser.add_argument("--visuals", type=int, default=15, help="First N deterministic samples; -1 saves all")
    args = parser.parse_args()
    if args.per_label < 1 or args.visuals < -1:
        parser.error("per-label must be positive; visuals must be >= -1")
    cv2.setNumThreads(1)
    args.output.mkdir(parents=True, exist_ok=True)
    with args.manifest.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    annotations = json.loads(args.annotations.read_text(encoding="utf-8-sig")) if args.annotations else {}
    paths = {"current": ROOT / "ekyc/module2_homography.py"}
    if args.baseline:
        paths = {"baseline": args.baseline, **paths}
    source_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    runner_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    detectors = {name: load_detector(None if name == "current" else path) for name, path in paths.items()}
    records = []
    for index, (meta, image, truth) in enumerate(samples(rows, args, annotations)):
        truth = cyclic_quad(truth) if truth is not None else None
        h, w = image.shape[:2]
        meta.update(image_shape=list(image.shape), gt_quad=truth.tolist() if truth is not None else None,
                    gt_in_frame=bool(((truth >= 0) & (truth < [w, h])).all()) if truth is not None else None,
                    input_sha256=hashlib.sha256(image.tobytes()).hexdigest())
        warped_images = {}
        for name, detector in detectors.items():
            result, warped = evaluate(detector, image, truth)
            meta[name] = result
            warped_images[name] = warped
        if args.oracle and truth is not None and meta["gt_in_frame"]:
            meta["oracle"], warped_images["oracle"] = evaluate_oracle(detectors["current"], image, truth)
        visual = (args.visuals == -1 or index < args.visuals or
                  (args.oracle and truth is not None and not geometric_pass(meta["current"])))
        overlay, artifacts = image.copy(), {}
        if visual and truth is not None:
            cv2.polylines(overlay, [np.rint(truth).astype(np.int32)], True, (0, 230, 0), 4)
        for name, warped in warped_images.items():
            if visual and warped is not None:
                result = meta[name]
                if name != "oracle":
                    points = np.rint(result["geometry"]["corners"]).astype(np.int32)
                    cv2.polylines(overlay, [points], True, (0, 0, 255) if name == "baseline" else (255, 80, 0), 2)
                relative = f"images/{index:03d}_{name}.jpg"
                write_image(args.output / relative, thumbnail(warped))
                artifacts[name + " warp"] = relative
        if visual:
            relative = f"images/{index:03d}_overlay.jpg"
            write_image(args.output / relative, thumbnail(overlay))
            meta["artifacts"] = {"input overlay": relative, **artifacts}
        records.append(meta)
        print(f"[{index + 1}] {meta['id']}: " + ", ".join(f"{n}={meta[n]['status']}" for n in detectors), flush=True)
    if not records:
        parser.error("No samples found for this mode/split in the manifest")
    report(args, records, paths, source_hashes, runner_hash)


if __name__ == "__main__":
    main()
