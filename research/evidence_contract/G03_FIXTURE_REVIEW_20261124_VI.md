# G03 — Independent follow-up review · 24/11/2026

Review baseline main: `47fbf848fedb148efa20b9888d22247c59995d98`. Exact fixture implementation blob `8d39409538fcd3e517a10aa9d5c1a09395694937`; test blob `d9efb6d2dcc31ba5bc63024681421366d50f27ea`. Reviewed against [C2-37 protocol](C2_37_ANALYSIS_PROTOCOL_VI.md), [B v3](B_PROTOCOL_V3_20261121.md), [P2](P2_AUDIT_VI.md), frozen `oracle_reliability/mrz_ablation_v1.py`, `reporting.py`, `protocol_v3.py`, `human_gate/state_matrix.py`. This is a separate ChatGPT review pass, **not** an external reviewer or Codex review.

## Verdict

`FIXTURE_ARITHMETIC_REVIEW_PASS / PRODUCTION_NOT_READY / PROTOCOL_INTEGRATION_REVIEW_REQUIRED`.
G03 v1 is a useful isolated descriptive prototype, not the end-to-end C2 pipeline. Keep its receipt immutable. Do not change its synthetic scope to real or treat synthetic flags and hash strings as authorization. No model execution, private data access, rights approval, real observations or prospective GO.

## Executed checks

Loaded the exact pinned GitHub module and test source into the JavaScript tool runtime. Re-executed all 43 existing assertions: 43 passed, including the original 4096 missing-truth assignments. This was not a Node CLI execution in an organizer checkout.

Additional deterministic stress test: 128 synthetic 37-row panels, LCG seed 20261124 (multiplier 1664525, increment 1013904223, unsigned 32-bit), six allowed D4 pointwise pairs uniformly sampled, boolean truth sampled with p=.5, null truth probability .22 capped at eight missing values per panel. Enumerated every missing-truth assignment per panel; compared sensitivity and FAR extremes in both arms and paired FAR difference extremes, plus coverage, abstention, sensitivity, FAR and selective risk per arm to independently counted values. 20 comparisons/panel, 2560 comparisons, 0 mismatches at tolerance 1e-12. This supports the finite-panel arithmetic, not the validity of the input or the statistical design. Neither the original nor the extra stress test establishes independent real truth.

## Adversarial probes of v1 (all nine accepted; not nine bugs)

Each starts from the existing synthetic fixture, changing only the described fields (and corresponding bindings where indicated). No real artifacts were used.

| ID | Mutation | Observed | Interpretation / severity for future real use |
|---|---|---|---|
| R1 | First case primary_removed_after=FAIL | eligible 36, metrics n=37, COMPLETE | High: eligibility and pointwise completeness are separate; cannot report 37 as qualified C2. Need explicit qualified and enrolled outputs, documented policy for guard outcomes. A failed C2 removal does not necessarily make a pointwise decision invalid. |
| R2 | First case provenance_verified=UNKNOWN | eligible 36, binary accepted, metrics n=37 | High: provenance is not enforced by the arithmetic module; real admission must fail closed on unverified bindings. |
| R3 | First case semantic_equality_approved=FAIL | eligible 36, metrics n=37 | High: distinguish source-semantic qualification from pointwise results; do not assume pointwise result establishes source equivalence. |
| R4 | Replace first candidate ID with SYNTH_REPLACEMENT in case and decision | COMPLETE | High integration gap: counts and prefix do not authenticate locked membership, order or exact field/source keys. |
| R5 | Replace first asserted/checked states with NO_FAULT/NO_FAULT, preserve hashes | COMPLETE; withdrawals decrease 6 to 5 | High integration gap: states are supplied, not recomputed from frozen compare_pair or bound to verified shared payload and policy version. |
| R6 | Copy first non-null truth evidence digest to next non-null truth row | COMPLETE, 25 known | High integration gap: truth evidence may legitimately cover multiple fields, but hash equality alone cannot establish the specific output, field, independent basis and authority. |
| R7 | First case rights=false, proposals/adjudication=false, reference=null, reference condition FAIL; remove its decision, leave cached outputs | rights 36, paired_outputs 37, paired_decisions 36, metrics null | Correctly suppresses full metrics; cache availability is not authorized availability. Clarify counters and reason categories. |
| R8 | Assign output of a second image the first image's output hash; update all dependent output digest references | COMPLETE, 45 image outputs | Not inherently a bug: identical output content on distinct images is possible. Real provenance must bind input, reader and output in an authenticated record, not require unique text hash. |
| R9 | First case reference=null/reference condition FAIL, both decisions UNKNOWN, bindings null | COMPLETE, approved 36, metrics n=37 | Potentially valid for enrolled pointwise abstention; not evidence of a complete qualified C2 frame. Explicitly label status and separate estimands. |

## Other gaps identified by code inspection

- Input has field_kind, not exact field, precision, primary/backup region IDs or source/transform and exposure metadata. Synthetic counts (37/18/45) cannot prove selection digest/membership. No real file or signed record verification.
- Reader config strings and matching digests check internal equality only. No actual runtime fingerprints, model weight/output byte verification, unique run identity or trusted manifest. Both arms must receive one verified shared payload and frozen comparator result. Use signed registry; do not invent replacement approvals.
- All cases must have rights and 37 decisions for a complete fixture. This safely suppresses primary metrics for missing decisions, but can indefinitely block reporting where a real candidate is denied or unresolved. Before observations, specify separate enrolled-flow and eligible-frame definitions, and when an incomplete eligible frame suppresses comparisons. Do not treat missing output as UNKNOWN or silently drop cases. No post-outcome cohort selection.
- Condition distributions currently contain candidate counts only. Protocol requires physical-ID contributions for each condition/status; IDs may occur in multiple statuses. Add eligibility/flow by ID and template, missing reason categories (rights, reference, source quality, outputs, decisions and truth), exposure and exact field/precision audit.
- Fixture cluster output includes synthetic IDs. Production projection must stay local; only release-reviewed aggregates may be published. Do not expose actual physical/candidate IDs, raw truth, raw output or record bindings on public GitHub.
- Existing Python reporting/protocol implementation is the primary comparator for a cross-language differential replay. New CJS fixture must not become a second independent definition of metrics. Run actual Node CLI and Python compatibility/differential tests on a checkout, including mixed validity, empty denominators and missingness; no claim of these tests having run yet.

## Next acceptance criteria (G03 v2 / G07)

1. Agree a pre-observation interpretation of enrolled 37 vs eight-condition qualified subset vs exact paired endpoint frame. Distinguish authority for decision, C2 semantic eligibility, independent fault truth. Record missingness, including all nonqualifying rows, without changing original protocol silently.
2. Prefer a single Python statistics core or explicitly cross-check CJS results with existing Python protocol and reporting. Retain v1 snapshot and add targeted tests for above probes, mixed status, candidate duplication/reordering, signed registry/rights mismatch, nonmatching field/precision/regions, run digest and incomplete frame. Tests that simulate authorization must not accept real production.
3. Build a separate local adapter: verify exact private locked queue/selection and artifact digests, rights and signed authority/events, verified model and per-output records, same payload for frozen comparator, separate output-bound truth. Use synthetic end-to-end fixture first. No actual C2 execution until separate approvals. 
4. Independent code review and actual CLI replay (GitHub CPU CI or local ordinary command). Codex can review locally once private integration is possible, but does not need to write pure arithmetic; human authority/truth remain external. No need to spend current weekly quota on a re-review of 43 tests alone.

No change to C2-37 D10, 0 approved real references, 0 exact real cache pairs, NO_GO_SUPERIORITY, GO_PREPARATORY_ONLY, P5B INFEASIBLE, TASK 6B/7B BLOCKED. G03 status is **fixture prototype validated; qualification, real-input integration and external review pending**, not production complete. No changes to original progress weighting.
