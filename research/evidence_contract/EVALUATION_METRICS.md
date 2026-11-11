# TASK 4 — Evaluation metrics and denominators

`evaluator.py` consumes stored outputs, graphs, oracle decisions, actual invocation events and optional measured worker-process costs. It contains no reader loader. Metrics retain numerator/denominator/scale; denominator zero gives JSON `null` (not a misleading zero error rate).

## Units

| Unit | Identity and interpretation |
|---|---|
| Physical ID | Hashed physical-document identity; multiple images/fields are not independent documents |
| Image | Unique decoded RGB pixel SHA; file SHA additionally binds input provenance/cache |
| Reader view | Pixel SHA + full reader fingerprint; distinct model/config/code/runtime identities are separate |
| Field observation | Reader view + explicit semantic key, deduplicated across contract reuses; conflicting duplicate annotations stop aggregation |
| Generated pair | Graph + mutation + original/follow-up pixel hashes; retained even when invalid/unknown |
| Contract evaluation | One paired contract/key × reader; deduplicated by bound decision hash |
| Inference call | One `inference_begin` for a pixels-only image-reader invocation. Includes failed/ambiguous attempts. Internal OCR detector/recognizer and autoregressive token forwards are not measured as separate calls |
| Behavior cluster | Independently adjudicated cluster, or a conservative fingerprint of physical ID/contract/key/category/reader. **Not** an identified software bug |
| Defect | Independently verified root-cause identity with patch/revert or seeded-fault activation evidence |

Repeated references to the original image across C1–C4 do not multiply inference or field counts. Pair validity is model-independent; output/reader binding eligibility is recorded separately. All injected oracle-unit outputs, fields and call events are excluded from actual-model metrics by origin.

## Detection metrics

Let alarms retain their original issued flag even if independent review later rejects them.

| Metric | Numerator / denominator |
|---|---|
| Verified failure count | Number of `CONFIRMED_VIOLATION` contract evaluations, not merely emitted alarms |
| Unique failure clusters | Unique verified behavior fingerprints/adjudicated clusters; separate from unique defects |
| Alarm precision | TP / (TP + FP) among adjudicated issued alarms. TP: independent failure label AND valid test. FP: independent non-failure label OR independently invalid test. Unknown positive labels lacking validity do not become TP |
| Alarm recall | Issued alarms on independently known valid failures / all independently known valid failures. A PASS/INCONCLUSIVE on a known failure is FN |
| False-alarm rate | Issued alarms on independently known valid negatives / all independently known valid negatives |
| Invalid-test alarm rate | Issued alarms on independently invalid attempts / all independently invalid attempts; reported separately from valid-negative FAR, while still burdening precision |
| Label coverage | Adjudicable alarms / issued alarms; and adjudicable decisions / decisions. Unlabelled alarm count is explicit |
| Valid-test rate | Evaluations meeting known mutation/output/adjudication preconditions / all contract evaluations |
| Generated-pair valid rate | Valid TASK3 mutation pairs / all attempted unique pairs; independent of number of readers |
| Inconclusive rate | Final INCONCLUSIVE verdicts / all contract evaluations; candidate alarms have their own count |
| Errors detected per100 calls | 100 × verified failure count / originating image-reader invocations |
| Clusters/defects per100 calls | Same budget denominator; numerators are unique verified behavior clusters or verified defects respectively |
| Verified defects/runtime | Unique verified defects / measured seconds, separately for cold-inclusive invocation/loading costs and end-to-end fresh worker process costs |

No independent failure labels means alarm precision, recall and FAR are **NA/null**. No confirmed faults with a positive known budget gives defect yield zero; it does not establish good system quality. A failed/ambiguous attempt consumes call budget. Unknown runtime is not silently zeroed: the runtime-dependent yield is unavailable when the required duration is incomplete.

## Field accuracy, F1 and CER

These scores are scoped to declared, supported source references and known removed fields. Construction support is explicitly not human readability or universal natural-document GT. Unannotated predicted keys remain `unjudged_predicted_key_view_count`; a partial source graph is not a complete list of all fields printed on a card.

Visible reference value is chosen deterministically from supported sources, preferring full-date precision when actually supported, then source ID. An inaccessible full reference is not substituted when only a reduced-precision source survives. Field support/conflicts and typed semantic/date precision are assessed by unchanged TASK3 code.

Literal normalization: Unicode NFC and collapsed whitespace, **case-sensitive**, no aliases/century inference. Exact match = correct supported key/value observations / all supported references. Semantic match is reported separately through TASK3 `assessment`; do not conflate the two.

Micro keyed-value F1 uses TP for a present exact key/value match; an incorrect supported value incurs FP+FN; a missing supported value incurs FN; a prediction on a known removed field incurs FP. Unknown/unannotated fields are unjudged. Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN). These are partial-universe scores, not whole-card KIE precision.

CER = sum Unicode Levenshtein edits / sum visible-reference characters. Missing output uses an empty prediction; the ratio can exceed1. Removed fields have no readable text reference and do not enter the CER denominator. Unusable JSON counts supported references as missed in end-to-end accuracy/CER, with separate conditional-on-usable-output accuracy and JSON-valid rates. It is not reported as a verified semantic omission. `missing_fields` is unknown on unusable output; there is no hardcoded CCCD field list.

## Budgets and runtime

Every public metric distinguishes:

1. Originating calls used for the stored results, including failed/ambiguous begins.
2. New calls in selected run IDs. Resume/replay have zero; they are not an infinite zero-cost improvement in errors/call.
3. Invocation-wrapper seconds from terminal events, including the predictor and raw-cache commit cost.
4. Model-load seconds, including the adapter's repeated read-only checks.
5. Cold-inclusive seconds = 3+4; excludes initial CLI preflight/import/startup.
6. Fresh worker-process seconds from subprocess measurement, including startup/import/initial preflight/load/inference/cache I/O; excludes fixture construction and scoring. Complete generation/annotation/review cost is not instrumented in this smoke.

Native prediction latency/CPU time and Vintern memory/token metadata remain in private normalized raw records; public runner summaries expose measured latency and model/input/code/config hashes. Model loading is never charged once per field/pair. Contract/source groups share calls; their totals and shared cold/process costs are **non-additive**. `budget.neural_internal_forward_passes=null` makes the granularity explicit.

Grouping is available by contract, source kind, reader, construction/human/unknown readability and document source group. Multi-source/multi-contract buckets overlap. No significance test, bootstrap, or independent sample-size claim is made on a single physical ID.

## Determinism and reproducibility

Generator seed42 and input files/pixels are frozen before reader execution. Same full-image input is used for each reader; the existing predicted rectification is part of the SUT. Baseline package/model/config/prompt/code/runtime hashes are bound into the inference fingerprint; scoring code hashes are separate. Raw-cache identity deliberately excludes the oracle/evaluator/normalization implementation so re-analysis requires no OCR call.

Vintern uses existing greedy decoding and deterministic CUDA configuration; RapidOCR uses its existing CPU providers/thread limits. Driver/hardware, mixed precision, ONNX/CUDA kernels, scheduling, I/O and load order remain potential nondeterminism/latency sources. Cache replay equality is **not** a fresh-inference determinism experiment. This task did not repeat fresh model calls or estimate latency variance, tune warmup, compare statistically independent documents, or change settings based on scores.

## Actual smoke, not confirmatory evidence

One fictional ID; 4 images (original, body-only mask, all-declared-sources mask, padding translation); 4 pairs (C1–C4). C1 and C3 intentionally reuse one masked raster. Three readers give 12 image-reader calls, 12 contract evaluations and 24 unique field-reader views:21 supported reference fields and3 known removed fields.

| Reader | Calls | PASS / candidate / inconclusive | Literal exact match | Literal F1 | CER | Invocation wrapper s | Load s | Fresh worker s |
|---|---:|---|---|---:|---:|---:|---:|---:|
| RapidOCR v4 | 4 | 1 / 1 / 2 | 0/7 | 0.0000 | 0.1724 | 11.747 | 22.366 | 37.248 |
| RapidOCR Latin v5 | 4 | 2 / 1 / 1 | 4/7 | 0.6154 | 0.1264 | 6.808 | 8.150 | 17.183 |
| Vintern partial_42 | 4 | 2 / 1 / 1 | 5/7 | 0.7692 | 0.1149 | 12.796 | 32.492 | 58.716 |

All three C2 alarms are supported-field reading errors needing independent confirmation. All C1 refusals pass this limited contract. Inconclusive C3/C4 cases have wrong original readings; do not recast them as new regressions. Total:5 PASS,3 candidate,4 inconclusive; valid mutation pairs4/4; no independently verified failures/defects; alarm precision/recall/FAR NA. All12 responses parse as usable JSON. These tiny fixture observations do not rank model quality or prove H1–H3.

Originating12 calls completed with zero failed/ambiguous calls. Invocation wrapper budget31.351s; cold loading63.007s; cold-inclusive94.359s; fresh workers113.146s. The first orchestration attempt failed package-path preflight for all readers with **zero** image-reader calls; its logs/costs are retained separately. Resume and replay each use all12 cached outputs with **zero new calls and zero model loads**; replay appends no inference events. Scoring-only revisions are retained as separate files, never overwrite prior scores or count as new model execution.

Artifacts: [final evaluation](execution/task4_runner/smoke_02/evaluation_final.json), [verification](execution/task4_runner/final_checks.json), [tests](execution/task4_runner/pytest_run_06.execution.json), [results and limitations](TASK4_RESULTS_VI.md).
