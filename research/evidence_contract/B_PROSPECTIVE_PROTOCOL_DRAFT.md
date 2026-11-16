# Prospective B: Oracle Reliability & Abstention

16 November 2026. **DRAFT_ONLY — no scientific GO, no confirmatory lock or execution.**
This proposal follows the [development results](B_ORACLE_RELIABILITY_20261116.md).
It does not amend frozen A, the historical IFV protocol, old propagation B,
reviewer packages or the existing manuscript's results.

## Research questions and proposed contrast

| Question | Proposed evidence | Decision still needed |
|---|---|---|
| RQ-B1: Which reference defects cause false oracle decisions? | Paired reference-quality interventions on fixed output pairs, with separately established field/source truth | Accept primary contrast and eligible reference intervention set |
| RQ-B2: What fault detection is lost when the oracle abstains? | Labeled/all coverage, selective risk, all-fault sensitivity, unresolved alarms at predeclared operating points | Minimum useful coverage/sensitivity and effect or noninferiority margins |
| RQ-B3: What remains when a flat method receives the same evidence? | Identical images, inventories, literal MRZ, provenance, validity, references and annotation budget for compared methods | Confirm baseline implementations and cost scope |

Proposed primary contrast: v2 checked reference policy versus a separately named
metadata-asserted policy, applied to the same pairs and same information under
controlled reference defects. It must be implemented and frozen before the new
cohort; the four historical v1 projections are not that confirmatory experiment.
The reference intervention is the manipulation, not a change in the model output
or in the evaluation truth. Include an equally informed flat comparator using
the same validation boundary; expected parity is reported as such. Keep frozen
A/A_flat/B3 as secondary context, without giving only one method extra truth.

The RQ-B2 operating points initially proposed are the two current evidence tiers.
They are heuristic categories, not calibrated probabilities. The correlated-bad-
reference case shows that two agreeing sources can share an error. Any revised
source-independence score or learned abstainer belongs to a versioned development
amendment; thresholds cannot be tuned using confirmatory outputs. Risk and coverage
are motivated by selective prediction, but this project has not implemented or
trained [SelectiveNet](https://proceedings.mlr.press/v97/geifman19a.html).

## Truth and approval must be external to the tested decision

For every field/pair, record the complete intended value, observable/readable
evidence, semantic key, all source realizations, mutation validity and output
correctness as separate observations. Source existence does not prove readability.
Hashes bind versions; they do not validate truth. Preserve UNKNOWN on ambiguity.

Reference authors/validators must not derive truth from B's output or model
agreement. Freeze reference collection before output exposure where applicable;
record each assessor's role and prior exposure. Obtain independent judgments,
report agreement before adjudication, retain disagreements and their resolution.
The organizer must name the approving authority and its relationship to the
implementation before a reference registry can be approved. Approval binds exact
reference IDs, field, image pair, policy scope and timestamp; an amendment needs
new approval. Current production approved ID set remains empty.

Constructed reference/output controls stay `oracle_unit_injected`. A test that
changes an origin flag to exercise a trust guard is still a unit test, never
actual model inference. Checksummed MRZ is not independent authenticity evidence.
TD3 unsupported fields or precision remain UNKNOWN under the current v2 subset.

## Sampling and data readiness

MIDV-2020 is a candidate external to the project's renderer, not automatically
external to prior model development. [Provider/schema checks and evidence](execution/master_01/oracle_reliability_20261116/SOURCES_AND_FEASIBILITY.md)
are complete at metadata level: provider license identified as CC BY-SA 2.5;
all ten template types already appear in inspected history; at least 148 physical
instances were already used. No new cohort has been selected or downloaded.
Existing full metadata headers have been accessed; this exposure must be recorded.

Candidate inclusion requires an auditable lineage registry for physical instance,
document type/template family, content, capture/view, encoded SHA, decoded pixel
SHA and near-duplicate group. Merge known aliases and shared identities across
MIDV versions/modalities. Complete the exposure inventory beyond the five inspected
manifests. Unknown pretraining overlap remains unknown. Repeated frames/fields/
mutations do not add independent physical IDs. A template-generalization claim
cannot be based only on these ten already-used types.

Before selecting or opening new prediction outputs, specify sampling frame,
stratum allocation and missing-data rules. Reserve development and confirmation
by physical identity and the additional axes required by the claim; record all
overlaps. Keep image variants from one instance together. Hold out template
families only where genuinely unexposed families exist. Existing pilot images
remain development even after additional human reviews.

| Required panel | Independent checks before scoring |
|---|---|
| Known-good reference and non-fault | Source availability/readability, semantic binding and correct output verified separately |
| Faulty reference | Deliberately wrong value, wrong key, missing inventory and correlated wrong sources; preserve intervention provenance |
| Invalid / indeterminate test | Wrong mutation target, uncertain removal, corrupted metadata; retain denominators and reasons |
| C2 surviving backup | Main existed and was removed; distinct backup supported the same semantic field before/after; literal MRZ checks where within scope |
| Actual field fault | Independently verified output mismatch/omission/unsupported assertion, without inferring software root cause |
| Wrong→correct / wrong original | Separate pointwise correctness from whether a relation is assessable |
| Unusable output structure | Parser failure and unusable normalized object; separate structural endpoint, no relabeling as semantic failure |

Template field boxes and transcript annotations can seed inventory preparation;
they cannot automatically approve readability after crop/mask/photographic
distortion. New human labels must come from actual assessors, not a relabeling
of the current author's answers or a majority vote treated as truth.

## Locked analysis proposal

Comparison unit: unique `(reader, before pixel, after pixel, field, mutation,
reference version, endpoint)` with repeats explicitly grouped. Main sampling and
inference cluster: physical instance; retain template/capture dependence in the
design. Author-defined control truth is analyzed separately from natural outputs.

Report every planned method on the same frame, separately for primary and
diagnostic strata, contract and cluster. Missing or rejected references remain
UNKNOWN; INVALID_TEST is explicit. Publish counts before denominators. For each
endpoint report: alarm TP/FP/FN/TN, confusion among decisions, coverage over all
pairs and labeled pairs, all-fault sensitivity, FAR, selective risk, abstained
faults, all-alarm accounting and reasons. No decisions means risk NA. In alarm
confusion, an abstained nonfault is a nonalarm, not a validated NO_FAULT.

Define the paired estimand, meaningful effect, coverage/sensitivity floors,
uncertainty method and multiplicity family before sizing. Sizing must use
independent clusters and the expected missing-label/abstention rates. The old
three-ID pilot is inadequate for a precise variance or power estimate. Do not
pick a fixed number of IDs because many fields/views make the row count large.
Sample size, seed, model-call budget, resource budget, margins and stopping cap
are **PENDING**, not zero-cost claims or execution defaults.

Primary analysis uses the frozen, approved truth snapshot. Predeclare sensitivity
for unresolved/adjudicated labels, source scope and reference validity; do not
select the panel giving the best FAR. Report differences/intervals at cluster level
where supported; no p-value from treating fields as independent. Cost claims need
prospectively measured active human time, annotation effort, runtime and calls;
cache replay or wall time while waiting cannot substitute for human triage cost.

Stop at the locked cohort and budget, not when significance or a favorable score
appears. Keep every execution failure, timeout and protocol deviation. Freeze code,
model hashes, readers, seeds, references, sample, analysis and exclusions before
confirmatory outputs; no interim tuning. Amendments are dated, justify changes,
and distinguish prior from future exposure. Only the project owner's scientific
GO may open TASK 6B/7B after these decisions are concrete.

## Reviewer rounds run in parallel

**Round 1 remains OPEN.** Proposed membership is author + R02 + R03 on the same
historical sample. Author has both phases; R02 phase 1 is sealed and its phase 2
package exists; R03 is pending. No new submission arrived in this milestone.
R02's role correction is a separate organizer statement; raw role/answers stay
unchanged, and independence has not been independently verified.

Proposed snapshot trigger: all three have completed the phases being analyzed,
or the organizer explicitly records a dated analysis cutoff and the actual
incomplete membership. This proposal does not silently close recruitment or
declare that cutoff now. Seal raw bytes and schema/provenance per reviewer.
Any late reviewer enters Round 2 or a documented amendment, with exposure,
package version, timestamp and purpose; never overwrite Round 1.

Give each reviewer only the already-issued matching package. Keep model/system
identities, author answers, disagreement tables and development findings out of
ongoing independent review. Open phase 2 only after that person's phase 1 is sealed.
Use private organizer joins, not cross-reviewer case IDs. Compute agreement before
discussion, then document adjudication separately. Current agreement tooling covers
phase 1; phase-2 multi-reviewer aggregation must be validated when genuine inputs
exist. Do not manufacture another person's form to exercise the real intake.

## Conditions still open

| Item | State / next concrete action |
|---|---|
| P1/P2 implementation and arithmetic | DONE for development; 336 tests + 6 subtests and replay receipts |
| P3 independent reviews / adjudication | OPEN; receive R02 phase 2 and R03, then report pre-adjudication agreement |
| Provider license and schema feasibility | CHECKED at source/metadata level; pin archive release and artifact-specific attribution before new release |
| Corpus eligibility and diversity | PENDING full lineage/exposure audit and independently verified C2/source panel |
| Approved reference authority / registry | NEEDS_HUMAN; no approved production reference IDs |
| RQ/contrast, margins, sizing, seed and budgets | DRAFT_ONLY; finalize before new confirmation data |
| Scientific GO / TASK 6B/7B | NO_GO_SUPERIORITY; no lock or inference opened |
| Paper B / track choice | Claim ledger updated; no new B PDF or submission; final contribution/track decision remains open |

The official [Research CFP](https://conf.researchr.org/track/ease-2027/ease-2027-papers)
was checked on 16 November: abstract 15 January, full paper 22 January 2027 AoE,
10 content pages plus 2 reference-only pages. It welcomes negative findings;
the project's need for new evidence depends on its intended claim, not a universal
CFP requirement for confirmatory superiority. [Short/Emerging](https://conf.researchr.org/track/ease-2027/ease-2027-short-papers-and-emerging-results)
and [RENE](https://conf.researchr.org/track/ease-2027/ease-2027-reproducibility-and-negative-results)
remain possible tracks, not automatically suitable substitutes for missing evidence.
