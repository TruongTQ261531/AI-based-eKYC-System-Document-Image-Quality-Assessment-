# Prospective B protocol v2 — 17 November 2026

**DRAFT_ONLY. PENDING_OWNER_DECISION. NO_GO_SUPERIORITY.** This version refines
the [16 November draft](B_PROSPECTIVE_PROTOCOL_DRAFT.md) without changing its bytes,
historical A/A_flat/B3, reviewer instruments or frozen B policy/results. B means
Oracle Reliability & Abstention. No prospective outputs, reference approvals,
final cohort or confirmatory lock have been created.

## Questions and proposed estimand

RQ-B1 asks which reference defects cause false oracle decisions. RQ-B2 asks how
much detection and coverage are lost when the oracle abstains. RQ-B3 asks what
remains when a flat implementation has the same information and validation.

Proposed primary contrast: checked v2 versus a separately named metadata-asserted
policy on identical fixed image/output pairs and reference interventions.
Proposed primary endpoint: paired difference in false-alarm probability on all
eligible, independently labeled nonfault comparisons in a prespecified reference-
defect panel. Positive `FAR_asserted - FAR_checked` favors checked, but a useful
result must also satisfy separately chosen coverage and all-fault sensitivity
floors. Missing truth stays in the full frame and is reported; invalid tests form
a separate declared stratum, not post-hoc convenient exclusions. Final panel,
endpoint, meaningful effect and floors require decisions D4–D8.

Reference intervention truth and output correctness are established independently
and remain fixed across methods. A deliberately wrong reference is not itself a
natural model fault. Do not mix reference-defect prevalence from injected panels
with the natural prevalence in eKYC. Reference assessment must precede exposure to
the method's verdict; output correctness assessment may necessarily see the output
but must remain blinded to method identity/verdict and intervention assignment.

## Equal-information comparator specification

This is an implementable **specification**, not an executed prospective baseline.
The existing checked/flat code is tested; the asserted arm remains to implement
and freeze under its own name after D4. Historical v1 projections are diagnostic
counterexamples, not the final comparator. One narrow, auditable first contrast
would disable only literal TD3 validation; broader guards need separate ablations.

| Arm | Information | Validation guards | Abstention | Reference assumptions | Computation | Human annotation | Failure modes |
|---|---|---|---|---|---|---|---|
| Checked v2 | Same pairs, frozen outputs, inventories, literal MRZ, provenance and versioned reference | Shared binding/trust/validity/structure + typed value, literal MRZ and transition checks | UNKNOWN on unresolved support; declared tier 1 primary proposal | Human-approved provenance and semantic mapping; correlated sources remain possible | Measure normalization + shared validation + predicate separately | One shared reference/truth collection budget; record assessor active time | Confidently wrong shared reference; excessive deferral; unsupported formats |
| Asserted MRZ ablation (proposed first comparator) | Exactly the same information, including MRZ literals it chooses not to verify | Identical mandatory guards; trusts declared supported MRZ value/conditions instead of recomputing literal consistency/check digits | Same missing/conflict/transition rules and same tier | Metadata assertions may be wrong; no additional human truth | Same timed sections; omitted check work recorded | Same shared labels and budget, no privileged truth | Poisoned/invalid MRZ metadata can produce wrong decisions |
| Matched flat | Exactly checked v2 information | Same validator and guards by design | Same tiers | Same assumptions | Measure flat predicate, shared work not counted twice | Same budget | Same reference failure; parity is expected in tested domain |
| Frozen A/A_flat/B3 | Their historical interfaces | Frozen historical rules | Historical rules | Historical one-author evidence only | Context only | No retrospective claim of equal annotation cost | Not a confirmatory equal-information comparator |

The asserted implementation must reuse a separately factored common admission
boundary: image/mutation/field hashes, typed schema, designated reference approval,
output origin, validity and parser usability. The sole initial resolver change is:
for a SUPPORTED MRZ source with all declared flags true, use its typed declared
value without the literal TD3 check; preserve conflict, exhaustive absence and
C2 before/after transition rules. In this ablation, an asserted MRZ source has the
same declared tier as a checked MRZ source, so tier is not an additional treatment.
Both arms see the same full source record; neither receives evaluation truth.

Before freezing: parity on valid-reference controls, divergence only on declared
MRZ interventions, identical missingness/frame/budgets, and independent arithmetic
must pass. Do not silently copy and diverge the common gate or patch the frozen
policy in place. A larger 'all checks disabled' comparator would confound effects
and needs a separately approved specification. Graph/flat share their validator;
their agreement does not constitute independent truth validation.

## References, review and adjudication

The [signed registry workflow](oracle_reliability/REFERENCE_WORKFLOW.md) is now
implemented and tested, with **zero production authorities/approved IDs**. Candidate
schema validity, source agreement, literal equality, cryptographic hashes and unit
tests cannot authorize semantic truth. Actual reviewers/approvers must be named
privately by the owner; the production trust configuration is not filled by an
assistant. Amendments create new versioned evidence and explicit decisions.

Round 1 remains OPEN: author has both phases, R02 has sealed phase 1 and an issued
phase-2 package, R03 is pending. D1 is either complete the planned same-sample panel
or explicitly record a dated cutoff, membership and missingness. No cutoff is
assumed. Later submissions enter a new round/amendment. Existing packages stay
unchanged; disagreement tables, author's answers and B findings stay out of ongoing
blind review. Intake now validates exact raw bytes and the assigned issued ZIP.

Two external reviewers plus the author is a practical panel proposal, not a
universal minimum or a proof of reliability. A separate adjudicator handles
remaining disputes only after independent judgments are sealed. Report agreement
before discussion, including uncertain categories, overlaps and marginal counts;
report categorical reliability coefficients only where defined and appropriate.
Current new phase-2 tooling demonstrates exact agreement on synthetic inputs;
no actual phase-2 multi-reviewer coefficient or adjudication result exists.

## Corpus, exposure and C2

The extended audit inspected 22,861 existing JSON files. It confirms recorded
exposure for at least 192/1,000 MIDV-2020 instances across all ten types; 808 are
EXPOSURE_UNKNOWN. **All 1,000 template metadata records have now been accessed**.
Unknown historical output exposure is distinct from known metadata access. No
instance is certified unexposed, and pretraining overlap remains unknown.

Recorded hashes and aliases support metadata lineage only. Before a new cohort,
finish claim-relevant cross-version identity/content joins, decoded-pixel hashes,
near-duplicate grouping and capture/template lineage using permitted assets.
Repeated frames/crops/fields stay with the same physical instance. New captures
of used instances are not independent IDs. All ten template types are historically
exposed, so a template-generalization claim needs another justified sampling frame.
Source-license discovery is complete at provider level; artifact release rights,
attribution and anonymous redistribution still need D10.

The inventory contains 1,100 potential body/MRZ pairs on 400 instances (300 ID,
400 DOB, 400 expiry); zero satisfy C2 eligibility. Its mechanical comparisons
report 1,097 literal/precision differences and three unsupported MRZ formats.
These are not 1,097 wrong annotations: lexical keys and full-date versus YYMMDD
precision may refer to different semantics. No body/MRZ match is treated as truth.

A C2 case needs: primary supported before, primary removed after, a distinct
backup supported before and after, approved same-field equality, verified
provenance and an approved bound reference. A header box or transcript cannot
certify post-mutation readability. If a field lacks an eligible backup, retain the
failure reason and feasibility denominator; do not relabel it C1 or silently drop
it to improve the C2 result. Candidate IDs stay private until release approval.

## Sampling, analysis, resources and stopping

Unit: `(reader, before pixel, after pixel, field, mutation, reference version,
endpoint)`. Inference cluster: physical document instance. Preserve template,
capture and source lineage for additional dependence; controls have zero physical
IDs and remain separate. Equal cases across policies are paired, not separate N.

The [sizing draft](B_SIZING_AND_POWER_DRAFT_20261117.md) supplies 384 deterministic
design-effect sensitivity scenarios for precision and a paired normal contrast.
No owner margin/floor/N/seed/budget is selected. It is not exact achieved power or
an interval for the historical pilot. Define denominator fractions, eligibility,
missingness, cluster allocation and feasible caps before selecting IDs or looking
at new outputs. Reuse of old pilot labels remains development.

Proposed inference for a sufficiently sized new cohort: paired physical-ID cluster
bootstrap of predeclared rates/differences, stratified by sampling strata if needed;
seed, replication count, weighting and percentile/alternative interval choice need
validation before lock. Whole instances are resampled with all their comparisons
and policies together. Rare-event/empty bootstrap denominators remain NA and their
frequency is reported; do not discard replicates until a favorable interval
appears. Small numbers of clusters require a design revision, not row-level CIs.

One primary contrast/endpoint is proposed; any confirmatory family beyond it must
have multiplicity handling specified before lock (e.g. Holm for the chosen family).
Coverage/sensitivity floors are prespecified decision requirements, not substitute
endpoints selected after results. Secondary endpoints are relation correctness,
structure, selective risk, abstention, invalidity, truth availability, per-contract
and per-exposure descriptions. Report all declared panels and sensitivity analyses.
No undefined metric becomes zero; [accounting definitions](oracle_reliability/ACCOUNTING_AND_SIZING.md)
include deferrals in all-fault sensitivity and preserve unresolved alarms.

Resource planning must separate unique before/after reader calls from replayed
policy/reference arms. A naive upper call bound is `2 * IDs * cases/ID * readers *
repeats`; an exact deduplicated image-reader manifest is required before execution.
Set model-call, wall-time, storage and human active-minute caps; do not substitute
waiting wall time for annotation effort. No cost advantage is currently measured.

Freeze code, outputs interface, readers/model hashes, sampling manifest, seed,
approved reference/truth snapshot, analysis and caps before prospective outputs.
Stop at those caps; record timeouts, failures and deviations. Do not continue until
significance. If no feasible design fits, narrow the intended claim or use another
track with honest preliminary evidence. TASK6B/7B stays closed until a separate
owner scientific GO after D1–D12 and executable baseline validation.
