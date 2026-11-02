# Same Pixels, Different Evidence: Auditing Reference Policies for Partial ID-Document Extraction

Working research manuscript. No authors, conference acceptance or independent human annotation is implied.

## Abstract

A partially captured identity document can retain the same information in a body field, a declared translation, or a machine-readable zone (MRZ). A reference tied to a single body field can therefore treat an explicitly supported answer as outside its contract. We investigate this reference-policy effect and an inexpensive supervision intervention using the same pixels, ordered identity exposure and optimizer budget. Our benchmark separates 128 training, 24 development and 48 test identities, combining authored specimens and photographed MIDV-2020 mock documents. Six matched-budget LoRA runs use two seeds and three training conditions on a pinned 938-million-parameter Vintern model. We compare eight VLM configurations and six CPU OCR/postprocessing configurations, without counting shared OCR or re-scored outputs as independent inference runs. Source-aware references contain 682 test fields versus 599 under body references. Source-supervised test F1 is 0.3947/0.4063, versus 0.3786/0.3978 for matched body-partial supervision. The two-seed comparisons do not jointly establish a positive source-supervision effect; no general superiority claim is supported. These findings concern bounded extraction references, not document authenticity, human legibility or certified eKYC.

## 1. Question and contribution boundary

We ask two separate questions: (RQ1) how does a declared evidence policy change the evaluation of identical model outputs; and (RQ2) does source-aware supervision improve extraction when all input pixels and image/update exposure are held fixed? RQ1 is a descriptive measurement analysis; RQ2 is the prospective matched intervention. The contribution candidate is the auditable reference-policy evaluation and controlled evidence, rather than a claim to invent MRZ parsing, logical visibility operators, LoRA or OCR fusion. A useful negative intervention result must remain a negative result.

## 2. Related work

[KIE-HVQA](https://arxiv.org/abs/2506.20168) already studies key-information extraction under degraded visual evidence and training-based hallucination mitigation. [BoundingDocs](https://flore.unifi.it/retrieve/271bfa4d-4b12-4bd3-8ec1-a5f64ce8ca0b/s10032-025-00563-5.pdf) allows multiple answer locations and audits semantic matches. Consequently, multiple locations and visibility-aware evaluation are not first contributions here. [OCR redundancy modelling](https://arxiv.org/abs/2508.14557) concerns character-shape statistical redundancy; it should not be described as the same semantic MRZ intervention. [MIDV-2020](https://arxiv.org/abs/2107.00396) supplies public mock-document photographs and author annotations. [ICAO Doc 9303 Part 4](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf) defines TD3. Our comparison is narrower: preserving explicit alternative realizations, date precision and inference provenance on partial identity-document captures under a matched-pixel training design.

## 3. Data and evidence contract

| Role | Identities | Views | Source composition |
|---|---:|---:|---|
| Train, each arm | 128 | 640 slots | 96 authored + 32 photographed mock IDs |
| Development | 24 | 72 | 16 authored + 8 photographed mock IDs |
| Test | 48 | 144 | 24 authored + 24 photographed mock IDs |

Each train identity has five ordered slots. Two slots differ between complete-content and partial-content exposure; three are byte-identical. R2 body-partial and V3 source-partial use the entire identical pixel sequence. Here an identity/ID denotes a grouped document instance, not an independently verified natural person. Document-instance separation does not establish an unseen biometric population. Test includes fourteen Samsung captures absent from train and eight held-layout identities; these small strata are reported separately rather than called a broad cross-camera population. Earlier-study photo overlap is excluded from development/test. Unknown base-model pretraining overlap cannot be ruled out.

For key k, a realization is a literal value with an explicit author-associated source and one or more actual line polygons. A realization is geometrically visible if every transformed component vertex lies inside the capture and every synthetic-mask intersection is at most 0.05 pixel-squared. Components combine with AND; declared alternative realizations combine with OR. The area threshold is a numerical tolerance, not five percent visibility. Unrelated fields are not linked merely because their text happens to match. Author-linked translations, narrowly declared duplicate values and TD3 character spans supplement body fields. Optional TD3 data is not presumed to be a personal number at inference.

Targets prefer the maximum explicitly printed date precision, then native body values, declared alternatives and MRZ. A YYMMDD date does not expose its century. Any-source F1 and maximum-date-precision F1 are both reported. A geometric support label does not establish legibility after blur, glare, resampling or rectification. No independent human-legibility labels have been obtained.

## 4. Intervention and baselines

The complete pinned model is 5CD-AI/Vintern-1B-v3_5, revision `b98f263eab246eb5269ade64edbdca8a887dc44d`, with 938,193,024 parameters. The vision encoder/projector are frozen; rank-8, alpha-16, zero-dropout LoRA updates 1,081,344 language-module parameters in q/k/v/o projections. Each run starts from the same base and performs 320 AdamW updates, four-image accumulation and exactly 1,280 presentations. Seeds are 42 and 31415; learning rate is 0.0002 and weight decay 0.01. Final step 320 is always used. Equal image/update exposure does not imply equal answer tokens; actual loss-token exposure and wall/memory counters are released separately.

Four raw/rectified, two/four-tile profiles were compared on a fixed development panel before training. The selected rect2 profile is fixed across all configurations. Rectification uses predicted geometry and existing completion/raw fallback, never author corners. Frozen visual features accelerate training and benchmark generation; every referenced feature is freshly re-extracted for audit. Additional pixel-level repetitions distinguish cache-only generation timing from actual image-processing latency.

The eight VLM comparators are the original model, V1 task-transfer adapter, two complete-content R2 adapters, two body-partial R2 adapters and two source-partial V3 adapters. Six R2 outputs are re-scored under the V3 contract; they are not six additional inference experiments. CPU baselines use rapid_v4 and rapid_latin_v5, each with body extraction, MRZ-format fallback or checksum-validated fallback. Three postprocessors share one OCR execution. A separately registered secondary baseline fills missing VLM keys from the same rapid_v4 MRZ output, without overwriting fields, repairing characters or inventing a century. It is established engineering, not new fusion theory.

## 5. Evaluation and results

Micro precision/recall/F1, date precision, omissions, wrong values, outside-contract keys, JSON validity and empty-abstention behavior are retained. Outside-contract does not prove hallucination or absence from every possible encoded source. Paired intervals use 10,000 identity-cluster bootstrap resamples, stratified 24 authored + 24 photographed test identities. These quantify test-sample uncertainty, not all training uncertainty. Two seeds are reported independently. Model/input/code locks were remotely verified before any test generation.

| VLM configuration | Source F1 | Max-date-precision F1 | Omissions | Wrong values | Outside contract |
|---|---:|---:|---:|---:|---:|
| original | 0.1757 | 0.1757 | 52 | 374 | 1602 |
| v1 | 0.3413 | 0.3413 | 427 | 76 | 112 |
| control_42 | 0.3644 | 0.3644 | 95 | 292 | 350 |
| partial_42 | 0.3786 | 0.3786 | 175 | 241 | 216 |
| control_31415 | 0.3670 | 0.3670 | 116 | 277 | 327 |
| partial_31415 | 0.3978 | 0.3978 | 148 | 248 | 222 |
| source_42 | 0.3947 | 0.3947 | 162 | 238 | 227 |
| source_31415 | 0.4063 | 0.4063 | 140 | 244 | 243 |

| CPU recognizer / postprocessor | Source F1 | Max-date-precision F1 |
|---|---:|---:|
| rapid_latin_v5/body | 0.1916 | 0.1916 |
| rapid_latin_v5/mrz_checks | 0.2256 | 0.2180 |
| rapid_latin_v5/mrz_format | 0.2256 | 0.2180 |
| rapid_v4/body | 0.1938 | 0.1938 |
| rapid_v4/mrz_checks | 0.2834 | 0.2621 |
| rapid_v4/mrz_format | 0.2834 | 0.2621 |

| Paired source-reference comparison | Delta F1 [95% ID-bootstrap interval] |
|---|---:|
| source_42 minus partial_42 | +0.0160 [-0.000010, +0.032228] |
| source_31415 minus partial_31415 | +0.0085 [-0.016845, +0.033900] |
| source_42 minus control_42 | +0.0303 [+0.002887, +0.058913] |
| source_42 minus v1 | +0.0534 [+0.012476, +0.098482] |

For the original body-reference R2 intervention, the independently retained paired results are:

| Partial minus complete, seed | Delta F1 [95% interval] |
|---|---:|
| partial_42 minus control_42 | +0.0212 [-0.003897, +0.047746] |
| partial_31415 minus control_31415 | +0.0291 [-0.004799, +0.064496] |

The two-seed comparisons do not jointly establish a positive source-supervision effect; no general superiority claim is supported.
The descriptive reference-policy transition matrix keeps each predicted string fixed and separately records formerly outside-contract answers that become supported and newly counted fields that remain omitted. It is post-hoc description and never selects a checkpoint or deployment rule. Full source/device/layout/view strata, all secondary fusion configurations, costs and the transition matrix accompany the Vietnamese results report.

## 6. Local application and verification

Development selected `partial_42`. Its deployment gate is `False` and secondary fusion promotion is `False`. When the gate is false, the web requires an explicit research-mode opt-in rather than presenting the model as validated eKYC. Image values are generated from pixels, never retrieved by matching an image to dataset identities. Only returned keys are populated; edits/additions retain manual provenance. Camera images and text are ephemeral, served at localhost with bounded requests and host/origin checks. OCR is not identity or liveness approval.

The source-contract audit replays 3024 score rows; 432 independently executed CPU pairs agree. Sixteen additional selected-model pixel-level calls on eight inputs/four identities have 0 output mismatches, with p50 10.12s and p95 16.81s. The R2 and V3 repeat panels may share inputs and the selected model; they are not additional independent identities. Shared OCR, raw-output rescoring and checksum postprocessing are reported separately from model calls. Mocked browser/camera tests and specimen demonstrations establish software behavior, not camera-population accuracy.

## 7. Limitations and reproducibility

This study has one small backbone, two seeds, few layouts/fonts and 48 test identities. Authored rasters and public photographed mock documents cannot substitute for a newly consented Vietnamese camera collection. Independent human legibility review and physical-user camera testing remain unperformed. A blinded 48-image review tool is provided for future annotation; automated UI answers are never counted as human labels. The source graph is deliberately bounded by declared author regions/TD3 associations and excludes arbitrary inference from QR codes or facial appearance. GPU/CPU times are hardware- and execution-path-specific; some CPU baselines run concurrently with GPU work, and allocated/reserved counters are not total physical VRAM. The full dataset/font/model provenance, original failed pilot, preprocessing choice, matched budgets, negative results, numeric rows and hashes are retained. Public code and numeric artifacts exclude camera PII, raw dataset images and weights; the pinned complete model and adapter instructions remain reproducible from the documented local assets. These limits constrain claims and do not establish CORE B acceptance.

## Artifact links

- [Method specification](V3_METHOD.md), [primary protocol](V3_PROTOCOL.md), [secondary protocol](V3_FUSION_PROTOCOL.md).
- [Measured results and limits](V3_RESULTS_VI.md), [R2 results](V2_RESULTS_VI.md), [runbook](V3_RUNBOOK.md).
- [Source audit](results/source_visibility_v3/audit.json), [source intervals](results/source_visibility_v3/paired_intervals.json).
- [Reference-policy transitions](results/source_visibility_v3/reference_policy_diagnostics.json).
- [Human review status](V3_HUMAN_REVIEW.md).


## Exploratory mechanism diagnostic: newly supported fields

This post-hoc descriptive subset contains keys absent from body references but supported by an explicit remaining source under V3. It does not select a model or replace overall F1. Only 22/640 partial-training slots changed targets, limiting the intervention exposure. Multiple fields/views from one document are correlated; field counts are not independent identities. Any subset benefit must be weighed against errors on the remaining test fields.

| Configuration | New reference fields | Correct | Wrong value | Omitted | Subset recall |
|---|---:|---:|---:|---:|---:|
| original | 83 | 9 | 59 | 15 | 0.1084 |
| v1 | 83 | 1 | 18 | 64 | 0.0120 |
| control_42 | 83 | 5 | 62 | 16 | 0.0602 |
| partial_42 | 83 | 2 | 56 | 25 | 0.0241 |
| control_31415 | 83 | 4 | 55 | 24 | 0.0482 |
| partial_31415 | 83 | 6 | 58 | 19 | 0.0723 |
| source_42 | 83 | 7 | 56 | 20 | 0.0843 |
| source_31415 | 83 | 15 | 62 | 6 | 0.1807 |


## Generation budget diagnostic

All eight VLM configurations use the same fixed maximum of 384 new tokens. A limit-hit flag denotes budget exhaustion, not proof of hallucination or a diagnosis of the error cause. The limit is not tuned after test release. This table is descriptive and introduces no new generation calls.

| Configuration | Test calls | Limit hits | Median generated tokens |
|---|---:|---:|---:|
| original | 144 | 5 | 195.5 |
| v1 | 144 | 0 | 29.0 |
| control_42 | 144 | 1 | 67.5 |
| partial_42 | 144 | 0 | 61.0 |
| control_31415 | 144 | 2 | 65.0 |
| partial_31415 | 144 | 1 | 63.0 |
| source_42 | 144 | 1 | 64.0 |
| source_31415 | 144 | 0 | 63.0 |


## Exploratory reference-contract interaction

Using the same fixed outputs, this post-hoc analysis compares the measured partial-versus-complete training gain under body and source references. The interaction is source-contract gain minus body-contract gain. It is not a new training trial, model-selection criterion or proof that earlier published annotations are erroneous. Intervals use 10,000 paired document-instance bootstrap resamples, source-stratified 24+24, seed 20261103, without multiplicity correction. Both training seeds are retained regardless of the direction.

| Seed | Body-reference gain | Source-reference gain | Gain change | Exploratory 95% interval |
|---|---:|---:|---:|---:|
| 42 | +0.0212 | +0.0142 | -0.0069 | [-0.014497, -0.000292] |
| 31415 | +0.0291 | +0.0308 | +0.0017 | [-0.005499, +0.010156] |

Both configured CPU body-only pipelines have zero photographed-subset KIE F1. They measure OCR plus a limited English/Vietnamese printed-alias matcher, not standalone character recognition accuracy. These outcomes do not establish superiority over all modern OCR or language/document-specific information extractors.


## Availability incident and timing sensitivity

Windows recorded a battery-triggered sleep from 09:25:46 UTC to 14:45:48 UTC on 2026-11-02. One V1 generation includes the suspension interval in its raw wall timer. All original outputs, hashes, accuracy rows and raw timers remain unchanged. Companion reports give both raw latency and a post-hoc sensitivity statistic excluding only the independently documented interrupted generation. This is not exclusion of difficult or incorrect OCR cases. Power/GPU operating conditions were not controlled across the run, so these descriptive times do not support model-speed superiority.
An additional same-model/image/profile cached-feature generation replays the affected case: 1 call(s), 0 hash mismatch(es). This incident check is separate from pixel-level fresh repeats and never replaces the primary output.


## Post-hoc CPU label-position sensitivity

The original test summaries were already observed before this diagnostic was designed. Two alias-prefix normalization variants reuse the original aliases and spatial assignment, each with/without the existing strict MRZ fallback, for both readers. No new neural calls are made. This is a simple-head sensitivity diagnostic, not an independent confirmatory test or SOTA KIE baseline. Original primary results and deployment selection are unchanged. Timers sum the existing OCR cost and new parsing cost rather than measuring a fresh end-to-end request. All eight outcomes are retained.

| Supplemental configuration | Development F1 | Test F1 | Outside-contract keys |
|---|---:|---:|---:|
| rapid_v4/search/body | 0.2537 | 0.1990 | 1 |
| rapid_v4/search/mrz_checks | 0.3125 | 0.2874 | 1 |
| rapid_v4/bilingual/body | 0.2537 | 0.2039 | 1 |
| rapid_v4/bilingual/mrz_checks | 0.3125 | 0.2921 | 1 |
| rapid_latin_v5/search/body | 0.2537 | 0.2047 | 5 |
| rapid_latin_v5/search/mrz_checks | 0.2537 | 0.2373 | 5 |
| rapid_latin_v5/bilingual/body | 0.2537 | 0.2047 | 5 |
| rapid_latin_v5/bilingual/mrz_checks | 0.2537 | 0.2373 | 5 |

The supplemental development choice is `rapid_v4/search/mrz_checks`. 1728 derived rows were replayed, with zero new neural calls. The [supplement protocol](V3_CPU_LABEL_SUPPLEMENT.md) states the post-hoc boundary explicitly.
