# Priority 1: traceable field annotations and controlled transfer diagnostics

This is an annotation/data release in the existing project, not an algorithm
improvement claim. V1, V4, R2, V3, HP and fair_controls_v1 remain immutable.
All answers come from provider annotations or recorded rendering inputs;
OCR predictions never create or overwrite the evaluation references.

## Original corpus

Import every one of the 21,050 manifest images, including the 50 MIDV-2019
reference images explicitly assigned Clean. Preserve the native field names,
author strings, template polygons, card quadrilaterals, homographies, image
dimensions and hashes. The 50 physical documents shared by MIDV-500 and
MIDV-2019 define groups; reference pictures and video frames do not create
new identities. A fixed SHA order (seed namespace 20261104) assigns 30/10/10
physical-document groups to future train/development/test roles.

These are legacy data exposed to earlier quality/geometry/OCR work. These
new role names do not make them an unseen test for an existing model. Keep
the old quality split in provenance; never promote Clean/Blur to transcripts
or readability judgments. Reference values stay available when their regions
are outside the image, but must be distinguished from observed transcriptions.

Provider positions on captured frames are template-to-card projections, not
independently annotated per-frame text boxes. Frame intersection is measurable;
blur, glare, local occlusion, script knowledge and human readability are not
inferred from that intersection. Font identity in captured images stays unknown.
All unreviewed readability labels are explicitly unassessed.

## New controlled diagnostics

Create 32 new fictional identities (8 development, 24 test), disjoint from
all previous author-rendered values and ID namespaces. Each is rendered in a
paired 2x2 layout/value-font design, with a full and a value-masked capture:
256 views. Seen geometry uses the prior vertical body arrangement; held
geometry places values around a central portrait. Seen value fonts are the
previous Noto Sans/Noto Serif files; held value fonts are Tahoma/Times New
Roman available on this Windows machine. Hash and check Unicode glyph coverage;
do not redistribute Windows font files. Labels, identity content, background,
field order, per-field font size and chosen masked semantic key are controlled
within an identity. Choose font sizes to fit both geometries and both fonts.
Report font novelty relative to local fine-tuning, not unknown pretraining.

Rendering records every value region and its ink/glyph support. A mask erases
one value while preserving its label and other value ink. These construction
facts are labeled separately from human readability. Keep partial/absent
observations distinct from the complete underlying author answer.

Acquire 24 additional MIDV-2020 instances, using photo/template TAR members
19/20 of each type and member21 in four SHA-ranked types. Verify author member
headers/sizes, per-image SHA256 and identity/content/pixel overlap with previous
study roles. This is new selection from the existing public collection, not
a newly self-captured camera population. Use one of the new instances from
each of the eight known training document types for development; the other
16 are test. Evaluate full and deterministic single-value-masked views (48).
Choose a mask by the fewest additional semantic keys lost, then a fixed SHA
rank of the identity/key; mask every declared realization of the chosen key.
Keep provider body/MRZ source variants, multiple components and unknown fonts.
The complete planned panel is 304 views, 56 physical-document instances:
80 development views and 224 test views. No case is removed after seeing OCR.

## Frozen readers and endpoints

Before any new OCR prediction, publish the prepared data/model/analysis lock.
Use the current partial_42 Vintern adapter, unchanged rect2 and 384 generation
tokens; and the existing CPU RapidOCR v4/v5 readers with the unchanged global
label/spatial parser and strict TD3 missing-key fallback. Each predictor takes
only image pixels. Ground-truth field positions are used only for scoring and
annotation inspection. No new training, threshold search or model promotion.
Report every invalid JSON, empty result and exhausted generation budget.

Use the unchanged source-aware 17-key semantic scoring on the bounded panel,
including all supported author variants. Preserve all native fields in the
annotation corpus; report semantic coverage/exclusions instead of inventing
meaning for positional field01 keys. Native-field annotation coverage and
semantic extraction accuracy are different quantities.

Report layout and font effects separately on complete synthetic captures,
within ID, and the layout-by-font interaction; report masks separately. Publish
the two CPU readers and VLM separately, with identity-cluster bootstrap
intervals (10,000 draws; seed20261109). Primary endpoints are descriptive field
F1/exact values; no superiority or human-legibility claim is registered.
Public-photo transfer is a separate source diagnostic, not an isolated causal
camera effect. Two repeated fresh panel reads per model on four fixed images
(one authored and one photographed ID, full/masked) add 24 calls; keep their
small timing/reproducibility panel separate from the main sample size.

## Verification, privacy and review

Audit all manifest coverage and all source file hashes. Independently rebuild
field values/geometry from provider references; rebuild every authored raster
and mask from its saved inputs. Audit every score row from private raw outputs,
including malformed outputs, and verify the registered roles/grouping and frozen
history. Keep text, images, individual review exports and weights local; publish
only schemas, code, aggregates and hashes. Full scientific calls, fresh repeats,
visual encoder work and rescoring have separate counters. Append a begin/end
event for each actual main/fresh OCR invocation, and disclose failed attempts
or interrupted attempts whose end state is unknown. Cache resumes do not create
new inference calls. Record file-decode time separately from the decoded-pixel
rectification/OCR/parser timer; model loading is outside per-image latency.

Provide a localhost annotation viewer and blinded review tasks with native
fields, observed transcription, reading language and readability state. Reviews
are append-only proposals in a separate database, not silent edits of a released
reference or old test result. Two reviewer codes are not proof of two humans;
independence is self-declared and actual human evidence must be reported as such.
No actual independent reviewers are available at registration. Test fixtures and
automatic OCR agreement never count as human responses. A strict human-verified
export must honestly be empty until suitable reviews are received.

The deliverables can complete the annotation infrastructure and automated data
checks. Independent human legibility verification and a consented new camera
collection remain external evidence requirements; do not claim they were done.

Sources: [MIDV-2020 author paper](https://arxiv.org/abs/2107.00396),
[author dataset page](https://smartengines.ru/science/dataset/).
Retain MIDV attribution and the original CC BY-SA 2.5 conditions. Provider FTP
blocks have checked entry/header integrity; no claim is made that the entire
remote archive checksum was independently recomputed.
