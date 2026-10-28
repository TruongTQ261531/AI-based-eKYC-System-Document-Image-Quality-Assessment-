# Locked feasibility protocol, 2026-10-28

Mentor baseline: `4110f22b94699d30950cd1c0b23532ee9ccaaa59`.
This is a research feasibility study, not a completed CORE B submission.
Protocol fixed before computing benchmark predictions or inspecting outcomes.

Pre-inference clarification: all methods receive images resized to maximum side
960 for CPU feasibility, and predictions are mapped to source coordinates.
Add a field-aware calibration variant using projected annotated text fields,
and report worst-text-field retention alongside full visible-card retention.
This amendment is fixed before any benchmark predictions are computed.
Adaptive/constant calibrated variants require at least two valid view predictions
and median pairwise IoU >=0.50; otherwise use a full-frame review fallback.
All methods use the same automatic-accept gate: valid localizer output,
expanded/base area <=1.35 and output/frame area <=0.95. Report unconditional
region metrics as well, so this gate cannot hide a poor crop.

## Hypothesis and scope

Per-edge uncertainty from independently localized photometric/scale views can
support a less destructive crop than a single document quadrilateral, at a
smaller background-area cost than a uniformly enlarged crop.
The candidate method is an adaptive outward half-plane expansion calibrated
at physical-document level. Conformal prediction itself is prior work; novelty
of the particular document intervention must be assessed, not assumed.
No restored text is generated or inferred by an LLM.

## Data and immutable sampling

- Obtain original frame and reference annotations from author-published MIDV FTP ZIP archives, reading JSON only.
- Join to existing `full_dataset_original`; verify image dimensions and index alignment. Record every missing/malformed case.
- Primary set: frame numbers 01,08,15,22,30 in every available MIDV500/MIDV2019 clip, all 50 physical documents (expected 3500 frames). References are not independent samples and are excluded from the primary score.
- Report MIDV500 and MIDV2019 separately, including clipped/invisible documents. No removal because a method fails.
- Ground truth is never passed to the localizer or used to select a candidate at inference.
- Legacy MobileNet/ScanOCR weights have uncertain history for this purpose; do not use them as evidence for a leakage-free learned research result.

## Method and baselines

Three deterministic views: original, grayscale CLAHE, downscale then upscale.
The unchanged geometric mentor localizer predicts one quad per view, with a
medoid prediction and per-edge dispersion. A missing prediction falls back
to the full frame and is marked for review; it is not silently excluded.

Methods: single view; multi-view medoid; fixed outward margins 5%,10%,20%;
adaptive uncalibrated expansion; document-group calibrated constant-scale
expansion; document-group calibrated adaptive per-edge expansion.
Any implementation deviation must be logged before reporting results.

## Calibration and repeats

- Seeds: 13,29,47,71,97.
- For each seed: 20 whole physical IDs for calibration, remaining 30 for test, shared across both MIDV sources. No frame-level random split.
- Miscoverage target alpha=0.10. Calibrate the maximum normalized outward residual per physical ID, quantile ceil((n+1)*(1-alpha)). Infinity/full-frame is retained if the finite-sample quantile is unattainable.
- Calibration uses visible ground-truth polygons; invisible cases have a separate stratum. No claim to recover off-screen content.
- Predictions may be cached once; seed repetitions alter calibration/test membership. Explicitly distinguish these from repeated model training.
- Repeat analysis from the same cache and verify identical numeric summaries.

## Metrics and interpretation

For every sampled frame: polygon IoU, visible-document area retention,
strict containment (1-pixel tolerance), predicted-area / visible-GT-area,
automatic-accept/review coverage, and failures. Also evaluate utility at IoU
>=0.80 AND retention>=0.98, preventing a full-frame crop from counting as success.
Record runtime, extraction exceptions and input/cache hashes.
Use paired physical-ID bootstrap (2000 resamples) for the first seed's test
set; do not treat adjacent frames or five overlapping split seeds as independent.
Report all seeds, all baselines and ablations, including negative results.

The exchangeability premise does not establish out-of-domain guarantees.
Geometric retention is not OCR accuracy or identity-verification accuracy.
No declaration of paper readiness without an explicit novelty/data/baseline audit.
