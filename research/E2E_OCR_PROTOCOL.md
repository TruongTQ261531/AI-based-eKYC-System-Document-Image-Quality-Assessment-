# Locked end-to-end OCR experiment, 2026-10-30

This follow-up addresses the missing downstream evidence in REPORT_VI.md.
Earlier geometry outcomes are known; no outcome from this new OCR benchmark
has been inspected when this protocol and runner are committed. This is an
exploratory follow-up, not independent confirmation of an invented algorithm.

## Provenance and immutable sample

Use the existing environment/weights, never install dependencies or train.
Sources: author MIDV500/2019 annotations and 20 author MIDV-2020 photos already
audited; pinned DocAligner FastViT-SA24; EasyOCR 1.7.2 CRAFT and english_g2;
the existing VietOCR VGG Transformer and config. Record local SHA256, package
source hashes, author URLs and official EasyOCR MD5 verification. Retain the
upstream pretrained-training-overlap limitation.

Primary sample: from the frozen 700 frame15 cases, include all **91 cases with
exactly three corner predictions** and one four-corner case per physical ID
chosen by minimum SHA256 of `e2e-control-20261030/UID` (**50 controls**).
Include all **20 existing external photos** separately. No field/OCR-success
filter selects images. This is a targeted sample, not a random accuracy estimate
for all MIDV images. Report true GT corner visibility separately: missing neural
corners do not necessarily mean physically off-screen document corners.

## Six fixed policies

1. `raw_fullframe`: original oriented pixels, no localization/review gate.
2. `neural_strict`: four valid predicted corners and region/frame <=.95;
   rectify that predicted quad, otherwise request recapture/review.
3. `three_fullframe`: same four-corner path; exactly three corners forwards
   the original full frame; other failures request review.
4. `three_support`: same four-corner path; exactly three uses the two observed
   side half-planes, clips the polygon to frame and crops its bounding rectangle,
   with pixels outside polygon set white. Apply region/frame <=.95.
5. `three_support_bbox`: same as support but without the polygon mask; ablation
   separates rectangular cropping from removing background pixels.
6. `three_parallelogram05`: same four-corner path; exactly three completes the
   fourth by parallelogram and expands its four supporting lines outward by
   .05*sqrt(quad area). Rectify the expanded, potentially off-frame quad with
   white outside-source pixels; apply clipped region/frame <=.95.

Quad rectification uses longest opposite-side dimensions, max output side1600;
no GT corners, aspect ratio, card type or text orientation is given to inference.
No policy reconstructs missing characters. Partial-content routing is not
approval of an incomplete ID document in the production eKYC flow.

## OCR, entirely prediction-driven

CRAFT detects text on the actual policy image. Fixed parameters: canvas1280,
mag_ratio1, text_threshold.55, low_text.3, link_threshold.3, min_size6,
width_ths.35, add_margin.06. Use at most80 predicted regions in reading order;
record truncation. This cap is fixed before results.

Both recognizers receive only predicted line regions. EasyOCR greedy decoding,
batch_size16, rotation_info=[180], standard contrast handling. VietOCR receives
the same predicted-line crops and tests 0/180 degrees, choosing its own greater
confidence, never GT text. VietOCR groups tensors of identical width in batches
of at most8, with no extra padding/resizing, and freezes each sequence after
its own EOS. Before benchmark inference, compare text and confidence against
the existing single-line implementation on fixed synthetic lines (exact text,
confidence tolerance1e-4); abort on mismatch. This is an inference optimization,
not a claimed novel OCR model. CPU Torch threads2, OpenCV1, ONNX2. No dictionary,
0/O repair, language-model correction or ground-truth field crop.

## Evaluation contract and limitations

The predictor returns text+boxes; it does not receive field names or GT. Map
predicted boxes through the inverse policy transform to source coordinates.
Only after inference, assign each line to the eligible GT field having maximum
intersection/prediction area when >=.5 (and IoU>=.01). Multiple predicted lines
can map to a field; score reading order in that field's coordinate system.
This is an explicit spatial field-transcription evaluation, **not semantic KIE**
or successful automatic form-field labeling. Report unassigned regions; do not
call them all false positives because the dataset does not label every text.

Eligible targets: annotated nonempty Latin-script/alphanumeric text, length
1..128 after NFC uppercase/whitespace normalization, >=.995 visible area.
No source-size/recognition-success filter. Non-Latin, partially visible and
invalid fields are counted separately, not silently removed. Do not compare a
partial visible string to the unavailable full GT value. Keep every selected
image in routing/latency counts. Ground-truth projection is used only by the
evaluator, never by crop/detection/recognition. No arbitrary field is required
for every document type.

Metrics: per-field exact match, uncapped character edit distance/CER, field
detection coverage, digit-only-field exact match, image-level all-targets-exact,
unconditional correct-field yield (rejected/missing predictions are empty),
and conditional results among routed cases. Report geometry-review and no-text
rates separately. Confidence is not truth. Also report review/accuracy curves
at fixed median nonempty-line-confidence thresholds 0,.25,.5,.75,.9,.95;
do not select a production threshold from these test outcomes.

## Repetition, runtime and audit

Three complete fresh passes, shuffle image order with seeds202610301/2/3.
No OCR/prediction cache is reused across passes. Equal policy raster images
within one image/pass may reuse OCR; log unique executions and hashes, and
charge their measured stage time to every equivalent policy. This is shared
execution, not six independent measurements. Neural inference is measured fresh
once per image/pass and charged only to policies using it. Raw has zero
localizer cost. Model loading/warmup is recorded separately, not hidden in
steady-state latency. Record wall and process CPU time for decode/localization,
transform/detection/recognition and combined pipeline; no GT-scoring time is
charged as inference. These are serial desktop timings, not server throughput.

Save complete per-image/field numeric results, signature/input/model/code hashes,
attempt/failure journal and private predicted text+boxes for audit. Do not publish
personal strings/images. Each completed image is an atomic checkpoint, validated
against an immutable signature on resume. Unexpected exceptions abort the run;
do not drop a failed image or manufacture successful text.

Publish all three passes. Compare canonical prediction and scoring hashes, plus
timing variation; repeats are not independent data or training. Report primary,
3-corner/4-corner strata and external separately. The existing five physical-ID
splits are descriptive subgroup repetitions. Use first-pass seed13 held-out IDs
for 2,000 paired physical-ID bootstrap intervals; do not treat fields/video
frames as independent or overlapping splits as new tests. Publish all policies,
negative results and deviations, with no post-outcome threshold changes.
