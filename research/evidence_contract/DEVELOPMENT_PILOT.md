# TASK 5 — Development pilot results

Exploratory development study, not confirmatory evidence. Protocol and code were locked before new reader outputs: [BASELINE_PROTOCOL](BASELINE_PROTOCOL.md), [ABLATION_PLAN](ABLATION_PLAN.md), [pilot_lock.json](execution/task5_pilot/pilot_01/pilot_lock.json). Models/checkpoints/prompt/rect2/max384 configuration are unchanged from TASK4. No production or locked-test input was used.

## Scope, test generation and actual execution

Primary:3 existing authored physical IDs (backup/MRZ, multiline, development renderer specification0); seeds42 and31415. Shared diagnostics add context loss, limited source coverage, bad MRZ checksum and incomplete erasure. Total5 physical IDs; the limited annotation variant shares the backup's physical ID. No real customer identity or biometric data was added.

| Quantity | Actual result |
|---|---:|
| Candidate proposals, common to A/B1 | 63 |
| Common-gate admissible candidates | 63/63 |
| Auxiliary C3 validations for mask bundles | 27 |
| Selected paired contracts per arm | 20 A;20 B1 |
| Shared diagnostic pairs | 4:2 INVALID_TEST,2 INCONCLUSIVE |
| Selected records | 44:40 VALID,2 invalid,2 unknown |
| Unique input pixels / physical IDs | 31 /5 |
| Backends | RapidOCR v4, Latin-v5-rec/shared-v4-det, Vintern partial_42 |
| Actual new image-reader calls | **84:28/backend**, completed84, failed0 |
| Read-only TASK4 cache results used | **9:3/backend** |
| Distinct image-reader outputs available | **93**, not93 new calls |
| New model loads | 3 |
| Resume / replay / rescoring new calls | **0 /0 /0** |

Each arm has10 unique image requests per seed/backend,60 charged logical requests total and60 scheduled contract-key evaluations across3 backends. Shared C1/C3 rasters are charged symmetrically. Across seeds the conditioned arm repeats one follow-up: A has16 unique primary rasters/48 reader views; B1 has17/51. These deduplicated counts are disclosed rather than treating repetitions as new documents. Equal per-block logical quota is not a claim of equal new physical calls across separately cached arms. No additional cases were added after seeing this difference.

All candidates, strata, domain hashes, invalid/unknown selected reasons, selection times and quotas are in [preparation.json](execution/task5_pilot/pilot_01/preparation.json). Random has the same valid targets/source subsets/annotations/area bins and final checker; no arbitrary-background random baseline was substituted. All63 proposals happen to be valid in this small authored primary pool, so this panel cannot demonstrate better proposal-validity yield from conditioning.

## Matched-output baseline results

Each table cell counts60 scheduled contract-key packs, including correlated seed repetitions. These are **alarms needing verification**, not independently confirmed errors or bugs.

| Checker on selected arm | A-selected alarms | B1-selected alarms | Interpretation |
|---|---:|---:|---|
| A full contracts | **8** | **9** | Conditional candidate failures |
| B0 full-reference per-field | 44 | 47 | Result errors, including expected loss of masked text; not a fault-discovery success count |
| B2 source-agnostic MR | 4 | 5 | Can miss supported omissions when it expects masked targets absent |
| B3 flat visible-reference | 27 | 31 | Strong pointwise checks, including original-already-wrong readings |
| Frozen V3 scorer | 27 | 31 | Same counts as B3 on this panel |
| Frozen V3 + common gate | 27 | 31 | Primary mutations are already valid |
| A-flat representation control | **8** | **9** | Same verdict as A on60/60 packs of each arm |
| A without alternative handling | 3 | 3 | Lower alarms mainly miss supported omissions, not proof of improvement |
| A without observed validator | 8 | 9 | Same primary verdicts because all chosen primary mutations are valid |
| A without non-interference | 8 | 8 | C3 explicitly disabled/unknown |

Full A on conditioned cases:32 PASS,8 CANDIDATE_VIOLATION,20 INCONCLUSIVE. On random cases:29 PASS,9 CANDIDATE_VIOLATION,22 INCONCLUSIVE. All20/22 primary inconclusives are original-already-wrong/unverified exclusions. Decision coverage is40/60 (66.67%) and38/60 (63.33%), compared with60/60 for the pointwise B3. Fewer alarms cannot be called a lower false-alarm rate while ignoring that loss of coverage and different goals.

| A contract | A-selected PASS / candidate / unknown | B1-selected PASS / candidate / unknown |
|---|---|---|
| C1 | 17 /1 /0 | 16 /2 /0 |
| C2 | 0 /6 /0 | 0 /6 /0 |
| C3 | 8 /0 /10 | 7 /1 /10 |
| C4 | 7 /1 /10 | 6 /0 /12 |

No A alarm is exclusive over B0 or strong B3 on either arm. A has5/6 alarms absent from B2, mainly because nominal source-blind refusal misses supported-field reading problems. This only exceeds a weaker relation checker. There is no new C3 alarm on the A-selected cases; the one on random cases is also caught by B3. No version quad, patch/revert or historical software-fault provenance is present.

Taxonomy is multi-label: conditioned A has5 supported-field omissions,1 unsupported-declared-source assertion and3 reference mismatches (one alarm has two labels). Random A has7 omissions,2 unsupported assertions and2 mismatches. Category sums are not unique failure counts.

## Validity diagnostics, shared by all methods

| Diagnostic,3 reader evaluations each | A | Frozen V3 raw | V3 + common gate | A without observed validator |
|---|---|---|---|---|
| Shared semantic context destroyed | 3 INVALID_TEST | 3 alarms | 3 INVALID_TEST | 3 INCONCLUSIVE |
| Target removal incomplete | 3 INVALID_TEST | 3 alarms | 3 INVALID_TEST | **3 PASS despite invalid mutation** |
| MRZ checksum invalid | 3 INCONCLUSIVE | 3 alarms | 3 INCONCLUSIVE | 3 INCONCLUSIVE |
| Source universe incomplete | 3 INCONCLUSIVE | 3 PASS | 3 INCONCLUSIVE | 3 INCONCLUSIVE |

The common gate suppresses6 legacy alarms on known-invalid contract attempts and3 on uncertain-backup attempts. This is an **admissibility difference**, not9 independently proven false alarms. In particular V3 is a result scorer and may report a genuine field-reading error on an input that is invalid for the intended C1/C3 relation. Even simple V3+gate reproduces A's diagnostic verdicts here. No-validator can incorrectly accept an invalid removal even without raising an alarm; count that as invalid test acceptance, not successful refusal evidence.

Independent natural-image readability/failure gold and validated root-cause defects are absent. Confirmed real-model violations=0, verified software defects=0; false alarms, alarm precision/recall/FAR=**NA** for every method. Injected control outputs in unit tests demonstrate expected mechanisms only and do not appear in this model ledger.

## Conventional field evaluation

Partial annotated field universe; outside keys remain unjudged. Scores below deduplicate image/key/reader observations and include original plus follow-up images. Full references include inaccessible masked values; visible references use verified declared support. Neither is a count of independent documents or a cross-arm model ranking.

| Arm / reference | Exact match | Micro F1 | CER |
|---|---|---|---|
| A / full | 58/132=43.94% | 116/224=0.5179 | 817/1953=0.4183 |
| A / visible | 58/114=50.88% | 116/206=0.5631 | 555/1689=0.3286 |
| B1 / full | 70/147=47.62% | 140/250=0.5600 | 917/2169=0.4228 |
| B1 / visible | 70/129=54.26% | 140/232=0.6034 | 661/1911=0.3459 |

Each arm has18 known-removed field observations. Reference-set and selected-input differences explain why F1/EM numbers cannot establish generation superiority. All full-reader/per-contract/source/pair counts and normalized hashes are retained in [evaluation_01.json](execution/task5_pilot/pilot_01/evaluation_01.json) and [per-pack checks](execution/task5_pilot/pilot_01/evaluation_01.checks.json).

## Measured cost and CPU/GPU use

CPU/RSS monitoring starts after harness imports and before reader preflight. Parent-measured worker wall time also includes interpreter startup; the two observation intervals differ slightly.

| Backend | New calls / reused | Process CPU s | Fresh worker wall s | Sampled peak RSS GiB | Native peak CUDA allocated / reserved GiB |
|---|---|---:|---:|---:|---|
| RapidOCR v4 | 28 /3 | 96.219 | 55.982 | 0.932 | NA /NA |
| RapidOCR Latin v5 | 28 /3 | 71.234 | 42.506 | 0.935 | NA /NA |
| Vintern partial_42 | 28 /3 | 159.531 | 155.930 | 5.722 | 1.945 /2.047 |

CPU process-time includes multiple threads and can exceed wall time: average CPU percent of one core was176.96%,173.80%,103.86% respectively. RSS is sampled process resident memory, not all host RAM. Vintern's71 device-wide nvidia-smi samples observed peak100% GPU utilization and3371MiB device memory; other applications are included. Native CUDA figures apply to new calls in this worker, not historical cached outputs. Unavailable CPU-reader GPU measurements remain null. Private resource traces are retained; public summaries contain no OCR strings or embeddings.

Shared preparation wall16.990s; A selection total1.032s, B1 selection0.841s (includes deriving C3 pairs). Initial oracle/baseline scoring wall9.839s, CPU8.391s; includes cold legacy imports, not a pure microbenchmark. Fresh worker wall total254.418s includes startup/preflight/load/inference/cache overhead; native logical-request latency charged to A148.321s and B1143.688s for the same60-request quota. This descriptive difference reflects selected inputs and reused historical latencies, not statistically established speed. Shared pool/annotation costs are not free; person-minutes for existing authored annotations are unknown, so annotation-cost efficiency cannot be claimed.

## Verification, reproducibility and preservation

19 new baseline/selector/cache mechanism tests passed; the targeted combined suite passed **165 tests +6 subtests**,0 failed/error/skipped. JUnit171 includes the6 subtests. Logs: [first baseline tests](execution/task5_pilot/baseline_tests_01.log), [combined execution/code hashes](execution/task5_pilot/regression_tests_02.execution.json), [combined stdout](execution/task5_pilot/regression_tests_02.log). No failed test was hidden or rerun until a desired result; all completed model outputs were reused.

Resume and replay each return93 outputs with0 new inference/0 new model loads. Historical TASK4 event logs are unchanged. [Replayed evaluation](execution/task5_pilot/pilot_01/evaluation_replayed.json) has the same semantic-payload hash and identical per-pack checks as the initial evaluation; timing/event-history metadata may differ after cache-hit logging. Rescoring calls=0. Evidence: [final checks](execution/task5_pilot/final_checks.json), [byte preservation](execution/task5_pilot/preservation_final.json).

All2.574 preexisting nonignored files (180.304.995 bytes), HEAD/refs and tracked/staged diffs are checked unchanged. Ignored weights are pinned by read-only reader preflight; this does not assert every ignored dataset/cache was recursively hashed. No checkpoint, split, prior result, API/UI or Git history was modified. Public artifacts expose hashes/counts/statuses/semantic keys only; new raw inputs/outputs are private ignored fictional-data artifacts.
