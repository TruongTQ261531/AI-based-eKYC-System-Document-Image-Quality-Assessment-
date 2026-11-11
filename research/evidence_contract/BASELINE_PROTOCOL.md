# TASK 5 — Prospective development baseline protocol

Version1, frozen before TASK5 reader outputs. RQs/H1'–H3' in RESEARCH_QUESTIONS.md and METHOD_SPEC.md remain unchanged. All TASK0–4 components, checkpoints, datasets, test splits and published results are read-only. New code is in `task5/`, logs in `execution/task5_pilot/`, private images/raw/cache in ignored `local/task5_*`. No production choice, training or confirmatory test is authorized here.

## Comparisons and information access

| ID | Implementation | Role / limits |
|---|---|---|
| A | Existing TASK3–4 source contracts/validator/oracle | Conditional candidate failures, not independently confirmed faults without gold |
| B0 | Conventional full-reference exact match/F1/CER and missing/wrong-key checks; per-key canonical reading check with the same common validity gate | Result evaluation. A field lost through masking can be an expected loss of answerability; do not call each B0 error a fault or hallucination |
| B1 | Uniform validity-filtered box-aware random selection from the **same** finite source-region candidate pool as A, same annotation, area bin, operators, common gate and final A checker | Primary strong generator comparator. Not random noise over arbitrary background pixels. It is allowed all valid targets/retained pairs in its matched stratum and all body-containing proper source subsets for C2 |
| B2 | Graph-blind nominal metamorphic relations: masked target absent; retained field invariant; declared padding translation invariant | Receives nominal contract/key/operator, outputs and a common external validity result, not explicit graph/GT values. Does not pretend every field of a deliberately masked image is invariant. Its common gate is source-aware upstream: this is a controlled oracle comparison, not a wholly annotation-free system |
| B3 | Flat visible-reference + known source availability/precision, same common gate and canonical matching | Strong per-field result checker; intentionally able to find all pointwise output errors A can find. Does not require the original to be correct before reporting an ordinary reading error |
| B3-V3 | Actual frozen `v3_sources.visible_realizations` + `v3_metrics.score`, with an explicit new input-schema adapter; raw and common-gated variants | Existing OR-source/value-region visibility and precision scorer. Geometry is not independent human readability. No claim of rerunning its historical dataset experiment |
| A-flat | Flatten verified availability/typed references at the oracle boundary; preserve A's original-correctness and operator gates | Strong representation control. Source facts still require upstream annotation/validation; equivalent results would undermine any claim that explicit graph representation alone adds detection capability |

No model gets answers, target key, graph, mask, polygon or expected state as inference input. All oracle baselines reuse exactly the same raw execution pack; the original reader/config/prompt/max tokens/preprocessing remain frozen. B0/B3 field metrics and conditional fault-discovery alarms are reported separately. A mismatch of their goals is not proof of superiority.

## Panel and generation, chosen without new model outputs

Primary panel: existing `backup_fixture`, `multiline_fixture`, `existing_renderer_development(0)`:3 physical IDs. All are fictional fixture/development; no natural customer data. Shared diagnostic cases add `shared_context_fixture`, bad-checksum backup, limited-source annotation of the same backup ID, and incomplete-target erasure. The latter is an intentionally invalid test, not an injected model defect. Total physical IDs at most5; annotation variants/seed repetitions are not independent documents.

Selection seeds42 and31415. Enumerate each supported annotated field and its permitted retained neighbor; mask padding1/2/4; C2 every body-containing proper subset with a backup; translation offsets(5,7),(12,16),(20,11). Every proposal runs the common TASK3 validator before selection; a C1/C3 bundle is eligible only when both relations are valid. Retain metadata/hash/reason for all rejected/unknown proposals; retain images for selected primary and all diagnostic attempts. No free rejection/refill loop; the entire bounded candidate pool and cost are charged to both selectors.

Area strata use fixed masked-area fractions with edges1%,4%,12%,35%,101%; reported area is union raster area, not sum of overlapping boxes. Choose a nonempty bin by seed index, common to A/B1 in each document/family block. A prioritizes new source-type signatures and semantic-key coverage; deterministic seed hash breaks ties. B1 samples uniformly from that identical eligible bin. Rankers never use predictions, exact GT strings, OCR loss or confirmatory outputs. Area distributions, domain hashes, pool sizes and chosen candidates are published; within-bin area differences remain a validity threat, not claimed exact pixel-area matching.

Per arm/selection seed:3 removal+neighbor bundles (6 contract pairs),3 geometry pairs,1 backup pair =10 paired contracts;3 originals+7 follow-ups =10 unique image requests per backend in that block. Assert this quota **before inference**. Two seeds ×3 readers =60 charged logical image requests per arm. Reused originals across seed blocks still consume the same logical quota; within-block C1/C3 reuse is symmetrical. Cache hits never buy extra samples. Diagnostics are a separate shared fixed panel, not extra discovery quota for A.

Plan hard cap:120 **new actual** image-reader invocations across the union, including failed/ambiguous attempts; no automatic retry or scale-up. Record exact prepared union and read-only cache reuse before workers run. Raw TASK4 outputs may be reused only with exact reader/file/pixel/config/code bindings and replay without appending its old logs. Report originating historical calls, TASK5 new calls, cache hits and per-arm logical requests separately. Never count unit control outputs/rescoring as model inference.

## Models, runtime and cost

Use existing RapidOCR v4, Latin-v5-rec/shared-v4-det and Vintern partial_42 step0320 via unchanged TASK4 `reader_adapters`/`Runner`. Verify baseline manifest, model/package/code hashes; no repair/install/download. Existing venv/CUDA overlay only. Run backends sequentially; fixed hash order of inputs; no post-score prompt/version/preprocessing change.

Measure preparation/proposal/selection/oracle wall and CPU time, actual-call and cached-native latency, cold load and worker wall, process CPU/RSS/thread observations and native Vintern CUDA peak allocated/reserved bytes. Device utilization samples, if obtainable, include other applications and are marked device-wide; unavailable data remains null. No measured person-minutes exist for reused authored annotations: report annotation cost as unavailable, not zero. Shared annotation/pool costs are charged equally in cold-start comparisons. Cache replay is not a fresh stochastic stability experiment.

## Metrics and decision rules

Report proposal/generated/valid/invalid/unknown counts; per-contract A candidate/confirmed/invalid/inconclusive counts; baseline alarms and overlaps on the same contract-key packs; source/type taxonomy; full vs visible EM/F1/CER with explicit field/view/ID denominators; matched logical and actual inference budgets; CPU/GPU/resource observations. Use unchanged TASK4 evaluator for A where applicable. Report original-already-wrong exclusions and decision coverage beside lower alarm counts.

Independent real failure/readability gold is not available. Thus verified defects and confirmed real-model failures remain zero unless a genuinely independent bound artifact is supplied; alarm precision/recall/FAR are NA. Alarms on validator-invalid attempts are recorded as such, not silently certified as false alarms of a real bug detector. Deterministic correct/incorrect output packs in tests demonstrate mechanisms only and are excluded from the real model ledger. There is no historical version quad in this pilot; do not relabel single-version output changes as software regressions.

GO permits a bounded next verification study only. No automatic scale-up if A equals the strong per-field/flat-source controls or if extra alarms lack independent validation. No-Go for confirmatory/superiority claims when independent reference/fault provenance or statistical adequacy is missing. Analyze five requested novelty questions with actual counts and information/gate ablations; do not use significance language on this small, clustered development panel. Any proposed narrowing is prospective and does not rewrite the frozen RQs in this task.

## External implementation eligibility audit (06/11/2026)

- [VeriOCRBench official repository](https://github.com/zy001122/Beyond-Blind-Compliance): task verification/diagnosis/over-refusal with a different QA/prompt/judge interface. Its scripts use provider APIs and new task prompts; running those here would not preserve this frozen extraction task. Inspected release structure/README; not downloaded or executed; no borrowed result numbers.
- [GenMorph official repository](https://github.com/jonayerdi/genmorph): Java-method MR synthesis/evaluation and Java mutation tools, not an image-to-fields black-box implementation. Not executed or installed; conceptual MR-validity prior art remains relevant.
- [LLMorph official repository](https://github.com/steven-b-cho/llmorph): NLP text-task MR interface and model API prompting; not a drop-in fixed image-reader baseline. Current README differs from older search snippets, so no environment compatibility is inferred from the snippet. Not installed/executed.

These are scope/eligibility assessments based on primary repository documentation, not claims that the works lack other capabilities. B2 is an explicitly local generic MR adaptation, **not** a reproduction of any of these tools. The runnable frozen V3 implementation is included as B3-V3. No comparable third-party implementation has been reproduced in this pilot.
