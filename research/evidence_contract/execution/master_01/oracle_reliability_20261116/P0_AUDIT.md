# B Oracle Reliability: P0 audit

16 November 2026. Starting revision: `63cdc07a13b1c7f95a5cba73b37a331e1cab0519`.
The supplied handoff is input to this development task, not a change to frozen
protocols or a scientific GO. Its exact byte hash and the 21 source documents
read are recorded in `p0_intake.json`. No newer reviewer submission was found.

50 existing reference-policy, agreement, package and IFV tests pass. The R02
intake verifier reproduces the author report and checks 2,493 historical assets.
A larger pre-change protection manifest is private; the public receipt records
its size. A repeated test run and exclusive-write refusal are documented in
`p0_followup.json`; the log contains the second successful 50-test run.

| Claim | Classification | Evidence / limit |
|---|---|---|
| Historical pilot and R02 phase-1 intake are computationally replayable | SUPPORTED_DEVELOPMENT | Existing sealed receipts and intake verifier; no external phase-2 labels |
| Reference binding and typed checks can gate decisions | SUPPORTED_DEVELOPMENT | Version-1 software controls; a hash does not establish truth |
| Hardened source checks and abstention may improve oracle decisions | EXPLORATORY | New version and controlled evaluation planned, not yet executed at this P0 checkpoint |
| Graph beats an equally informed flat baseline | UNSUPPORTED | Existing parity and boundary results; equal-information controls required |
| Fewer alarms establish improved reliability, or independent gold exists | UNSUPPORTED | Coverage, missed faults and unresolved alarms must remain visible |
| Old images become unseen by adding reviewers | UNSUPPORTED | Same physical IDs and development exposure remain |

Continue P1/P2 under the pre-execution `development_plan.json`. New controls
must be explicitly injected; historical actual outputs and reviewer labels stay
separate. No training/inference budget, no confirmatory lock, no external
reference approvals. R02/R03 collection remains open and its issued ZIPs frozen.
