# P5 · Feasibility matrix

At the +10 percentage-point FAR reduction, all probabilities below are percentages of synthetic cohorts unless a different denominator is named. Brackets give pointwise 95% Wilson Monte Carlo intervals. Each scenario/point uses 1,200 cohorts in the recorded run. The nominal tests use the frozen v3 one-sided bootstrap limits.

| Profile | P(all three pass) | P(insufficient) | Issued / simulated | MDE point / MC-supported (pp) | Power-only verdict | Statistical verdict |
|---|---:|---:|---:|---:|---|---|
| reference | 65.9 [63.2, 68.5] | 0.0 [0.0, 0.3] | 1200/1200 | 12 / 12 | INFEASIBLE | INFEASIBLE |
| independent | 88.1 [86.1, 89.8] | 0.0 [0.0, 0.3] | 1200/1200 | 10 / 10 | FEASIBLE | INFEASIBLE |
| strong_dependence | 42.8 [40.1, 45.7] | 0.1 [0.0, 0.5] | 1199/1200 | — / — | INFEASIBLE | INFEASIBLE |
| rare_fault | 19.7 [17.5, 22.0] | 58.5 [55.7, 61.3] | 498/1200 | — / — | INFEASIBLE | INFEASIBLE |
| very_rare_fault | 0.0 [0.0, 0.3] | 100.0 [99.7, 100.0] | 0/1200 | — / — | INFEASIBLE | INFEASIBLE |
| missing_truth | 43.4 [40.6, 46.2] | 0.1 [0.0, 0.5] | 1199/1200 | 18 / — | INFEASIBLE | INFEASIBLE |
| informative_missing | 63.4 [60.7, 66.1] | 3.6 [2.7, 4.8] | 1157/1200 | 12 / 12 | INFEASIBLE | INFEASIBLE |
| low_disagreement | 90.0 [88.2, 91.6] | 0.0 [0.0, 0.3] | 1200/1200 | 10 / 10 | FEASIBLE | INFEASIBLE |
| high_disagreement | 44.8 [42.0, 47.6] | 0.0 [0.0, 0.3] | 1200/1200 | 15 / 15 | INFEASIBLE | INFEASIBLE |
| fewer_cases | 44.2 [41.5, 47.1] | 0.2 [0.0, 0.6] | 1198/1200 | 18 / — | INFEASIBLE | INFEASIBLE |
| tight_floors | 10.8 [9.2, 12.7] | 0.0 [0.0, 0.3] | 1200/1200 | — / — | INFEASIBLE | INFEASIBLE |
| near_full_coverage | 31.2 [28.6, 33.8] | 51.2 [48.4, 54.1] | 585/1200 | — / — | INFEASIBLE | INFEASIBLE |
| full_coverage | 0.0 [0.0, 0.3] | 100.0 [99.7, 100.0] | 0/1200 | — / — | INFEASIBLE | INFEASIBLE |
| high_deferral | 0.0 [0.0, 0.3] | 0.0 [0.0, 0.3] | 1200/1200 | — / — | INFEASIBLE | INFEASIBLE |

MDE is the first tested alternative whose joint pass estimate (or MC lower bound) reaches 80%. A dash means no such grid point. Inspect the curves before interpreting a crossing. The largest tested effect is 18 pp except for low disagreement (10 pp). Where a population floor fails, these are pass probabilities under a composite null; power and a useful MDE for that combination are inapplicable.

## Type I error across three true nulls

Numerator is false joint success; denominator includes every attempted cohort, including non-issued results. Each column changes the named population criterion; other assumptions are specified in the JSON. Some stress profiles can fail more than one population criterion.

| Profile | FAR difference = 5 pp | Coverage = 79.99% | Labelled sensitivity = 79.99% |
|---|---:|---:|---:|
| reference | 4.7 [3.6, 6.0] | 6.5 [5.2, 8.0] | 7.8 [6.4, 9.5] |
| independent | 5.3 [4.2, 6.8] | 6.4 [5.2, 7.9] | 8.2 [6.7, 9.9] |
| strong_dependence | 5.8 [4.6, 7.2] | 4.8 [3.7, 6.1] | 9.8 [8.3, 11.6] |
| rare_fault | 1.7 [1.1, 2.6] | 2.8 [2.0, 3.8] | 5.2 [4.1, 6.7] |
| very_rare_fault | 0.0 [0.0, 0.3] | 0.0 [0.0, 0.3] | 0.0 [0.0, 0.3] |
| missing_truth | 3.2 [2.3, 4.3] | 5.8 [4.6, 7.2] | 8.2 [6.8, 9.9] |
| informative_missing | 5.2 [4.1, 6.7] | 6.1 [4.9, 7.6] | 8.2 [6.8, 9.9] |
| low_disagreement | 4.2 [3.2, 5.5] | 5.3 [4.2, 6.8] | 8.3 [6.9, 10.0] |
| high_disagreement | 5.2 [4.1, 6.6] | 6.6 [5.3, 8.1] | 7.0 [5.7, 8.6] |
| fewer_cases | 4.2 [3.2, 5.5] | 6.3 [5.1, 7.9] | 6.5 [5.2, 8.0] |
| tight_floors | 0.6 [0.3, 1.2] | 2.5 [1.8, 3.5] | 5.7 [4.5, 7.1] |
| near_full_coverage | 2.6 [1.8, 3.6] | 6.4 [5.2, 7.9] | 3.4 [2.5, 4.6] |
| full_coverage | 0.0 [0.0, 0.3] | 7.7 [6.3, 9.3] | 0.0 [0.0, 0.3] |
| high_deferral | 0.0 [0.0, 0.3] | 0.0 [0.0, 0.3] | 0.0 [0.0, 0.3] |

## Interval coverage conditional on issuance at +10 pp

Each component reports P(lower limit ≤ true parameter | all three intervals issued). The last column requires simultaneous coverage; it has no separate 95% guarantee. Divide each hit count in the JSON by all trials for the probability of issuing covering bounds. NA means no bounds were issued.

| Profile | Decision coverage | All-fault sensitivity | Paired FAR difference | Simultaneous |
|---|---:|---:|---:|---:|
| reference | 92.9 [91.3, 94.2] | 88.1 [86.1, 89.8] | 95.8 [94.5, 96.8] | 78.2 [75.8, 80.5] |
| independent | 93.7 [92.1, 94.9] | 92.7 [91.1, 94.0] | 94.2 [92.8, 95.4] | 82.1 [79.8, 84.1] |
| strong_dependence | 92.5 [90.9, 93.9] | 86.7 [84.6, 88.5] | 95.3 [94.0, 96.4] | 76.5 [74.0, 78.8] |
| rare_fault | 92.6 [89.9, 94.6] | 85.1 [81.7, 88.0] | 94.4 [92.0, 96.1] | 74.9 [70.9, 78.5] |
| very_rare_fault | NA | NA | NA | NA |
| missing_truth | 92.2 [90.6, 93.6] | 86.2 [84.1, 88.0] | 95.9 [94.6, 96.9] | 76.5 [74.0, 78.8] |
| informative_missing | 91.4 [89.7, 92.9] | 88.5 [86.5, 90.2] | 94.8 [93.4, 96.0] | 77.1 [74.6, 79.4] |
| low_disagreement | 93.0 [91.4, 94.3] | 89.3 [87.5, 91.0] | 95.5 [94.2, 96.5] | 79.2 [76.8, 81.4] |
| high_disagreement | 92.1 [90.4, 93.5] | 88.2 [86.3, 90.0] | 94.8 [93.4, 95.9] | 77.1 [74.6, 79.4] |
| fewer_cases | 92.7 [91.1, 94.1] | 90.9 [89.1, 92.4] | 95.8 [94.5, 96.8] | 80.8 [78.5, 82.9] |
| tight_floors | 94.2 [92.8, 95.4] | 91.7 [90.0, 93.1] | 95.9 [94.6, 96.9] | 83.0 [80.8, 85.0] |
| near_full_coverage | 100.0 [99.3, 100.0] | 89.9 [87.2, 92.1] | 94.4 [92.2, 96.0] | 85.1 [82.0, 87.8] |
| full_coverage | NA | NA | NA | NA |
| high_deferral | 94.3 [92.9, 95.5] | 94.5 [93.1, 95.7] | 94.2 [92.8, 95.4] | 84.5 [82.3, 86.4] |

## Guard accounting at +10 pp

The first three counts partition insufficient cohorts. A bootstrap draw is invalid if either truth denominator is zero. Degenerate coverage is counted after the denominator guard and can coincide with another constant metric. Waiver is a counterfactual on identical resamples. It bypasses only the constant-coverage check.

| Profile | <30 clusters | Any undefined draw | Any constant metric | Constant coverage | Invalid draws / draws run | Joint pass with waiver (%) | Additional pass probability (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| reference | 0 | 0 | 0 | 0 | 0/12000000 | 65.9 | 0.0 [0.0, 0.3] |
| independent | 0 | 0 | 0 | 0 | 0/12000000 | 88.1 | 0.0 [0.0, 0.3] |
| strong_dependence | 0 | 0 | 1 | 0 | 0/12000000 | 42.8 | 0.0 [0.0, 0.3] |
| rare_fault | 678 | 0 | 24 | 0 | 0/5220000 | 19.7 | 0.0 [0.0, 0.3] |
| very_rare_fault | 1200 | 0 | 0 | 0 | 0/0 | 0.0 | 0.0 [0.0, 0.3] |
| missing_truth | 0 | 0 | 1 | 0 | 0/12000000 | 43.4 | 0.0 [0.0, 0.3] |
| informative_missing | 0 | 0 | 43 | 0 | 0/12000000 | 63.4 | 0.0 [0.0, 0.3] |
| low_disagreement | 0 | 0 | 0 | 0 | 0/12000000 | 90.0 | 0.0 [0.0, 0.3] |
| high_disagreement | 0 | 0 | 0 | 0 | 0/12000000 | 44.8 | 0.0 [0.0, 0.3] |
| fewer_cases | 0 | 0 | 2 | 0 | 0/12000000 | 44.2 | 0.0 [0.0, 0.3] |
| tight_floors | 0 | 0 | 0 | 0 | 0/12000000 | 10.8 | 0.0 [0.0, 0.3] |
| near_full_coverage | 0 | 0 | 615 | 615 | 0/12000000 | 64.3 | 33.2 [30.6, 35.9] |
| full_coverage | 0 | 0 | 1200 | 1200 | 0/12000000 | 65.6 | 65.6 [62.8, 68.2] |
| high_deferral | 0 | 0 | 0 | 0 | 0/12000000 | 0.0 | 0.0 [0.0, 0.3] |
