# Denominators and prospective sizing preparation

17 November 2026. This supplement does not change frozen results, select a cohort,
estimate population performance or approve a statistical design.

## Explicit oracle accounting

`reporting_v2.py` accepts the frozen public contingency cells, preserves every
legacy metric and adds UNKNOWN abstention, INVALID_TEST, combined deferral,
structural error and truth availability rates over all rows. It separately counts
unresolved truth. `verify_reporting_v2.py` independently reconstructs all group
keys and arithmetic using the frozen standalone verifier, without importing the
new generator. Groups are overlapping descriptive views, never extra observations.

| Measure | Numerator / denominator | Zero denominator |
|---|---|---|
| Coverage (all) | FAULT + NO_FAULT + STRUCTURAL_ERROR / all rows | NA |
| Coverage (labeled) | decided with known truth / known truth | NA |
| UNKNOWN abstention | UNKNOWN / all rows | NA |
| Invalidity | INVALID_TEST / all rows | NA |
| Combined deferral | UNKNOWN + INVALID_TEST / all rows | NA |
| All-fault sensitivity | alarms on labeled faults / all labeled faults, including deferrals | NA |
| FAR | alarms on labeled nonfaults / all labeled nonfaults | NA |
| Selective risk | wrong binary decisions / decided rows with known truth | NA |
| Structural error | STRUCTURAL_ERROR / all rows in that endpoint | NA |
| Truth availability | known truth / all rows | NA |

Structural errors are a separate endpoint; unusable structure leaves semantic
endpoints UNKNOWN. An abstained nonfault counts as a nonalarm in alarm confusion,
not as a verified NO_FAULT. Unknown truth never becomes negative truth. All-abstain
risk is NA, not zero; a low FAR with poor coverage is not superiority. Alarm
accounting retains unresolved alarms. No uncertainty interval is added to the old
three-ID pilot. More raters do not create more independent physical instances.

## Reproducible planning sensitivity

`sizing.py` evaluates the complete grid in `sizing_assumptions.json`. Every effect,
floor, seed, ID cap and budget requiring an owner decision remains null. Values
prefixed `illustrative_` are examples, not recommendations or preregistration.
The endpoint rates are separate marginal precision illustrations, not a jointly
realizable confusion matrix or a generated prospective dataset.

For K physical IDs, m cases/ID, assumed within-ID ICC rho and denominator fraction
q, the calculation uses DE = 1 + (m - 1) rho and n_eff = K m q / DE. It keeps the
full-cluster DE after thinning: conservative under homogeneous nondifferential
missingness, but not a repair for informative missingness. The correlation formula
is an approximation described in the [Cochrane methods handbook, section 23.1.4](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-23).
Its use here concerns correlated observations; this is not a clinical trial.

Planning interval widths use the [NIST Wilson formula](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
at the illustrative rate and fractional effective N. Those widths are NOT valid
reported confidence intervals for future clustered data without further analysis.
Expected fault prevalence, reference-defect prevalence and label availability
reduce relevant denominators; abstention reduces the selective-risk denominator.
Invalidity is set to zero only in this illustrative calculator; a nonzero rate
requires an explicit model amendment, not silently dropped observations.

For paired false alarms, let D = baseline alarm - checked alarm on the same known
nonfault row. With discordant probabilities p10 and p01, E[D]=p10-p01 and
Var(D)=p10+p01-(p10-p01)^2. The calculator uses a two-sided normal approximation
with that variance, inflated by the illustrative DE. It is not exact McNemar power,
not a noninferiority calculation and has no small-cluster or rare-event correction.
No observed pilot effect is used to claim achieved power. Fewer than 30 clusters
is flagged as a diagnostic warning, not an endorsed sufficiency threshold.

Scenarios can imply more IDs than the available corpus. This diagnoses a mismatch
between the assumed estimand, prevalence and precision; it never authorizes
acquisition or changes the goal until an attractive sample size appears. A locked
design needs a meaningful effect/floor, cluster allocation, unequal-size/template
dependence and missingness sensitivity, then an appropriately validated simulation
or analytic justification. It must stop at its predetermined cap regardless of
significance. Fields, frames, crops and repeated interventions cannot be counted
as new independent IDs.

Reproduce from the research root with the project Python environment:

```powershell
python -m research.evidence_contract.oracle_reliability.reporting_v2 --input HISTORICAL_AGGREGATE_CELLS.json --output research/evidence_contract/execution/NEW_REPORT
python -m research.evidence_contract.oracle_reliability.verify_reporting_v2 HISTORICAL_AGGREGATE_CELLS.json research/evidence_contract/execution/NEW_REPORT/report.json
python -m research.evidence_contract.oracle_reliability.sizing --output research/evidence_contract/execution/NEW_SIZING
```

Output folders must be new. `None`/JSON `null` denotes NA, never an implicit zero.
