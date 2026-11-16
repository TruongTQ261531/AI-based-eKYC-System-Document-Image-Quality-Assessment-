# EASE 2027 submission readiness

Latest B milestone, 16 November: [Oracle Reliability & Abstention](../B_ORACLE_RELIABILITY_20261116.md)
P0/P1/P2 are complete for development: 58 symbolic controls, historical replay,
336 tests + 6 subtests, and an independent aggregate verifier. Stricter evidence
tiers still fail on correlated wrong references; no superiority is established.
[B claim ledger](B_CLAIM_TO_EVIDENCE_20261116.md) and [prospective draft](../B_PROSPECTIVE_PROTOCOL_DRAFT.md)
are available. No new B manuscript/PDF, human labels, inference or confirmatory
lock was created. Reviewer Round 1 remains open. Provider license/schema checks
advance corpus feasibility; exposure, independent truth, sizing and scientific
GO remain pending. Frozen papers and older receipts below retain their scope.

Latest intake, 16 November: [R02 completed all 86 phase-1 slots](../R02_REVIEW_INTAKE_20261116.md).
The organizer clarified that the reviewer is external and selected the author
role by mistake; the correction is separate from the immutable export.
Author/R02 phase-1 agreement is now available, with 19/86 semantic-key
disagreements (Cohen kappa 0.0239). R02's own 46-case phase-2 ZIP is prepared,
not completed; R03 is pending. No independent gold or superiority GO follows.
The frozen paper's endpoint results remain the author's single-review pilot.
Code, aggregate results and progress use **main as the sole branch**; earlier
progress-branch and zero-external-review statements below describe prior milestones.

16 November readiness milestone: [conditional representation analysis and actual
historical parser executions](../READINESS_ANALYSIS_20261116.md) are complete.
**260 Python tests and 6 subtests pass.** The [Emerging Results draft](output/pdf/emerging_20261116.pdf)
now compiles to **3 pages** in ACM anonymous review format and all rendered pages
were inspected. No overfull boxes, missing glyphs or undefined references remain.
[Build receipt](../execution/master_01/readiness_20261116/pdf_build_receipt.json).
The [22-file public replay archive](readiness_replay_20261116.zip) passes an
isolated extracted run with 596 actual parser calls. It is a development archive,
not the final anonymous submission supplement. Author/novelty review, final
anonymity, rights and scientific adequacy remain open. Research superiority is
still NO-GO; the new draft does not replace that gate or the frozen pilot.

Additional feedback-independent development on 16 November validated the
[reference-boundary prototype and constructed controls](../REFERENCE_CONTROLS_20261116.md).
The 252 injected executions reduce to 131 distinct comparisons/13 pixel pairs;
245 Python tests plus 6 subtests and 15 JavaScript tests pass. This adds software
and counterexample evidence, not external labels, natural-model accuracy or a
confirmatory GO. It does not replace the frozen manuscript's pilot results.

Status checked 16 November: exploratory A variants, reviewer package builders
and agreement tooling are implemented. Two phase-1 ZIPs are ready for private
handoff; no external judgments have been received. Public development code and
aggregate archives are synchronized on the progress branch, with main awaiting
review. This is not an anonymous conference release or a new scientific GO.
[Development](../A_DEVELOPMENT_20261116.md) · [Handoff](../REVIEWER_HANDOFF_VI.md) ·
[Synchronization](../execution/master_01/development_20261116/catchup_sync.json)

**Internal draft and local replication candidate prepared. Research submission remains blocked by evidence.** All 86 phase-1 observations and 46 phase-2 judgments are sealed and replayed. A one-project-author review supports descriptive subset counts; 17 cases have literal coherence flags. The apparent FAR difference is not robust to the post-hoc sensitivity panel. Independent references, adequacy and a new scientific GO remain pending. The three linked CFPs were checked again on 15 November 2026. [Current roadmap](../EASE2027_ROADMAP_VI.md) · [IFV results](../IFV_RESULTS_VI.md)

| Official track | Published deadline and format | Fit after evidence is available |
|---|---|---|
| Research Papers | Abstract 15 January 2027, full paper 22 January 2027, AoE. ACM conference format. 10 content pages plus 2 reference-only pages | Main target conditional on adequate evidence. Personal IFV collection is complete; independent reference, stronger coverage and confirmatory work remain pending. [Research Papers CFP](https://conf.researchr.org/track/ease-2027/ease-2027-papers) |
| Short Papers and Emerging Results | Abstract 22 February, paper 1 March 2027, AoE. 6 pages total | An option for a specific emerging finding with evidence and a clear scope. [Short Papers CFP](https://conf.researchr.org/track/ease-2027/ease-2027-short-papers-and-emerging-results) |
| Reproducibility and Negative Results | Abstract 22 February, paper 1 March 2027, AoE. 10 content pages plus 2 reference-only pages | An option if a well-supported analysis shows when strong simple baselines suffice. A small inconclusive study does not on its own support a negative result. [RENE CFP](https://conf.researchr.org/track/ease-2027/ease-2027-reproducibility-and-negative-results) |

The official conference site describes the EASE series as CORE A. The track comparison above concerns fit and evidence requirements. [EASE 2027](https://conf.researchr.org/home/ease-2027)

## Double-anonymous submission checklist

- [ ] Confirm a contribution, claims, locked evidence and an appropriate track. Apply the relevant ACM SIGSOFT empirical standards and discuss limitations of each inference. [Empirical standards](https://www2.sigsoft.org/EmpiricalStandards/)
- [x] Build the separate Emerging draft using ACM `sigconf,review,anonymous`; inspect all three pages and scan identifiers/metadata. Recheck the latest official class and final manuscript before submission.
- [ ] Write self-citations in third person. Keep code archive, datasets, metadata and version history anonymous in the submission. Prepare the final supplement with a non-identifying link. The local Markdown and paths are for internal use.
- [ ] Review usage and redistribution rights for specimen assets, fonts, public corpus components and model weights. Release hashes, configuration and replay instructions for material that cannot be redistributed.
- [ ] Record reviewer role, instructions, blinding, disagreements and approvals or exemptions required by the institution and publisher when applicable. Keep observations and identities private.
- [ ] Apply ACM authorship and AI-content disclosure policy. Authors verify every claim, citation, figure and artifact. Follow the CFP link to check the current disclosure wording. [Research Papers CFP](https://conf.researchr.org/track/ease-2027/ease-2027-papers)
- [ ] Review soundness, significance, novelty, verifiability and presentation against the official CFP. Compilation and layout inspection are complete for the Emerging draft; the full Research draft remains scientifically incomplete. No manuscript or artifact has been submitted.

The full Research source remains at [main.tex](main.tex), with the method diagram,
contract table and explicit confirmatory placeholders. Its historical source
checks passed, but compilation was unavailable at the 11 November checkpoint.
[Historical receipt](../execution/master_01/continuation_20261111/acm_source_verification.json).
On 16 November, a pinned portable Tectonic 0.17.0 compiler removed that environment
blocker. The new [Emerging source](emerging_20261116.tex) was built and visually
checked; `main.tex` was not rebuilt in this milestone. The measured dependency is
the bundled official `acmart` 1.83, recorded in the build receipt. Check the current
ACM distribution again for the final submission. The first build attempts and
their layout corrections are retained in the execution directory.

The [replication candidate](candidate_20261111_02.zip) passed a fresh-process scorer replay and extracted-archive verification. Its automatic identifier scan passed. It is tracked in the public development branch; final human anonymity and redistribution-rights checks remain open for a separate conference release. The corrected candidate preserves B2's graph-free interface and matches all stored decisions. Its historical build receipt retains the original local-only distribution state. [Candidate receipt](../execution/master_01/continuation_20261111/candidate_20261111_02_receipt.json)

The [15 November IFV aggregate supplement](ifv_aggregate_20261115_02.zip) adds
original and post-hoc sensitivity counts with a standalone consistency verifier.
It passed fresh-process and extracted-archive checks. Raw review content remains
private; verifying aggregate arithmetic does not reproduce human labels or
establish independent adjudication. [Receipt](../execution/master_01/ifv_20261115/aggregate_receipt.json)
