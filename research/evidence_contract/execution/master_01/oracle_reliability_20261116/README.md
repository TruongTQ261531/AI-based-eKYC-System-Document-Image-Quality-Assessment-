# B Oracle Reliability checkpoint — 16 November 2026

Start with [the result report](../../../B_ORACLE_RELIABILITY_20261116.md),
[prospective draft](../../../B_PROSPECTIVE_PROTOCOL_DRAFT.md) and
[claim ledger](../../../paper/B_CLAIM_TO_EVIDENCE_20261116.md).
P0/P1/P2 are complete for development, with 0 new inference/training/reviews.
Scientific gate stays NO_GO_SUPERIORITY; Round 1 stays open.

| Artifact | Meaning |
|---|---|
| `p0_intake.json`, `P0_AUDIT.md` | Starting state, documents read, baseline and 2,685 protected files |
| `development_plan.json` | Plan recorded before new development runs, not a prospective study lock |
| `development_failures.json` | Initial invariant test's incorrect expected permutation count and correction |
| `run_01/` | Original 57-case development run and exact source snapshots |
| `control_amendment_02.json`, `run_02/` | Post-run correlated-poison addition, final 58-case run with all old cases retained |
| `run_02/expected_vs_actual.md` | Expected policy state, observed state and constructed task truth, separately |
| `regression_tests_02.log/json` | Final Evidence Contract suite: 336 passed, 6 subtests passed; earlier logs retained |
| `run_02/arithmetic_verification.json` | Independent stdlib arithmetic/hash check: 492 metric groups, 823 cells |
| `run_02/organizer_replay.json` | Reexecuted policy and private historical joins match final records/cells/report |
| `aggregate_replay_02.zip`, `aggregate_package_receipt.json` | Public arithmetic-only archive; checked after extraction in an isolated Python process |
| `inspect_midv_metadata.py`, `midv_metadata_feasibility.json` | Read-only schema/exposure audit of existing local metadata; no new images selected |
| `SOURCES_AND_FEASIBILITY.md` | Primary source links, directly checked license and remaining data limitations |
| `preservation_after.json`, `completion_manifest.json` | Protected input check and hashes of delivered code/results/docs |

From the research repository root, using its Python environment:

```powershell
python -X utf8 -B research/evidence_contract/oracle_reliability/verify.py research/evidence_contract/execution/master_01/oracle_reliability_20261116/run_02
python -X utf8 -B research/evidence_contract/execution/master_01/oracle_reliability_20261116/inspect_midv_metadata.py .
```

The second command requires existing private provider metadata and outputs only
aggregate schema/exposure counts. Full historical replay likewise needs organizer
data. Use a fresh directory under this checkpoint with
`python -m research.evidence_contract.oracle_reliability.run --destination <fresh-path>`.
The runner refuses overwrites and preserves private per-case historical joins
under `local/master_01/oracle_reliability_20261116/`. `run_01` uses its own source
snapshot; current code generates the amended 58-case set.

For public verification, extract `aggregate_replay_02.zip` and run
`python -I -B verify.py run_02`. This recomputes arithmetic from published cells,
not the underlying human judgments or policy logic. No reviewer IDs, notes,
images, actual model strings, weights or private analyst joins are in the archive.
It is a development artifact, not a final anonymous conference supplement.
