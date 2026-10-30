# Partial document capture: dataset card

## What this release contributes

A versioned experiment artifact for a precise question: how much **visible
information** survives geometric recovery when a captured document is clipped?
It couples full references, conservative visible-substring references,
geometry, semantic fields, disjoint document IDs and measurable execution cost.
This is a candidate dataset contribution, not an established world-first claim.

| Source | Documents | Captures | Conditions |
|---|---:|---:|---|
| Newly authored SPECIMEN documents |90|360|Full, corner clip, field clip, blur/glare|
| Additional author MIDV-2020 photos |60|180|Original, corner clip, field clip|
| Total |150|540|Two sources, separately reported|

The authored cards cover three mock document families, six configuration IDs and
English/Vietnamese labels.90 mock document identities are not90 human subjects.
Text values are fictitious; avatars are simple illustrations. No state seals,
authentic credentials, biometric evaluation or genuine identity approval.
SPECIMEN and NOT A VALID DOCUMENT are visibly printed on every authored card.

Physical-document roles are40 development,30 calibration,80 test. All captures
of one ID stay in one role.20 authored development IDs and20 calibration IDs
use configurations0..3. Test includes20 other IDs from these configurations and30 IDs from
configurations4..5. Configurations0/2 share slot geometry and language/font;
1/3 also share them. Thus there are four language/font/order groups, not six
independent spatial layouts. The two held-out configurations change font and
field order; this is a combined shift, not isolation of spatial layout alone.
The correction is recorded in RECOVERY_EVALUATION_ADDENDUM.md, preserving the
frozen generator and all540 original images. Common label/name vocabularies can overlap roles; image and
document-ID separation does not imply every word is unseen.

Two supplements do not change those primary roles or fit any model. The
layout stress set adds80 authored captures from20 new mock document IDs with
two genuinely different arrangements: two columns and portrait format. It
has its own protocol and two fresh8-image panel passes. MIDV-UP adds24 real
author photographs from four additional template types and two phone strata;
all24 are evaluated twice. Neither is a new self-collected camera population.
See RECOVERY_LAYOUT_STRESS_PROTOCOL.md and RECOVERY_EXTERNAL_UP_PROTOCOL.md.

Per MIDV type, inspect only the first12 source-TAR entries, exclude the earlier
study's two IDs, choose six by the locked hash and assign2/1/3 roles by that
order. This is a bounded sample of60 IDs, not a random sample of all1000 MIDV
identities. The60 are new to this study, not verified unseen in pretraining.
Template types overlap roles. No new real-world camera data was collected by
this generator; the localhost demo is not a substitute for a new capture study.

## Labels and target contracts

Each local record contains original/capture hashes, dimensions, capture
transform, document quadrilateral, field keys/values/quads and role. Authored
records additionally contain character support rectangles and both full and
visible references. Values and predictions stay in Git-ignored local data/cache;
released manifests expose numeric attributes and hashes. Authored SPECIMEN
examples can be published explicitly because they do not contain real PII.

Character rectangles use font advances and typographic bounding boxes. They
are **geometric support proxies**, not exact glyph pixel masks or human
legibility judgements. Visibility is polygon intersection with the capture
frame; a character is retained at.995 area fraction. Blur/glare severity does
not automatically redefine the reference or make difficult characters vanish.

Primary spatial transcription evaluates fully geometrically visible Latin
fields, preserving the previous experiment's exact/CER contract. Images with
no eligible fields remain in latency/routing counts. Secondary visible-reference
transcription includes surviving substrings of partially cut authored fields;
it is reported separately, never substituted after observing outcomes.
Semantic KIE is evaluated separately on authored keys, with explicit date/gender
schema normalization. It never receives GT field positions or expected values.
No universal mandatory CCCD schema is imposed on other document families.

Truncation diagnostics disclose how often a fixed review flag retains an image
with a clipped annotated field. They are not legal document-validity decisions.

## Provenance, licences and reproducibility

- [MIDV-2020 author paper](https://arxiv.org/abs/2107.00396), source archive
  `ftp://smartengines.com/midv-2020/dataset/photo.tar` and author template TAR.
  Author `license.txt` declares **CC BY-SA2.5 Generic**, encourages attribution
  of the artificially generated faces to [Generated Photos](https://generated.photos/).
  Retain that attribution for MIDV derivatives; do not relabel them as MIT or
  as newly collected photographs. Archive headers/entry sizes and local SHA256
  are checked, but whole-archive MD5 is not verified with bounded reads.
- Authored generator code follows this repository's MIT licence. Newly authored
  specimen images are offered under **CC BY4.0**, attributed to this project.
  This licence statement does not change upstream MIDV/font/model licences.
- Noto Sans and Noto Serif are sourced from the official Noto repository,
  with font hashes recorded and their OFL attribution retained. Font binaries
  are not included in this Git release.
- `recovery_setup.py` checks pinned assets; `--data` recreates acquisition and
  generation without installing packages. `recovery_data.py` produces the540
  deterministic cases. Model/code/input hashes bind the locked experiment.

The raw MIDV images, original reference strings, user camera images and model
weights are not uploaded to GitHub. The source hashes, public manifests,
regeneration scripts and a few clearly labelled authored examples are released.
This artifact is not an independent manually annotated dataset of real
Vietnamese CCCD, screen attacks, faces or document authenticity.

## Evidence required before a dataset-paper claim

Demonstrate a distinction from existing partial-boundary/quality datasets;
measure annotation validity on held-out samples; release regeneration and
splits; show useful results across independent readers. More real cameras,
backgrounds, document designs and consented new captures would strengthen
external validity. Synthetic cardinality alone does not establish sufficient
dataset novelty for a CORE B paper.
