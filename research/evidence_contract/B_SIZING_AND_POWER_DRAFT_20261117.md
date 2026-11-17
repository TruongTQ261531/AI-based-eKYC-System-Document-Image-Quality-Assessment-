# B sizing and power draft — 17 November 2026

**PENDING_OWNER_DECISION.** A deterministic calculator and 384 scenarios have run;
no sample size, margin, floor, cohort, seed or resource cap is approved.

The [calculator and assumptions](oracle_reliability/ACCOUNTING_AND_SIZING.md) explain
both precision-based planning and a paired contrast approximation, including their
limits. [Full JSON](execution/master_01/oracle_reliability_20261116/continuation_20261116_2347/sizing_01/sizing.json)
and [compact table](execution/master_01/oracle_reliability_20261116/continuation_20261116_2347/sizing_01/TABLES.md)
are reproducible without a notebook, private images, model inference or training.

| Design element | Proposed interpretation | Still needs decision/validation |
|---|---|---|
| Unit / cluster | Paired field comparison / physical instance | Cases, strata, unequal sizes, capture/template dependence |
| Primary endpoint | Paired FAR difference on independently labeled nonfaults in a fixed reference-defect panel | D4/D5: contrast, intervention set and exact panel |
| Precision targets | Widths for FAR, all-fault sensitivity, coverage, UNKNOWN abstention, selective risk | D6–D8: useful precision and floors; examples do not set these |
| Denominators | All-case rates preserve UNKNOWN and INVALID_TEST; truth-conditioned rates use known truth only | Separate invalid stratum; unresolved-truth sensitivity |
| Label missingness | Scenario label fraction 0.7/0.9 | Nondifferential assumption is illustrative, not established |
| Fault prevalence | 0.05/0.20 sensitivity grid | No prevalence estimated from three-ID pilot |
| Reference defects | 0.02/0.10 illustrative subset fractions | Deliberately sampled interventions need explicit design weights and scope |
| Dependence | ICC 0/0.2/0.5, 2/6 cases per physical ID, 20/50/100/200 IDs | All are assumptions; zero ICC is an optimistic boundary |
| Expected abstention | 0.2/0.6 | Tier is not a calibrated confidence probability |
| Analysis intervals | Proposed whole-ID paired bootstrap on a sufficiently sized cohort | Validate rare-event/empty-replicate handling and freeze seed/method |
| Multiplicity | One primary contrast proposed; additional confirmatory family declared and adjusted | Owner acceptance of family and method before lock |
| Success | Primary effect plus coverage/sensitivity requirements | All meaningful effects and noninferiority margins remain null |
| Budget / stop | Fixed IDs, reader calls, human active time and compute caps | No cap selected; never stop when significance becomes favorable |

The illustration at 100 IDs, six comparisons/ID, 5% faults and 90% labels shows
why frame counts are misleading: at ICC 0.2, the planning sensitivity interval
width is approximately 0.399, while coverage width is 0.090. An illustrative full
width target of 0.20 for sensitivity would imply 443 IDs under those assumptions.
For a five-percentage-point paired FAR contrast within a 2% reference-defect
subset, the same approximation implies 6,579 IDs for illustrative 80% normal
power, beyond this 1,000-instance corpus. **Neither number is a recommendation.**

These results motivate checking design feasibility, prospective reference-defect
sampling and the claim's population. Oversampling a rare defect can characterize
that defect efficiently but cannot estimate its natural prevalence unweighted.
No design choice is made here to force a manageable N. Marginal illustrative rates
are not a jointly simulated confusion matrix. Small-cluster, rare-event, unequal-
size and informative-missingness effects require validated analysis/simulation
before a scientific lock. The historical pilot remains descriptive, with CI/power
claims unavailable.

For two external reviewers plus the author, review reliability is a separate
design dimension: it helps characterize annotation disagreement but does not
increase the physical-ID sample size. Remaining disagreement may require a
separate adjudicator. No fixed reviewer count guarantees truth or EASE acceptance.
