# B manuscript outline — 17 November 2026

**Internal outline, not a submission-ready paper. No new B PDF was produced.**
The frozen A/Emerging manuscript is unchanged. Tags below constrain what can be
written: [SUPPORTED] implementation/artifact facts; [DEVELOPMENT] limited empirical
or constructed findings; [PROPOSED] future method; [BLOCKED] missing evidence.
Use the [claim ledger](B_CLAIM_TO_EVIDENCE_20261117.json) before upgrading wording.

Working title: *Oracle Reliability and Abstention in Evidence-Contract Testing
for AI Document Pipelines*. More cautious alternative: *Reference Failures and
Abstention: A Development Study of Test Oracles for AI Document Pipelines*.

## Motivation

[DEVELOPMENT] A low false-alarm count can coexist with missed field faults and
unresolved alarms. The project's historical pilot and authored controls motivate
joint accounting of risk, coverage and all-fault sensitivity (B02/B05), not a
general claim that one oracle architecture is better.

## Problem definition and evidence-contract context

[SUPPORTED] Define field correctness, metamorphic-relation correctness and output
structure as separate endpoints. Define FAULT, NO_FAULT, UNKNOWN, INVALID_TEST and
STRUCTURAL_ERROR. An oracle alarm is distinct from a verified software defect or
root cause. Explain the C1–C4 context without changing frozen historical semantics.

## Threat model for unreliable test oracles

[DEVELOPMENT] Include wrong value/key, incomplete source inventory, invalid
mutation, unsupported precision, corrupted literal MRZ and correlated bad sources.
The correlated poisoning control was added after inspecting run 01, so its finding
is development evidence with a disclosed amendment (B03), not prospective discovery.

## Reference validity and abstention policy

[SUPPORTED] Describe versioned binding, typed canonicalization, conservative TD3
subset and source transitions. Two declared evidence tiers are heuristic policies,
not calibrated probabilities. [DEVELOPMENT] Two agreeing sources can share a
wrong reference; a signed approval authenticates an assertion, not semantic truth.

## Research questions

[PROPOSED] RQ-B1: reference defects and false oracle decisions. RQ-B2: detection
lost through abstention versus risk/coverage. RQ-B3: residual effect when flat
receives the same evidence and validation. Do not write these as answered for a
population by the current controls or three-ID pilot.

## Study design and equal-information baselines

[DEVELOPMENT] Describe the 58 symbolic controls, zero physical IDs and two policy
tiers separately from 46 cached comparisons (42 primary/three IDs, four diagnostic).
The checked and flat implementations share guards and match in the tested domain
(B04). [PROPOSED] Add the narrowly specified asserted-MRZ arm only after its code,
parity checks and study design are frozen. Historical B3 is secondary context.

## Data, corpus and exposure

[SUPPORTED] Metadata audit: 22,861 existing JSON files, 192/1,000 instances with
recorded exposure and 808 exposure-unknown; all ten template types used before,
all template metadata now accessed. [BLOCKED] Pixel/near-duplicate and cross-version
lineage are incomplete; no final cohort is chosen. C2 has 1,100 potential pairs
but zero validated eligible before/after pairs (B08/B09).

## Human reference process

[SUPPORTED] Exact-byte intake and separate role correction preserve existing
exports. Author has both phases; R02 phase 1 is 86/86, R02 phase 2 and R03 pending.
Round 1 remains OPEN. [DEVELOPMENT] Author/R02 phase-1 agreement predates this
continuation; no real phase-2 multi-reviewer agreement or adjudication is added.
[PROPOSED] Seal independent judgments before adjudication; preserve uncertainty,
raw answers and evidence basis. [BLOCKED] No approved production reference exists.

## Metrics

[SUPPORTED] Report labeled/all coverage, selective risk, alarm and decided
confusions, all-fault sensitivity, FAR, UNKNOWN, invalidity, structure and unresolved
truth. Zero denominator is NA. An abstained nonfault is a nonalarm, not a correct
decision. The new supplement only reaccounts 823 old cells into 492 group views.

## Development findings

[DEVELOPMENT] On 25 truth-labeled pointwise controls, risk changes from 2/25 to
1/7 as coverage changes from 25/25 to 7/25; 14 of 19 faults are abstained at tier 2.
Correlated bad references still cause FP. Flat/B parity is conditional on shared
information/guards. Actual-pilot B has no approved reference, zero field/relation
decisions and risk NA. Keep the author's original and literal-withholding panels
separate; neither is independently adjudicated gold. Do not extrapolate prevalence.

## Prospective evaluation plan

[PROPOSED] Reference-quality interventions on fixed output pairs, independent truth,
physical-ID clustering, equal budgets, prespecified primary contrast and coverage/
sensitivity requirements. The 384 sizing scenarios are design-effect sensitivity,
not achieved power. [BLOCKED] No prospective Results section can be written yet.

## Threats to validity

[DEVELOPMENT] Author-designed controls, post-hoc amendment, one-author phase-2
labels, incomplete truth, three primary IDs, known template exposure and unknown
pretraining overlap limit internal/construct/external validity. Shared validators
limit implementation independence. Informative missingness and rare faults can
invalidate naive precision; agreement alone does not validate annotations.

## Artifact and reproducibility

[SUPPORTED] Versioned scripts, 411 tests plus six subtests, exact command/log
receipts, independent aggregate arithmetic and protected-file hashes are available.
Private raw submissions, images and organizer joins stay local. The public GitHub
development repository identifies the project and is not an anonymous supplement.
[BLOCKED] Rights-cleared anonymous archival release and final author review remain.

## Limitations

[BLOCKED] No natural-model superiority, population error rate, useful coverage
guarantee, measured triage cost, independent gold or B confirmatory result is
established. Mechanical workflow improvements are not evidence of better OCR.

## Related work to develop

[SUPPORTED] [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html) studies
learned prediction/rejection; this project currently has fixed evidence tiers and
does not implement or train that model. [Klie et al.](https://aclanthology.org/2024.cl-3.1/)
analyze annotation quality management and errors in agreement/error-rate reporting;
use this to motivate careful process reporting, not a universal rater minimum.
[Oortwijn et al.](https://aclanthology.org/2021.humeval-1.15/) propose a systematic
disagreement-resolution procedure; distinguish such a process from automatic
majority labels. [PROPOSED] Expand the oracle/metamorphic-testing novelty comparison
against primary literature before making a novelty claim.

## EASE relevance

[PROPOSED] Frame the contribution as empirical assessment of test-oracle assumptions
and evidence quality for AI software, with actionable failure boundaries. Topic
fit does not demonstrate novelty or adequacy. The [readiness matrix](B_EASE_READINESS_20261117.md)
keeps Research and Emerging planning separate; no acceptance or submission claim.
