# Observed-edge support: exploratory candidate after the neural baseline

2026-10-28, fixed before decoding partial corners or observing this candidate's
outcomes. The neural comparator has already shown that the geometric v1/v2
method is insufficient. The new question concerns the four-corner decoder's
all-or-review behaviour, not a claim of a new neural network.

On the same 700 frame15 and 20 external cases, retain all originally valid
DocAligner predictions unchanged. Re-run the 203 failed cases only, with the
same pinned model and preprocessing, to decode each corner channel separately
using the unchanged .3/Otsu/centroid procedure. Count all 0/1/2/3/4-corner
patterns. Only exactly-three-corner cases are eligible for rescue; otherwise
retain the original review fallback. No GT is used to detect missingness.

Compare five policies, with no fitted parameters:

1. Original neural quad/full-frame review.
2. Three-corner convex hull triangle (simple content-loss baseline).
3. Parallelogram completion, q_missing=q_prev+q_next-q_opposite.
4. Frame clipped by the **two observed document sides** whose endpoint
   corner channels are both present. Orient each inward normal toward the
   third observed corner. Keep the resulting polygon, not a guessed fourth
   physical corner or an invented rectified image.
5. Same observed-side intersection with outward margin equal to half the
   source-space heatmap-cell diagonal. This deterministic resolution floor
   is not a calibrated confidence bound.

Require finite non-collinear observed points. Original automatic gate remains
valid support output and region/frame <=.95; expansion/base ratio is 1 because
this is a support proposal, not expansion of an observable four-corner base.
State that this changes which partial-document cases can be processed; it is
not permission to approve an incomplete identity document in production eKYC.

Geometric fact: if the two observed sides are exact supporting lines of a
convex card, its visible portion lies in their inward half-planes intersected
with the frame. This is elementary convex geometry, **not new theory** and not
an unconditional guarantee for noisy neural corners. Missing corners need not
be reconstructed for this weaker support-region goal.

Use the same metrics, all five test splits (420 frames each) and separate 20
external cases. Report all policies, corner-pattern counts, recovery coverage,
field harm, accepted utility, area and source/quality strata. Add 2,000 paired
ID bootstrap intervals on seed13 for coverage, harmful-auto and accepted
utility relative to the original neural baseline. Never count fallback as
successful automatic localization.

Closest-prior caveat: partial/missing-corner document processing already exists,
including [IRI 2022 missing-corner stitching](https://web.ntpu.edu.tw/~myday/doc/IRI2022/IEEE_IRI2022_Proceedings/pdfs/IRI2022-2biJIxjybiQ3DOmA6IkB2x/660300a262/660300a262.pdf)
and [incomplete-boundary rectification, ICASSP 2025](https://doi.org/10.1109/ICASSP49660.2025.10889411).
The investigated distinction is preserving only observed content with partial
support constraints and no additional model/training. Novelty is unconfirmed.
No SOTA claim: upstream training split provenance and exact numeric equivalence
of our adapter with its package remain unresolved.
