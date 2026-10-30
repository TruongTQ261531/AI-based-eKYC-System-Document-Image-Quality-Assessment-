# Supplementary analysis locked before inspecting OCR accuracy

2026-10-30: the main v2 benchmark is still running (100/225 atomic image
checkpoints at this analysis amendment). Only execution counts/timings have
been inspected. This adds analysis and stronger integrity checks; it does not
change inputs, inference, eligible targets, main metrics or frozen protocol.

The original protocol compares policies with raw full-frame. To distinguish
support geometry from simply routing a previously rejected image, also compare
these five fixed contrasts on the **three-predicted-corner stratum**:

1. Masked support versus three-corner full-frame.
2. Support bounding box versus three-corner full-frame.
3. Expanded parallelogram versus three-corner full-frame.
4. Masked support versus support bounding box.
5. Masked support versus expanded parallelogram.

For each of the two readers, compute field exact, macro CER and wall latency
deltas using pass1 only, the existing seed13 held-out physical IDs, and 2,000
paired physical-ID bootstrap samples (RNG seed20261031). Each ID receives equal
weight; first average fields within an image, then images within an ID. This
estimand differs from the main pooled-field accuracy tables. Report all
contrasts, with exploratory percentile95% intervals and no multiple-comparison
correction. Neither intervals excluding zero nor repeated inference alone
establish novel method superiority or submission readiness.

Audit every published numeric row against the corresponding private checkpoint
projection, recompute canonical prediction hashes and all144 summary rows,
in addition to the already planned re-scoring and stage-time arithmetic checks.
This detects publication/aggregation corruption; it is not an independent
ground-truth annotation or proof that the shared evaluator is bug-free.
