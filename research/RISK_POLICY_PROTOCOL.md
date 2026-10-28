# Exploratory second-stage protocol, 2026-10-28

This protocol follows inspection of the complete v1 results. It is not an
independent confirmatory study or a preregistration. The v1 code, protocol,
metrics and negative results are retained unchanged. No v2 outcome has been
computed when this file and its runner are committed.

## Question

Can a bounded-area expansion/review policy provide useful automatic coverage
while reducing crop-induced text-field harm, without the nearly whole-frame
regions produced by worst-frame, whole-document containment calibration?

Use the same 3,500 images, cached frozen predictions and five physical-ID
20/30 calibration/test splits. The three deterministic views are correlated;
no independence between views is assumed. No new model is trained.

## Fixed intervention and baselines

Two expansion families share `safe_base` and the existing consistency fallback:
constant edge scale max(1.5px, .01 sqrt(base area)), or original adaptive scales.
Parameter grid: 0, .25, .5, .75, 1, 1.5, 2, 3, 4, 6, 8, 12, 16, 32, infinity.
The last parameter returns the full frame and always requests review.

The automatic-processing gate remains fixed: consistent localization,
region/base area <=1.35 and region/frame area <=.95. The gate is a proposed
research operating point, not a validated production threshold.

For every frame define geometric field harm as worst visible annotated text
field area retention <.98. An automatically processed frame with no evaluable
visible text field (including an invisible card) also counts as harmful.
This is geometric area loss, not character-error rate or verification error.

For a physical ID, average frame losses over all 70 sampled frames, including
both sources and missing/invisible-target cases. Use equal physical-ID weights.
The capped-policy loss is harm * auto_process. Both harm and the gate are
nonincreasing as expansion increases, so their product is nonincreasing.
Audit monotonicity on every cached frame/family; fail rather than silently
monotonizing the results.

Methods for each scale family:

1. `erm_cap`: smallest grid parameter with mean calibration ID loss <=.10.
2. `crc_cap`: smallest parameter with (sum of n ID losses +1)/(n+1) <=.10.
3. `crc_uncapped`: same correction applied to harm before the area gate;
   evaluate automatic coverage with the same gate afterwards.
4. `frame_crc_cap`: use individual frame losses in the correction. This is
   an ablation of the exchangeable unit, **not** a valid independent-frame
   guarantee for correlated video frames.

Conformal Risk Control is existing work:
[Angelopoulos et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html).
Its assumptions concern exchangeable document groups and monotone bounded
losses. The interpretation is expected harmful automatic decisions per
random document/frame protocol; it is NOT conditional error among accepted
cases, a high-probability bound for this test set, or an OOD guarantee.
The mentor heuristic's previous exposure to MIDV limits even this assumption.

## Outputs and decision criteria

Retain all methods, splits, chosen parameters, calibration losses and test rows.
Report document-balanced harmful-auto frequency, auto coverage, conditional
harm among auto, correctly preserved automatic field coverage, accepted
geometric utility (IoU >=.80 and card retention >=.98), area and IoU.
Report both sources and the five quality strata separately. In addition to
all-seed summaries, use 2,000 paired physical-ID bootstrap samples on seed13
against frozen single-view and uncalibrated adaptive baselines. No multiplicity
correction: intervals are exploratory, not confirmatory significance claims.

No parameter-grid/alpha/gate/feature tuning after this stage's outcomes.
No novelty claim for CRC, group averaging, or rejection itself. The contribution
remains an application hypothesis until external data, strong neural-localizer
baselines and actual end-to-end OCR effects are established.
