# Post-hoc CPU label-position diagnostic

The original test results, including zero photographed-subset body KIE F1,
were already observed before this supplement was designed. It is exploratory,
not a prospectively registered independent test or a new OCR reader. Never
replace the original CPU tables, locks, VLM choice or deployment gate.

On development photographs, the 48 reader/image calls contain 775 OCR boxes,
3 prefix-recognized labels, 33 additional boxes with a known alias inside the
line, and only one extracted body field. This motivates a limited check of
the printed-label head rather than a claim that the OCR engines read no text.
No individual test strings or reference values are used to create alias rules.

Both variants reuse the original global English/Vietnamese aliases and spatial
assignment. Search for the longest known alias anywhere in an OCR box and trim
only the preceding label prefix. The bilingual variant also chooses the final
same-key alias and removes a slash/parenthesis continuation without digits so
it is not mistaken for an inline value. Preserve 44-cell MRZ lines. Never
modify the original cached OCR predictions or add reference values/country IDs.

Evaluate both variants with/without the existing strict-check MRZ missing-key
fallback, for both readers: eight derived configurations sharing the existing
OCR calls. Report every development/test outcome. Record a development choice
before supplemental test rescoring, while explicitly acknowledging that the
original test summaries were already seen. These are not SOTA KIE baselines.
All latency totals are sums of the old OCR timer and new parsing timer, not
fresh end-to-end measurements. Raw parsed values stay in ignored cache.
Replay all 1728 derived score rows. No new neural OCR or VLM call is required.
