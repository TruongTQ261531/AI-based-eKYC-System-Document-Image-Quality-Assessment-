# Locked research expansion: document recovery,2026-10-30

This extends e7e4602 on the research branch only. Earlier exposed MIDV IDs and
all previous results remain exploratory. CORE B acceptance is not guaranteed.
No new venv or bulk dependency installation. Local web port8001 is separate
from the mentor server on8000. Private camera content is never persisted.

## Contributions to test, not assume

1. A reproducible partial-capture dataset with explicit complete/visible-field
   references, physical-identity grouping, layout holdouts, image/source hashes
   and capture transformations. Synthetic cards are newly authored SPECIMEN
   documents; MIDV derivatives are attributed, not claimed as new real captures.
   Geometric visibility labels are not human legibility annotations.
2. Budgeted view selection using predicted geometry and OCR observations,
   tested against fixed completion, full-frame, bbox and contour baselines.
   Linear/ridge and shallow boosted-stump selectors are competing structures;
   choosing the best development model is not a claim of novel learning theory.
3. A localhost camera/review interface using the actual prediction pipeline,
   displaying observed OCR fields and source text without filling missing values.

## Dataset and sealed evaluation

Newly generated90 synthetic identities, six layouts, three document families
(citizen-like mock card, student card, driving-licence-like mock card), English
and Vietnamese labels. Four captures per identity: full, corner clipping,
field clipping, blur/glare. Total360 images. Layouts0..3 each have five
development,five calibration,five test IDs; layouts4..5 each have15 test IDs.
Thus20 development,20 calibration,50 test identities. Text/geometry/rendering
are seeded and versioned; no real identity documents or portrait photos.

Acquire60 previously unused MIDV-2020 photo identities, six per template type,
excluding the20 used earlier. Select filenames by SHA256 before OCR. Per type:
two development,one calibration,three test. Derive original plus two fixed
frame-clipping views; total180 images,20/10/30 identities by role. Upstream
DocAligner may already have seen MIDV; call these newly selected study IDs,
never verified unseen-pretraining identities. Newly authored cards provide a
separate source with independently generated values/layouts.

All540 cases remain in routing/latency counts, even when they have no fully
visible Latin target. Original full strings, character/field geometry and
visibility fractions stay private. Publish numeric manifests and regeneration
code; publish only newly authored specimen examples, not MIDV images or camera
PII. Respect author CC BY-SA2.5 attribution on MIDV derivatives.

## Predictors and baselines

Reuse pinned DocAligner and legacy CRAFT/EasyOCR/VietOCR. Add an independently
sourced CPU OCR baseline using the official RapidOCR1.4.4 wheel (SHA256
971d7d5f223a7a808662229df1ef69893809d8457d834e6373d3854bc1782cbf),
loaded from a private cache without installation. Verify its native output
against the wrapper. The wheel's PP-OCRv4 detector/recognizer is one baseline;
an author-published Latin recognizer is a language-appropriate alternative,
with source/model hashes and alphabet coverage recorded before test scoring.
If a baseline is unavailable, record the actual failure rather than inventing
results. Commercial API systems without credentials are not claimed tested.

Image policies: raw, strict four-corner warp, padded parallelogram+5%,
observed-support bbox, classical contour warp, and text-line deskew. Non-strict
policies explicitly fall back to raw when geometry is unavailable. No GT/type
or expected aspect ratio enters inference. Identical rasters within a case may
share OCR, with measured stage cost charged to every equivalent policy.

Candidate selectors: fixed completion; maximum mean OCR confidence; ridge;
boosted stumps; and a budgeted cascade starting with completion and allowing
one fallback only when development-fitted expected error justifies it.
Features contain only image shape, corner counts, transform characteristics,
predicted boxes/edge contact, OCR confidence, recognized length and disagreement.
Development labels are field CER/exact, not test annotations. Tune only on
development IDs using deterministic grouped folds. Calibration selects a
review threshold at a fixed80% target image retention; no risk guarantee is
claimed. Report all alternatives and fixed review curves.

Primary predictor uses no GT. Separate evaluator matches predicted boxes to
fully geometrically visible GT fields, and reports field exact, uncapped CER,
detection coverage, digit fields, routed/review fractions, wall/process CPU and
tail latency. Semantic field extraction is evaluated separately against field
keys for synthetic cards; it must not use GT boxes or mandatory template values.

## Timing, repeats and honesty gates

Commit data/model/algorithm hashes before main test scoring. Per-case atomic
checkpoints and process lock prevent duplicate runs. No cross-pass OCR reuse.
One full540-case pass; two additional fresh passes on a fixed24-identity panel
(12 synthetic,12 MIDV; one capture per ID chosen by hash) with randomized policy
order. Report matched-panel mean/SD and exact canonical prediction agreement.
New inference or adapter bugs require an explicitly versioned run, not silent
replacement. Counterbalanced panel timing is distinct from replaying cached
scores. Legacy OCR is cross-checked on the same panel, not claimed run on all540.

Final test scores are released only after fitting/locking selectors on dev and
review threshold on calibration. Resample physical IDs2000 times; report paired
intervals versus padded completion, separately by source/layout/capture. Repeats
are not additional identities. No threshold changes after test inspection.

A negative result fails the proposed superiority claim. It does not authorize
discarding cases, renaming a baseline as novel, claiming verified PAD, or calling
synthetic-only evidence deployment validation. Resolve implementation and dataset
audit gaps explicitly; train-overlap and real-world breadth may remain external
limitations requiring author disclosure or fresh consented data collection.
