# TASK 4 — Contract oracle validity

Research prototype, 06/11/2026. Scope: `METHOD_SPEC.md`, TASK3 C1–C4, fixture/development only. Research Questions, production API, mentor UI, legacy checkpoints and prior results are unchanged. This task does not establish H1–H3 or paper acceptance.

## Execution boundary

`reader_adapters.py` calls **only** `research.labels_study.predictor(reader_id)` and the returned pixel-only closure. It does not call study setup/run/fresh-panel functions. The closure receives an RGB image; no document ID, target key, reference, source polygon, mask intent or expected value is passed. Business prompt and global predicted-label/MRZ parsing remain the frozen baseline. Scoring joins GT afterward in `oracle.py`/`evaluator.py`.

Three readers are registered:

| Reader | Frozen extraction pipeline |
|---|---|
| `rapid_v4` | RapidOCR ONNX runtime 1.4.4, PP-OCRv4 detector/recognizer and existing classifier; predicted `rect2` view; strict V3 MRZ fallback |
| `rapid_latin_v5` | Same detector/classifier and view; **Latin PP-OCRv5 recognizer**, not a full v5 detector pipeline; same frozen extraction/MRZ fallback |
| `partial_42` | Vintern-1B-v3_5 revision `b98f263eab246eb5269ade64edbdca8a887dc44d`, existing partial_42 step_0320 LoRA; `rect2`, two tiles, seed42, greedy generation, max384 tokens, host threads2 |

Pinned baseline manifest SHA256: `d8d0cf34bf556d2d2ac36f5f0506560afc23d491f85970c1d9cd8a348998b871`. Adapter SHA256: `98835d5922f968ce29681e2ec9a2b85f26e87d7ea9538fbfb701cc37cc8a6b27`. All three readers use identical original input pixels. Internal baseline preprocessing is retained; the oracle never supplies an ideal GT crop.

Read-only preflight verifies the manifest, reused code, existing ONNX assets, extracted RapidOCR wheel members, package versions, adapter and base-model assets. Missing/different assets cause a stop; nothing is downloaded, installed or repaired. Only the old optional RapidOCR extraction hook is replaced in memory by a read-only verifier of the **same package bytes**. Existing venv plus its existing CUDA overlay are reused. HF/Torch runtime destinations point into new ignored local storage. No model weights are saved.

## Verdicts and proof obligations

| Verdict | Meaning |
|---|---|
| `PASS` | This specific conditional relation holds under the declared source graph/policy. Not a whole-document success or proof of human readability. |
| `CANDIDATE_VIOLATION` | A declared-source or conditional reading alarm needs independent verification. Never counted as a verified model failure. |
| `CONFIRMED_VIOLATION` | An issued alarm is supported by a bound independent evidence certificate or independent failure adjudication. Behavior failure alone is not a software defect. |
| `INVALID_TEST` | Known precondition, graph/mutation, image/output binding or independent validity failure. Kept in denominators/attempt records. |
| `INCONCLUSIVE` | Source coverage, readability, precision, parser output, policy, baseline correctness or other necessary evidence is insufficient. |

`mutation_validity` preserves the model-independent TASK3 validator status. `test_validity` additionally covers output bindings and independent validity adjudication. A model-dependent output-binding error cannot make the shared mutation become invalid for every reader. Invalid and unknown attempts are retained.

### C1: Complete Evidence Removal

All required sources must be removed in a verified complete source universe. A nonempty assertion is a declared-source alarm, including a guessed value equal to the full reference. Correctness against a full reference does not prove visible support. Wrong reference value and unsupported declared output are separate categories and may coexist.

An unknown/limited universe never proves absence. If all declared target sources are removed and **the only uncertain precondition is exhaustive coverage**, a nonempty output can produce `CANDIDATE_VIOLATION`; otherwise it remains inconclusive/invalid. No parser omission is promoted to hallucination. Confirmation through a certificate requires independent mutation/semantics/reference verification, inspection of the declared sources, complete-universe and absence attestations. The marker `VERIFIED_ABSENCE_OF_EVIDENCE` is added only on that route.

### C2: Alternative Source Preservation

Surviving compatible body/duplicate/MRZ evidence supports the field. A correct reading is PASS even when the primary body source is hidden. MRZ must satisfy the frozen semantic, format, field/composite checksum and support conditions. Unknown backup quality or a failed checksum yields INCONCLUSIVE, not an absence claim.

A wrong supported value is `VALUE_MISMATCH_REFERENCE`; a missing supported field is `OMISSION_DECLARED_SUPPORTED_FIELD`. Human-readable omission is claimed only with accepted independent readability evidence. The frozen extraction policy requires supported fields; optional omission is available only through explicit `Policy(require_supported_fields=False)`. That switch was not used to improve smoke scores.

### C3: Neighbor Field Non-Interference

TASK3 must verify B's required source/context preservation. The original reading of B must be correct. A changed/wrong/omitted B then gives a conditional behavior alarm. If the original is already wrong, the result is INCONCLUSIVE for regression. The unchanged fields are assessed independently of C1 refusal; `{}` cannot make an entire paired case pass.

Version regression requires the original TASK3 bound four-output witness, two distinct versions, unchanged requirement provenance and verified stability. A single transformation pair is insufficient. Root-cause software-fault identity requires separate independent patch/revert reproduction or seeded-fault activation evidence.

### C4: Evidence-Preserving Geometry

TASK3 must verify source pixels/semantics are preserved and the policy must support the operator. This prototype policy includes identity and padding translation; an exact 90-degree rotation alone does not imply a supported invariance requirement. An already wrong original or unverified interpolation/crop cannot establish a new geometry failure. Correctness is assessed at supported precision; do not invent a missing date century.

## Independent evidence and trust boundary

`EvidenceCertificate` binds graph/mutation SHA, original/follow-up pixel SHA, contract/key, evidence artifact SHA and provenance. It requires independence from the SUT **and** generator. Human review requires two distinct normalized reviewer IDs. An independent construction audit may establish construction facts but cannot assert human readability. All relevant inspected source IDs must be present before certificate-based confirmation.

`GoldLabel` binds the exact decision: graph, mutation, images, both reader fingerprints, raw prediction hashes, normalized output/validity and normalizer code hashes, and policy. It distinguishes `is_failure`, `valid_test`, unknown labels, false-alarm cause, behavior cluster and optional defect identity/proof. A negative adjudication preserves `alarm_issued=True` when an alarm was emitted: the false alarm is not erased from precision statistics. Missing-source/incorrect-GT causes are reported separately.

Hashes establish **binding and integrity, not reviewer honesty or semantic completeness**. This package does not authenticate people, verify the content of arbitrary review artifacts, or issue independent certificates automatically. Human/audit artifacts must be externally inspected before confirmatory use. There are **no independent certificates or failure labels in this smoke**. Injected certificates/labels in unit tests are marked `oracle_unit_injected`, rejected for actual-model confirmation and excluded from actual-model totals.

## Raw format, schema and confidence

[`normalized_output.schema.json`](normalized_output.schema.json) records predicted semantic keys/values, exact model/config/runtime/input/code hashes, native raw output, strict JSON validity, baseline-compatible tolerant fences/numeric conversion, field-shape validity, native timings and confidence availability. Duplicate keys, invalid structures, nonfinite constants and floating overflow are rejected for contracts. A malformed response remains a **cacheable actual inference result**, not a successful empty refusal or an excuse to call the model again.

`missing_fields` is null before a reference join; `evaluator.missing_fields` lists only declared supported keys afterward. This is stored in the scoring artifact, never in the predictor input or raw-cache key. Unknown/unannotated keys remain unjudged. Rapid confidence is preserved at its native OCR-token scope; global/field confidence is null. Vintern provides no native confidence here; JSON parse status is never converted to a probability.

The schema is parsed and required-field alignment is unit-tested. Full JSON Schema Draft 2020-12 validation was not run: `jsonschema` is absent and no package was installed. Runtime dataclass/native validators and binding checks are exercised separately.

## Cache, interruption and replay

- Cache identity: input file SHA + decoded RGB pixel SHA + reader fingerprint (model, config, inference-code closure, runtime and origin). Byte-identical pixels with a different file encoding are conservatively separate cache entries.
- Atomic, no-overwrite raw creation, payload SHA verification and persistent OS locks prevent accidental corruption/duplicate same-key inference. A cache must have its originating `inference_begin` event.
- Hash-chained, fsynced JSONL events append actual invocation begin/completed/failed records. Cache hits and model loads have separate event types. Event hashes are anchored in public run summaries; this is not a tamper-proof external logging service.
- An incomplete/failed call with no cache blocks automatic inference retry. Explicit API `retry_failed=True` is required after audit; the CLI never retries it automatically. A raw record committed before completion logging can be recovered without a new forward call. Corrupt cache/log data is preserved and stops resume.
- Replay loads only stored specs/raw records and input pixels; no predictor loader is supplied. Scoring/normalization changes can be replayed without invalidating raw inference. Bootstrap/rescoring is never counted as inference.
- Raw text, native boxes, fixture images and runtime cache live under ignored `local/`. Public summaries contain counts/hashes/statuses and semantic keys, with no user identity values or biometric embedding. Only fictional/public-specimen fixture/development inputs are admitted; test roles and unknown/personal policies are blocked.

## Verification and limits

See [TASK4_RESULTS_VI](TASK4_RESULTS_VI.md), [latest evaluation](execution/task4_runner/smoke_02/evaluation_final.json), [execution verification](execution/task4_runner/pytest_run_06.execution.json) and [final integrity audit](execution/task4_runner/preservation_final.json).

The smoke has one fictional physical ID, no human readability labels, no independent defect pool, no historical version quad and no confirmatory data. Synthetic fault injections establish expected oracle behavior only; they do not demonstrate alarm precision/recall on real defects. No further model run or threshold/prompt optimization was performed after examining the smoke. TASK2 deliverables were not found during TASK3; confirmatory prerequisites/annotation locking remain a separate gate.
