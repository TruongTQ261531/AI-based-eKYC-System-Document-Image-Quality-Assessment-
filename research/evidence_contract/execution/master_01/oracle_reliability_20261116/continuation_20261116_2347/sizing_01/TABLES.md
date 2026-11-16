# Planning sensitivity: illustrative, not an approved N

Full grid: 384 scenarios. All decisions remain pending.

Shown: 100 IDs, 6 cases/ID, 5% faults, 90% labels, 20% abstention. Width target 0.20 is illustrative.

| ICC | Ref defects | Coverage width | Sensitivity width | IDs for sensitivity width | IDs for paired 80% normal power |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0.02 | 0.064 | 0.292 | 222 | 3290 |
| 0.0 | 0.1 | 0.064 | 0.292 | 222 | 658 |
| 0.2 | 0.02 | 0.090 | 0.399 | 443 | 6579 |
| 0.2 | 0.1 | 0.090 | 0.399 | 443 | 1316 |
| 0.5 | 0.02 | 0.119 | 0.503 | 775 | 11514 |
| 0.5 | 0.1 | 0.119 | 0.503 | 775 | 2303 |

These are equal-cluster/effective-N approximations, not measured power or defensible final sample sizes.
A large result may exceed the available corpus; it is not a request to acquire that many IDs.
Rare events, informative missingness, template dependence and unequal clusters require a revised design/simulation before lock.
