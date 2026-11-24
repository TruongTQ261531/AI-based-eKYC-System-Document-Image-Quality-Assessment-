# Research B — Claim-to-evidence audit G01/G02/G03 · 24/11/2026

Baseline evidence: 5b70e502d699b0deb129fc8829294de65445e446. New public verification: 7f11f1c17c33d2b6b4e912a271f4773a058efb46. Fixture analysis: 253fe5ae7ad21d00c4998ab0a3a33d92023e8a91. This dated ledger supplements, not replaces, historical A/B ledgers.

## Claim ledger for Research Papers

| ID | Claim allowed now | Evidence and denominator | Status / prohibited interpretation |
|---|---|---|---|
| G01-01 | Historical A and A_flat matched on the primary scheduled panel | [A/B3 diagnosis](A_VS_B3_DIAGNOSIS.md), 120 scheduled comparisons, 108 deduplicated primary comparisons, three main physical IDs | HISTORICAL_DESCRIPTIVE; graph architecture superiority not established |
| G01-02 | A emitted fewer alarms than B3 in the historical scheduled panel | Same audit, 17 vs 58 alarms / 120, 41 B3-only alarms | HISTORICAL_DESCRIPTIVE; cannot call 41 false alarms without independent truth |
| G01-03 | D4 changes pointwise decisions by withdrawal under the frozen shared inputs/tier | [Mechanism](D4_MECHANISM_BOUNDS_VI.md); [public recount](cloud_g01_g03/public_recount_receipt.json), 72 authored controls, 8 differing controls per tier: 6 FAULT and 2 NO_FAULT to UNKNOWN | SUPPORTED_CONSTRUCTED_ONLY; no estimated natural prevalence, no direct correction of FAULT to NO_FAULT |
| G01-04 | A decrease in FAR via withdrawal can cost sensitivity and coverage | [Mechanism bounds](D4_MECHANISM_BOUNDS_VI.md); for known nonfaults N, delta FAR=withdrawn false alarms/N; lost true detections reduce sensitivity | CONDITIONAL_MECHANISM; not an observed gain on real C2 |
| G01-05 | Both arms abstained on historical semantic replay | 46 cached cases, 42 primary/3 IDs; zero approved reference; all pointwise/relation UNKNOWN | HISTORICAL_DESCRIPTIVE; risk NA, no accuracy or additional inference |
| G01-06 | Round 1 intake and descriptive agreement exist | [Closure](ROUND1_CLOSURE_20261122_VI.md); R02/R03 primary pointwise 32/42, kappa .66955; relation 34/42, kappa .71282; recounted | UNADJUDICATED; 68/86 prior exposure self-reported by R03, independence unverified; signed closure and reference pending |
| G01-07 | Cross-collection pixel reuse is recorded | [P6 matrix](P6_CLAIM_TO_EVIDENCE_MATRIX.md): 24 groups, 12 later adapters, 44 local and 8 imported evaluation tables examined; 0 confirmed same-checkpoint overlap in audited scope | REPORTED_PROVENANCE; external pretraining unknown; not proof all models/tests free of leakage |
| G01-08 | Current superiority design fails calibration requirements | [P5B](P5B_STATISTICAL_CALIBRATION_VI.md): 23 scenarios x (800+1600)=55,200 synthetic cohorts; 3 methods; held-out v3 joint power 1553/1600, null sensitivity joint false pass 147/1600, sensitivity coverage 1381/1599; all methods INFEASIBLE in both phases | RECOUNTED_SIMULATION_SUMMARIES; no real cohort inference, no universal impossibility proof |
| G01-09 | Rights-based C2-37 technical scope exists | [Protocol](C2_37_ANALYSIS_PROTOCOL_VI.md); 37 candidates/18 IDs, 45 distinct full frames, 155 images/workspace, 74 blank forms; hold 8/6 Greek; public receipt count checks | TECHNICAL_ONLY; D10 pending, no new human proposal/approved reference |
| G01-10 | Historical cache does not furnish an exact same-reader pair in examined stores | [Cache audit](C2_37_OCR_CACHE_PREFLIGHT_VI.md), 0/37, 13/45 images with at least one bound result, 172 cache records not independent samples | LOCAL_REPORTED_DIAGNOSTIC; public report inspected, bytes not independently checked here; no empirical paired effect |
| G01-11 | Current machine has frozen-reader files according to preflight | [Runtime](C2_37_RUNTIME_READINESS_VI.md); CUDA execution fingerprint not verified, no inference | LOCAL_REPORTED_DIAGNOSTIC; cannot infer runnable or authorized |
| G01-12 | Descriptive analysis logic is testable without private data | [G03 fixture receipt](cloud_g01_g03/fixture_receipt.json): 43 tests, no failures, 4096 missing truth assignments enumerated | SYNTHETIC_SOFTWARE_ONLY; no real rights, labels, approved reference, performance or empirical sample |
| G01-13 | Claim of lower real FAR with sufficient coverage/sensitivity | 0 real C2 pairs, 0 eligible approved reference; P5B infeasible | BLOCKED; no superiority, significance, or population risk |
| G01-14 | Novelty beyond oracle applicability, equal-information guards, selective prediction and prior work | [B evidence v3](paper/B_EVIDENCE_V3_20261121.md); existing literature comparison targeted | NOT_ESTABLISHED; G04 must verify nearest prior art; no first-ever claim |
| G01-15 | Research Paper submission readiness | [Backlog](EASE2027_CHATGPT_CLOUD_BACKLOG_20261124_VI.md) | NOT_READY; G04/G05, valid real evidence and release/anonymous artifact review remain |

## What was executed (G02/G03)

G02: 269 independent arithmetic/invariant checks on 13 pinned public JSON artifacts, 0 failures. Recounted D4 states and expected vectors from public controls, IFV contingency agreement/kappa, P5 independent-replication Wilson summaries, P5B probabilities/count constraints and verdicts, P6 and C2 aggregate consistency. The code function ran in ChatGPT JavaScript tool runtime; Node CLI wrapper not yet independently run on a repository checkout. No original Monte Carlo draws, private membership, model execution or human labels were reproduced. [Code and receipt](cloud_g01_g03/public_recount.cjs).

G03: fixture-only module and test suite, 43 executed checks, 0 failures. Exact synthetic scope and counts, single reader/checkpoint/config/runtime/profile, common before/after and reference binding, incomplete-frame suppression, missing-truth bounds, descriptive strata. The initial fixture count error was corrected before passing checks. All synthetic metrics/rights flags are fictional and must not enter paper empirical results. [Module and limitations](cloud_g01_g03/README.md). Production adapter, authentication, signed authority, byte-level verification and real-input integration are explicitly deferred.

## Priorities / gates

- Next G04 novelty and G05 manuscript skeleton, then G06 independent CLI/CI replay and G07 gated local adapter. No additional Codex task required for those preparatory steps.
- Keep D10 REVIEW_ACCESS_PENDING, RETENTION_PENDING, RELEASE_PENDING, GO_PREPARATORY_ONLY, NO_GO_SUPERIORITY, P5B INFEASIBLE, TASK 6B/7B BLOCKED. No provider contact, Greek reopening, model training, real inference, new approvals or private artifacts.
- Management estimate remains approximately 51% under original weighting; public verification and fixture implementation reduce engineering uncertainty, not missing scientific evidence.
