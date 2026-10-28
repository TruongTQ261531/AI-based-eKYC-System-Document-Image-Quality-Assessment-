# Candidate method and limits

Let q be a convex document quadrilateral predicted without ground truth. Its
four inward unit edge normals are n_i and edge offsets b_i = n_i^T q_i.
For image domain Omega and nonnegative per-edge margins m_i, return

    C(q,m) = Omega intersect {x : n_i^T x >= b_i - m_i for every i}.

This is a support region, potentially with more than four vertices after
clipping to the frame. It is not a claim that true physical corners or missing
characters have been reconstructed. A downstream implementation can preserve
this support in a padded crop rather than inventing document pixels.

Three deterministic views use the frozen geometry localizer: original, CLAHE
grayscale, and 0.75-scale round trip. The IoU medoid provides q. Endpoint
disagreement projected onto each edge normal and its observed edge support
produce a positive scale s_i, with a source-pixel and document-size floor.
Unreliable view agreement falls back explicitly to full-frame review.

For calibration target polygons T (visible card, or projected visible text
fields), compute

    r(x,T) = max_i max_{v in vertices(T)} [b_i - n_i^T v]_+ / s_i.

For each physical document g, take the maximum r over its fixed sampled
frames, both MIDV sources included. With n=20 calibration groups and alpha=.10,
use the ceil((n+1)*(1-alpha))-th order statistic (19th of 20), not an interpolated
percentile. At inference, m_i = r_hat*s_i. No calibration/test annotation or
reference-text lookup is required by the predictor at inference.

This is an application of existing group-level split-conformal reasoning. A
coverage statement requires exchangeability of whole-document score groups
under the same sampling protocol; it is marginal, not a per-card certainty.
It does not imply conditional error control among the automatically accepted
subset or under a different camera/source distribution. Twenty groups provide
limited granularity and may require very wide regions.

Text-field-targeted calibration may reduce waste on blank document borders,
but it also does not protect a portrait/signature unless those regions are
included as explicit targets. That is a scope limit for an eventual full eKYC
deployment. Current research code does not modify the mentor verification flow.

Finite half-plane expansion, view perturbations and conformal quantiles are
not claimed as new mathematical inventions. The proposed research claim must
be supported by content-preservation utility and a clear closest-prior audit.
