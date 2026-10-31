# Auditing Information Loss in Partial Identity-Document Capture: Rectification, OCR Confidence and Field Extraction

Working manuscript. Venue decision pending; no claim of accepted CORE B status.

## Abstract

Mobile document systems can lose text when four-corner localization fails, yet forwarding or completing the card can be stronger than complex recovery. We investigate visibility-aware evaluation and bounded OCR view selection on 540 captures from 150 document IDs: 90 newly authored bilingual specimen identities and 60 additional MIDV identities. Development, calibration and test IDs are disjoint, with an additional font/field-order shift. Six original configuration IDs represent four style groups, not six independent spatial designs. We compare seven geometric views, two CPU OCR alternatives, naive confidence selection, linear/stump predictors and bounded cascades. We distinguish fully visible-field transcription, conservative visible-substring transcription, semantic schema extraction and review behaviour, and verify deployment using fresh online traces. All outcomes, code/model/input hashes, negative results and numeric rows are released. Primary cascades match completion accuracy in all four source/reader comparisons; rectification also loses to raw on the additional spatial layouts. A separate exploratory spatial field-assignment ablation improves canonical key-value exact from 66.67% to 76.27% on the authored test set and from 42.19% to 79.69% on the layout stress set, reusing the same OCR outputs. Its main-set comparison is post hoc. These findings support separating transcription, extraction and information-loss review; they do not establish new routing theory, document authenticity or PAD.

## 1. Research question and contribution boundary

When does completion or rereading preserve more useful text, and when is additional computation justified? The contribution under evaluation is the task/dataset/evaluation contract and an auditable implementation. Half-plane geometry, ridge regression, boosted stumps and cascades are established techniques. Algorithmic superiority must be supported by the held-out comparisons below, not presumed from a method name.

## 2. Related work

[DocAttentionRect](https://bmvc2025.bmva.org/proceedings/39/) and [ArbDR](https://github.com/chaoyunwang/ArbDR) already consider difficult document geometry; [DocRes](https://openaccess.thecvf.com/content/CVPR2024/html/Zhang_DocRes_A_Generalist_Model_Toward_Unifying_Document_Image_Restoration_Tasks_CVPR_2024_paper.html) studies general restoration. Missing boundaries alone are therefore not a new task. [MIDV-2020](https://arxiv.org/abs/2107.00396), [SIDTD](https://www.nature.com/articles/s41597-024-04160-9) and [DocXPand](https://github.com/quicksign/docxpand) also precede our generated specimen artifact.

[Kim, Han and Yang (IJDAR2026)](https://link.springer.com/article/10.1007/s10032-026-00620-7) separate visible/intended transcripts and study confidence-based OCR/VLM routing. We do not claim either idea as new. Our narrower setting concerns partial ID capture, spatially matched field transcription, semantic extraction, non-generative geometric rereading and measured CPU/review behaviour. Geometric character support differs materially from their human-legibility reference; neither label should be substituted for the other. The companion prior-work table distinguishes measured baselines from papers cited only as context.

## 3. Dataset and protocol

See DATASET_CARD_V4.md and RESEARCH_V4_PROTOCOL.md.540 cases;40/30/80 document IDs by role; two additional fresh24-case passes. Character support is a typography-derived geometric proxy, not human legibility. Synthetic examples and new-to-study MIDV images must remain separately labelled. Source training overlap is disclosed.

Separate frozen-model supplements comprise24 MIDV-UP physical photographs from four templates/two phones and80 authored captures from20 additional IDs with two-column/portrait layouts. They do not alter the primary fit, calibration or test results. Their sample size and language limitations are reported explicitly.

## 4. Methods

Pin two corner-localizer backbones and official CPU OCR code/weights. Generate seven prediction-only views. Fit competing view-quality and fallback-gain models with grouped development folds. Calibration selects confidence thresholds for80% target retention without a distribution-free safety claim. The primary cascade starts with padded completion and executes at most one alternative OCR view. No GT/template value lookup enters prediction.

### 4.1 Prediction and budget

Let x be the captured raster, v0 the completion view and Yv the OCR predictions for a candidate view. A regressor predicts the field-exact gain of a fallback v from features of Yv0 plus a one-hot view code. At inference it has no ground-truth transcript, document-type ID or annotated field locations. Features comprise raster size/aspect, observed corner count, text/confidence/edge statistics and view indicators.

`v* = argmax_v [ predicted_gain(features(Yv0), v) - 0.002 * development_mean_cost(v) ]`

Only if this quantity exceeds0.02 is v* executed; otherwise the completion output is returned. An identical raster skips duplicate OCR, while view construction can still incur overhead. The selected fallback is returned directly, without a third OCR pass or GT-based reranking. Ridge strengths0.1/1/10 and8/24 boosted-stump rounds are compared in four physical-ID-grouped development folds. The primary is the better development-CV cascade family. All-view ridge/stump and maximum-confidence alternatives are separate, costlier comparators.

### 4.2 Metrics and inference boundary

Primary field targets have valid Latin/alphanumeric text and at least99.5% geometric visibility. OCR always receives prediction-derived images, never reference field crops. Only the evaluator maps predicted boxes into source coordinates and assigns them to a reference field when prediction coverage is at least0.5 and IoU at least0.01. Reading order is evaluated in the reference field coordinate frame. Strings use NFC, uppercase and collapsed whitespace. CER micro is summed Levenshtein distance divided by summed reference length; it is not clipped or a per-image macro mean. Missing output counts as errors.

Semantic KIE instead compares predicted field keys and values without oracle box-to-key assignment. Dates/gender receive the documented canonical schema; raw literal results are retained. A secondary authored-data score evaluates surviving character-reference substrings. No-target images remain in the latency/review denominator. Confidence review is distinct from OCR output availability and from geometric truncation; it does not certify document completeness. Exploratory intervals use2000 physical-ID bootstrap resamples without multiplicity correction.

## 5. Results

The following primary choices were locked on development before test scoring. Values are pooled test-field exact; trace costs and actual online timings are distinct.

| Source | Latin method | Field exact | Trace wall seconds | Retention |
|---|---|---:|---:|---:|
| authored_specimen | completion | 80.00% | 1.148 | 100.00% |
| authored_specimen | cascade_stumps | 80.00% | 1.148 | 98.00% |
| midv2020_derived | completion | 57.29% | 2.325 | 100.00% |
| midv2020_derived | cascade_stumps | 57.29% | 2.325 | 28.89% |

All methods, paired ID intervals, semantic/visibility diagnostics and fresh online timings are reported in RECOVERY_RESULTS_VI.md and machine-readable artifacts. Do not replace these by best-test-only tables.

The locked primary cascades match completion accuracy in all four source/reader comparisons; algorithmic superiority is not supported. The learned routing result is retained as a negative experiment.

### Exploratory field-assignment application improvement

After seeing the V4 aggregate semantic gap, we added a separate printed-label right/below assignment alternative using existing aliases, typed validation and rectangular assignment. Its source and deployment choice are locked on development; all V4 main-set comparisons are post hoc. It reuses identical Latin completion OCR predictions and adds zero OCR calls. This is an application ablation, not new graph-learning theory.

| Source / role | Original key-value exact | Spatial assignment exact | Fields |
|---|---:|---:|---:|
| authored_specimen / test | 66.67% | 76.27% | 750 |
| authored_layout_stress / external_layout | 42.19% | 79.69% | 320 |

Per-target exact is recall-like. Exact extraction precision/recall/F1 on geometrically complete-field images, unexpected key counts and ID-clustered exploratory intervals are reported in the companion report. Values, document IDs and reference boxes never enter prediction. This additional parser does not retrospectively change the frozen primary cascade results.

## 6. Limitations and submission decision

The dataset contains few layouts/fonts and no newly collected real camera population. MIDV pretraining exposure is not excluded. Synthetic visibility differs from human legibility. The legacy reader check is panel-only and commercial systems are not tested. Classifier-based review does not verify full identity-document validity. A submission requires a convincing closest-prior distinction and adequate results across the declared trade-offs. Positive exploratory intervals alone cannot guarantee novelty, practical safety or conference acceptance.

## Reproducibility and ethical scope

Report exact code/model/data signatures, all ID roles, inference/repetition counts, source licences, processing settings and measured-versus-reconstructed times. Keep personal camera content local and memory-only. Publish only numerical results and clearly marked authored specimen examples. Mentor eKYC runtime is unchanged.
