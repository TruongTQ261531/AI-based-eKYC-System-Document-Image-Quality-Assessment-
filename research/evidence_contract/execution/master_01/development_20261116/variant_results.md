# A development variants — exploratory

Post-pilot analysis on unchanged outputs and one-author labels. Original A is frozen.
A_dual uses B3 for the field lane and A for the relation lane; this is not a superiority result.

| Panel | Variant | Pointwise TP/FP/FN/TN | Coverage | Relation TP/FP/FN/TN |
|---|---|---|---|---|
| original | A_frozen | 2/0/5/19 | 18/26 | 2/0/0/19 |
| original | A_change_union | 4/0/3/19 | 20/26 | 2/0/0/19 |
| original | A_dual | 7/3/0/16 | 26/26 | 2/0/0/19 |
| original | A_reference_gate | 0/0/7/19 | 0/26 | 0/0/2/19 |
| original | B3 | 7/3/0/16 | 26/26 | 2/3/0/16 |
| original | A_flat | 2/0/5/19 | 18/26 | 2/0/0/19 |
| withholding_sensitivity | A_frozen | 2/0/4/14 | 16/20 | 2/0/0/14 |
| withholding_sensitivity | A_change_union | 3/0/3/14 | 17/20 | 2/0/0/14 |
| withholding_sensitivity | A_dual | 6/0/0/14 | 20/20 | 2/0/0/14 |
| withholding_sensitivity | A_reference_gate | 0/0/6/14 | 0/20 | 0/0/2/14 |
| withholding_sensitivity | B3 | 6/0/0/14 | 20/20 | 2/0/0/14 |
| withholding_sensitivity | A_flat | 2/0/4/14 | 16/20 | 2/0/0/14 |

The reference-gate control has no approved independent references and therefore abstains; its low alarm count is not an accuracy improvement.
No external reviewers, C2 evidence or population confidence were manufactured. New reference and a locked study remain necessary.
