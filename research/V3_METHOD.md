# Method specification for the paper draft

This document describes the implemented method. It does not assert acceptance
at a conference or introduce results before the sealed test is complete.

## Question and scope

When part of an identification document is hidden, does supervision based on
one printed field penalize answers that remain supported elsewhere? We study
this question on the same rendered and photographed mock-document pixels,
holding input presentation and optimizer exposure fixed. The task is extraction
into 17 optional semantic keys, not authentication of a person or document.

## Explicit evidence

For a document, let each field k have realizations R_k. A realization r contains
a literal string, a source identifier and one or more component polygons Q_rj.
Sources are the author's semantic body annotations, their declared language
variants, narrowly linked duplicates, and recognized ICAO TD3 spans. Arbitrary
text equality across unrelated fields does not establish a semantic link.
TD3 optional data is linked to a personal number only with an explicit author
value association. The online conventional parser does not make that assumption.

For the capture transform H and synthetic mask set M, the implemented proxy is

```
visible(r) = AND_j [every vertex of H(Q_rj) is inside the captured image
                   AND no mask intersects H(Q_rj) by more than 0.05 pixel^2]
O_k = {r in R_k : visible(r)}
include(k) = (O_k is nonempty)
```

The 0.05 threshold is an absolute numerical area tolerance, not five percent
of a field. Multiline values require all actual line components; empty gaps
between lines are not text. A backup realization is sufficient even if the
primary body value is masked. This is a geometric proxy for explicit evidence,
not a human judgment of legibility after blur, glare, resampling or rectification.
Absence from this bounded graph is not proof of absence from every possible
encoded or inferred source on the document.

TD3 coordinates come from a projective mapping of the author's 44-character
MRZ strip to character spans. Format and numeric checks are recorded without
correcting OCR characters. Name truncation is handled conservatively. Checksums
do not protect every semantic attribute and do not establish authenticity.

## Date precision and supervision

Dates preserve the printed string. A six-digit TD3 date exposes a two-digit
year; it does not expose a century. If multiple realizations remain, training
prefers the maximum explicitly observed date precision, then native body text,
declared body translation/duplicate, then MRZ. Other keys prefer body text first.
Only fields with observed realizations enter the JSON target. An empty target
is a valid abstention case. This is a deterministic supervision rule, not an
online lookup of an expected identity or field set.

## Model and controls

The pinned complete model is 5CD-AI/Vintern-1B-v3_5, revision
`b98f263eab246eb5269ade64edbdca8a887dc44d`. It has 938,193,024 parameters.
LoRA updates 1,081,344 parameters in the language module's q/k/v/o projections
(rank 8, alpha 16, dropout 0). Its image encoder and projector remain part of
the multimodal system and are frozen. A Qwen language checkpoint alone is not
an equivalent replacement for this VLM.

Each arm uses 640 image slots from 128 train identities, 320 AdamW steps with
four-image gradient accumulation, and exactly 1,280 presentations. Learning
rate is 0.0002, weight decay 0.01. Two independent initializations use seeds
42 and 31415. The checkpoint is always the final step 320; no test selection
or unequal checkpoint selection is permitted.

R2 complete-content and body-partial arms share ordered identity/slot exposure;
three common views have identical file bytes. V3 source-partial and R2
body-partial share the entire ordered pixel sequence. Only supervised targets
differ in that comparison. Target token counts, wall time and memory are
reported separately: equal steps/images do not imply identical answer-token
counts or identical compute cost.

The raw/rectified and two/four-tile profiles are compared on a fixed development
panel before training. The selected rect2 profile is then fixed for every
model. Rectification uses predicted corners and the existing completion/fallback
path, never annotation corners. Frozen visual features are cached for speed;
the final audit re-extracts every referenced input and requires exact equality.
Fresh end-to-end repetitions measure processing from image pixels, rather than
claiming cache-only generation timing as complete camera latency.

## Evaluation and interpretation

The development set has 24 identities/72 views and test has 48 identities/144
views. Test combines 24 authored specimens and 24 photographed mock documents;
it includes held layouts and a held capture-device stratum. Identity, raster,
font/layout and earlier-study overlap checks are retained. Unknown overlap with
the base model's pretraining cannot be excluded.

All eight VLM comparators use the same prompt and test images. Six existing R2
outputs are re-scored under the source contract; they are not new independent
inference runs. Two new V3 models add the controlled supervision intervention.
Two frozen OCR readers with the printed-label matcher, TD3 format fallback and
TD3 checksum fallback provide six CPU configurations. Three postprocessors
share each OCR call. Separate R2 and V3 CPU calls provide a repeatability check.

Primary scoring accepts any explicitly visible realization after declared text,
gender and date normalization. A separate maximum-date-precision F1 reveals
outputs that return less date information than the image contains. We report
wrong values, omissions, keys outside the declared reference contract, empty
abstention and source/layout/device/view strata. An outside-contract key is not
automatically called a hallucination. Strict JSON parsing is secondary to the
declared tolerant parser shared by all methods.

Paired bootstrap intervals resample identities, source-stratified 24+24, 10,000
times. They quantify test-sample uncertainty, not all training uncertainty.
Seeds are reported separately. Both model locks are published and remotely
verified before any test generation. Raw output replay and numeric provenance
remain available locally; public artifacts exclude document values and weights.

The post-hoc diagnostic matrix reports how the same predicted field changes
status under the body and source contracts. It is descriptive and never used
for model selection. Related work is listed in V3_RELATED_WORK.md: OR/AND,
MRZ parsing, redundancy and LoRA are established techniques. The contribution
candidate is a measured reference-policy effect and a controlled inexpensive
remedy; independent human legibility, new consented camera data and broader
backbone validation remain necessary evidence for stronger generalization.
