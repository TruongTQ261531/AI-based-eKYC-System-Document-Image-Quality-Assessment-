# V3: author-source visibility rather than one-box absence

Registered before any R2 or V3 test prediction. R2 continues unchanged as the
body-ROI reference-policy comparator. R2 adapted models have not been evaluated
on test. No new physical images or extra person identities are introduced.

## Motivation from annotation inspection, not model test performance

The 64 selected author sources contain27 TD3 passports with two44-character
MRZ lines. Full author first names, surnames, document numbers and personal
numbers repeat in those lines. Thus hiding one printed body box is insufficient
to prove that a field is absent. R2 also uses a convex hull for multiline groups;
the evidence may instead be conjunctive over actual components.

This motivates a prospective reference-policy study. Define a field's usable
evidence as OR over explicit realizations (body/native, transliteration,
duplicates and supported TD3 fields), each requiring AND over its components.
Each component must be whole within the captured frame and not intersect an
applied synthetic mask. This remains a geometric visibility proxy, not an
independent human legibility judgment or universal proof of unobservability.
Do not claim first invention of multi-source fusion or LoRA.

Source semantics: author-labelled body fields and ICAO Doc9303 Part4 TD3 only.
https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf
Dates visible only in YYMMDD MRZ form do not justify inventing a century;
preserve that observed precision. Unspecified sex/filler-only values are omitted.
Optional/personal data is associated with a personal number only when author
values establish the association; do not assume every optional string is an ID.
Malformed or unrecognized MRZ formats are counted and excluded from MRZ links,
not silently repaired. No expected value is given to online inference.

## Controlled training and test

Keep the EXACT R2 image bytes, row IDs/order, prompt, selected input profile,
frozen model, optimizer,320steps, accumulation4 and seeds42/31415. Train two new
partial-image LoRA runs using source-aware targets. Compare them with R2 partial
runs of the same seed, which differ ONLY in reference policy during supervision.
R2 complete-content arms, original model and V1 transfer remain comparators.
Prefer visible body/native strings for training; use visible alternatives when
the body is unavailable. The allowable reference set includes all represented
visible strings, with date precision preserved. Report every changed target.
For dates choose the maximum explicitly visible year precision, then body/native
priority. Report both any-realization F1 and maximum-precision F1, so returning
a two-digit-year MRZ string when a four-digit-year body string exists is visible
in the results. These metrics do not treat an inferred century as observed text.

All eight models use the same images and prompt. Score R2's preregistered body
contract separately, then score all outputs under V3's explicit-source contract.
Cached original/R2 outputs may be reused when model/input/prompt match; this is
re-scoring, not a second independent inference run. Two V3 seeds are reported,
not selected by test. Source-aware dev F1 and unsupported/omission counts select
the web candidate before test; publish and verify BOTH model locks before any
test generation. Keep failures and negative findings.

Add practical CPU comparators: frozen RapidOCRv4/LatinV5 plus the existing global
printed-label matcher, with TD3 format parsing and with checksum-validated TD3
fallback. Only OCR text enters the online parser. No GT layout/type/boxes enter
CPU or VLM prediction. No automatic character repair, century inference or
identity approval. Report format-only versus checksum results separately.

Primary V3 effect: source-aware versus body-target partial LoRA, paired by seed
and ID, under source-aware references. Report correct fields, visible omissions,
wrong values, unsupported keys, empty-reference abstention, per-source/layout/
device/view slices and ID-cluster bootstrap CIs. Separate errors due to reference
policy from OCR/value errors; an unsupported body key need not be a hallucination.
Repeat fresh inference for the selected V3 model. R2 cache/prediction audits are
retained; V3 additionally verifies source derivation and identical input pixels.

## Claims and limits

This is an evaluated algorithm for building evidence-conditioned supervision
and comparisons, not a claim that one scalar OCR score establishes CORE B
novelty. Existing KIE-HVQA studies hallucination-aware training:
https://arxiv.org/abs/2506.20168 . MRZ fusion is established practice. Potential
contribution is the controlled measurement of reference-policy bias, explicit
multi-source/precision-aware references, and an inexpensive supervised remedy.
Only mock IDs and48 held-out identities are available, with two training seeds;
there is no new consented Vietnamese real-person corpus, no independent human
legibility GT, and no guarantee of unknown-pretraining or cross-camera coverage.
Do not broaden the evidence contract to every inferable/encoded fact on every ID.
