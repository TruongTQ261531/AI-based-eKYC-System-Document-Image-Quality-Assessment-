# Candidate manuscript scope and decision gates

This is an evidence-based outline, not a submission-ready paper. The data do
not support a new general statistical theory or a broad eKYC security claim.

## Working title

**When Four Corners Are Unavailable: Content Preservation and Review Trade-offs
in Mobile Document Capture**

Target fit: ACM DocEng main research track, current ICORE B. Track format and
submission date must be checked in the actual 2027 CFP when published.

## Potential contribution, subject to further validation

Investigate visible-content support from a frozen corner detector when the
four-corner decoding contract fails. Contrast support preservation, guessed
corner completion and full-frame review/passthrough. Explicitly measure the
cost of correlated video frames and large crops instead of reporting only
containment. The elementary half-plane construction is not new mathematics.

## Evidence currently available

- 3,500 MIDV500/2019 images, 50 physical IDs, nine initial policies, five
  whole-ID calibration/test splits, all outcomes and failures retained.
- A negative result: worst-frame conformal containment can preserve text by
  keeping almost the whole frame while automatic-processing coverage vanishes.
- A strong neural comparator on a matching 700-image subset and 20 external
  new identities, with pinned model hash and stated training-provenance limits.
- Exactly-three-corner support raises routing coverage from 70.62% to 84.29%
  on the fixed subset; full-frame routing achieves the same gain. Thus the
  gain cannot be attributed uniquely to the proposed region.
- Support keeps less background than full-frame on rescued cases but provides
  almost no accepted geometric-utility increase. Padded parallelogram is a
  strong simple baseline with a different content-loss trade-off.
- Repeated analysis, actual inference re-run checks, unit/regression tests,
  clustered intervals, all split IDs and negative/post-hoc results are saved.

## Suggested structure

1. Problem: missing observed corners versus recoverability of visible content;
   explain that a full identity document and a useful OCR support region are
   different output contracts.
2. Related work: incomplete-boundary rectification, corner completion/stitching,
   neural corner heatmaps, crop uncertainty and conformal risk control.
3. Support construction: observed side selection and elementary containment
   under exact-side/convex-card assumptions; discuss noisy-corner failure modes.
4. Experimental protocol: physical-document grouping, immutable sampling,
   temporal dependence, upstream model/data exposure, and exploratory stages.
5. Results: all baseline trade-offs, full-frame control, post-hoc controls,
   crop-induced OCR diagnostic, real end-to-end OCR once measured.
6. Limitations: small external sample, overlapping templates, no PAD study,
   area versus actual compute, no reconstructed off-screen content.

## Required evidence before a submission decision

- Actual downstream field/character accuracy and runtime benefit beyond simply
  forwarding the full image or completing a padded parallelogram.
- An external dataset/collection large enough to reveal failure modes across
  several cameras/conditions, with disjoint physical identities and explicit
  template overlap. No universal minimum count guarantees paper quality.
- Verified implementation of strong comparators and audit of training overlap.
- Closest-prior distinction stronger than applying known clipping/CRC to IDs.

If these gains are absent, retain the negative results and revise the research
question. A technically correct implementation and large result table alone
do not establish enough novelty for CORE B.
