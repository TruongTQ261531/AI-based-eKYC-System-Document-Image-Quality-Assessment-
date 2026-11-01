# V2: photographed-source transfer and exposure-matched partial-field learning

Registered before V2 training or scoring the new test. V1 and mentor artifacts
are frozen. V2 has a separate branch, cache, labels, adapters, results and web.

## R2 amendment before any adapted-model development or test score

The first control42 pilot was stopped during annotation inspection (last periodic
progress284; last completed optimizer event286),
not after model evaluation. Author line components (birth_place_line*,
authority_line*, residence_line*) and bilingual/transliterated variants were
underrepresented by the first direct-key map. Keep that pilot's code/results
at commit5a325f2 and its original data/cache unchanged; it is not a primary run.
R2 uses separate vlm_lora_v2_r2 data/cache/results and restarts all four runs.
Group only explicitly author-named line components, joining their text and
convex hull. All fully visible author variants of a canonical key are acceptable
references; deterministic training prefers native spelling, then visible
alternatives. A masked variant does not invalidate another visible variant.
The optional17-key task, IDs, seeds, step budget and selection rule remain fixed.
Original-base panel predictions may be reused only when exact encoded image
hash, unchanged prompt and preprocessing contract match; re-score every output
against corrected author-derived references. Pilot LoRA weights are never reused.
No V2 adapted-model development score or test score was observed before this fix.

## Hypotheses and bounded design

H1: adding author-transcribed photographs and broader mock layouts improves
visible-field recall outside the V1 generator. H2: paired partial-field learning
reduces nonempty unsupported fields at matched training exposure. These are
empirical hypotheses, not promised results or a claim of first invention.
Related prior work already includes KIE-HVQA and hallucination-aware SFT/GRPO:
https://arxiv.org/abs/2506.20168 . Author dataset:
https://arxiv.org/abs/2107.00396 .

Training: 96 new authored SPECIMEN identities + 32 prior-study MIDV-2020 identities
with iPhone XS Max EXIF, excluding fin_id and lva_passport entirely. Earlier
studies' 80 MIDV identities are retired from V2 evaluation. All 40 untouched
identities among the already header-verified first 12 TAR entries per type are
acquired, independent of OCR outputs. Eight new iPhone identities, one per seen
type, are development. Test selects two remaining identities per seen type,
prioritizing Samsung SM-G973F, plus all eight identities of the two held-out
types. Remaining sources are unused. Test also has 24 new authored identities;
development has 16. Identity and raster overlap are checked. Device-stratified
results report actual EXIF; only the Samsung subset is device-held-out.

Each of two training arms uses the SAME 128 identities, 5 slots per identity,
sampling order, 320 optimizer steps, accumulation 4, two seeds 42 and 31415.
Exactly 1280 presentations = two complete epochs of 640 slots. Common slots
are full, perspective/background, mild blur/illumination. Complete-content
control has two further content-preserving variants; partial arm replaces those
two slots with field clipping and value masking. Both arms have equal steps,
ID exposure, view slots and optimizer hyperparameters. Actual token counts and
time can differ and are reported. No per-arm early checkpoint selection.
LoRA r8/alpha16 on frozen Vintern-1B-v3_5's language module; frozen visual features;
no new base weights, venv or global dependency installation.

The 17 optional output keys are declared in v2_common.KEYS. MIDV-2020 author
name/surname/number/id_number map to first_name/last_name/id_number/personal_number.
Other explicitly mapped author fields are included when geometrically whole;
unmapped native-language duplicates, MRZ, code, height etc. are excluded from
this bounded task, and coverage counts are reported. No per-image expected key,
document type, filename or ground-truth corner is supplied to the VLM.
MIDV-500/2019 author field01-style labels contain text and geometry but lack
semantic key names: they are inventoried, not silently promoted to KIE labels.

Ground truth after deterministic clipping/masking retains only whole value
regions. For authored mock images labels are also tracked; photographed MIDV
label boxes are unavailable. Geometry is a visibility proxy, NOT independently
human-verified legibility. Real photographs are of MOCK identity documents,
not a new consented Vietnamese real-person collection. Pretraining overlap is
unknown. At most generalization within this bounded public corpus is supported.

## Input comparison and lock

Before training compare raw2, raw4, rect2, rect4 on a fixed hash-selected panel
of 8 development identities (4 mock,4 photo), full + field_clip: 16 inputs.
Rectification uses existing FastViT/Module 2 predictions only, with raw fallback;
GT is never recomputed to excuse fields lost by the predictor. Two tiles fit
896x448, four fit896x896; each tile448px. Four-tile backward feasibility is
measured. Select highest tolerant key-value F1, then fewer unsupported values,
then lower measured latency; a profile that cannot train on this GPU is ineligible.
The same selected profile and prompt apply to all V2 arms and transfer baselines.

Training checkpoints at80/160/240/320; final320 is primary for EVERY arm/seed.
Dev selects which arm/seed can be offered on the research web; failed criteria
leave the new model opt-in. New test is sealed with source hashes, adapter hashes,
preprocessing and selection BEFORE scoring. Publish the lock to git before test.
Primary comparisons: original Vintern, V1 adapter42, V2 control42 and partial42.
Both second seeds are evaluated on all cases too, rather than chosen by test.
The recommended web gate requires higher dev F1 than both VLM transfer baselines,
at least the best CPU dev F1, and no more nonempty unsupported outputs than each
of those baselines. This conservative gate can legitimately reject deployment.

## Metrics, repeated checks and privacy

Test views: full, field_clip, value_mask, same identity pairing, 144 total inputs.
Primary format-tolerant parser removes only a whole JSON fence and null/empty
values, rejects duplicate keys and non-object syntax; no substring extraction,
spelling correction, field recovery or GT-dependent repair. Strict is secondary.
Report semantic KV precision/recall/F1, literal accuracy, visible omissions,
wrong visible values, nonempty unsupported outputs, exact-document rate, token
limit hits, source/view/device/held-layout slices and ID-cluster bootstrap CIs.
V2 corrects a scoring limitation discovered during source annotation inspection:
verbatim printed dates always count as correct, including short-year or
space-separated formats. Valid unambiguous numeric four-digit-year dates are
canonicalized; short-year dates do not receive an inferred century. V1 results
remain frozen; all V2 comparators use the same new scoring function.
Independent OCR V4/LatinV5 baselines remain CPU and use the identical inputs.
They are task baselines, not a claim of beating every current commercial service.
Cached-feature timing is separated from fresh preprocessing+vision+generation.
Fixed hash panel of 4 test IDs (two sources) repeats fresh inference twice for
the chosen web model; record every mismatch, OOM, retry and excluded case.

Private transcripts, labels, raw photographs, feature tensors, optimizer states
and weights stay in ignored local data/cache. Public numeric audit includes
hashes and counts, no raw identity values. Do not upload images of real users.
Camera UI is localhost-only; ephemeral image processing, editable observed
fields, no identity approval or liveness claim. Keep errors and negative results.
No CORE B acceptance guarantee is made; method novelty needs external review.
