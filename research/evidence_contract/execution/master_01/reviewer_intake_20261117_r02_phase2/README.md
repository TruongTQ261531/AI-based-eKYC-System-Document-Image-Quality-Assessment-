# R02 phase-2 intake receipts — 17 November 2026

[Vietnamese report](../../../R02_PHASE2_REVIEW_INTAKE_20261117.md).
This namespace receives the real user-supplied R02 phase-2 export and computes
interim paired agreement. Round 1 remains OPEN; no labels are pooled, no real
adjudication or reference approval is performed, and the scientific gate stays
NO_GO_SUPERIORITY. The author's frozen report is unchanged.

| Receipt | Observed outcome |
|---|---|
| `preflight_01.json` / `preflight.json` | Complete 46/46, own R02 phase-1/package binding, 3,645 files protected |
| `targeted_tests_01.json` | Exit 1: 56 passed, 9 setup errors; basetemp parent had not yet been created by prepare. The old runner omitted an errors counter; the exact log is retained |
| `targeted_tests_02.json` | 65 passed after prepare completed |
| `intake_01.json` / `intake.json` | Raw bytes quarantined, exact answers sealed using frozen own-phase-1 guards |
| `analysis_01.json` | Exit 1 before outputs: unrecognized concrete diagnostic stratum in the new comparison adapter |
| `targeted_tests_03.json` | 70 passed after handling all four frozen diagnostic families; unknown strata still rejected |
| `analysis_02.json` | Interim comparison and separate R02 report generated successfully |
| `full_tests_01.json` | 432 passed, 6 subtests passed |
| `aggregate_audit_01.json` / `aggregate_verification.json` | Independent stdlib arithmetic: 18 agreement tables, 216 method panels, 12 alarm panels |
| `preservation_replay_01.json` / `verification.json` | All 3,645 protected files unchanged; exact raw bytes, answers and private paired replay pass |
| `completion_manifest.json` | Public artifact hashes, input/private artifact hashes and milestone limits |

Every run receipt retains the explicit command, exit code, UTC times, Python
version, pre-milestone Git HEAD and exact stdout/stderr hash. Logs are preserved
as recorded, including Windows line endings. The first runner version equals
the frozen prior continuation runner; later receipts add the `errors` count.
The old failure receipts are not rewritten to appear successful.

Public replay, from the repository root (requires only stdlib and public JSON):

```powershell
python -X utf8 -B research/evidence_contract/execution/master_01/reviewer_intake_20261117_r02_phase2/audit_public.py
```

Relevant software tests, using a fresh existing-parent temporary location:

```powershell
python -X utf8 -B -m pytest -q -p no:cacheprovider research/evidence_contract/tests
```

`workflow.py` is an organizer-only, dated intake, bound to the exact input hash
and issued package. Prepare, ingest and analyze write fresh receipts and refuse
to overwrite existing results; **do not rerun ingest** for the same review.
The verify action also writes a fresh receipt; the executed command and result
are retained here. Full provenance replay needs the ignored private evidence.
The standalone aggregate audit does not need it and does not prove truth.

Private copies, quarantine receipts, sealed answer/label files, exact canonical
joins, coherence details and disagreement rows stay below `local/`. Public
outputs contain categorical aggregates, anonymous cluster groups and hashes;
no raw answers, transcripts, reviewer notes, images or ZIPs are released.

`CONFIRMED_FAULT` is the existing operational label, not adjudicated gold or a
verified software root cause. Each review uses its own phase-1 observations.
The R02 role correction remains separate from the raw mistaken author role.
The same 42 primary comparisons cover only three physical IDs. No model call,
training, new cohort, CI/p-value, approval, closure or superiority claim occurs.
