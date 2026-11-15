# EASE 2027 submission readiness

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
- [ ] Move the draft into the official ACM Primary Article Template using the research track's anonymous review settings. Check page limits and PDF properties, links, author information, affiliations, identifiable paths, logos and acknowledgment fields.
- [ ] Write self-citations in third person. Keep code archive, datasets, metadata and version history anonymous in the submission. Prepare the final supplement with a non-identifying link. The local Markdown and paths are for internal use.
- [ ] Review usage and redistribution rights for specimen assets, fonts, public corpus components and model weights. Release hashes, configuration and replay instructions for material that cannot be redistributed.
- [ ] Record reviewer role, instructions, blinding, disagreements and approvals or exemptions required by the institution and publisher when applicable. Keep observations and identities private.
- [ ] Apply ACM authorship and AI-content disclosure policy. Authors verify every claim, citation, figure and artifact. Follow the CFP link to check the current disclosure wording. [Research Papers CFP](https://conf.researchr.org/track/ease-2027/ease-2027-papers)
- [ ] Review soundness, significance, novelty, verifiability and presentation against the official CFP. PDF compilation and layout inspection remain pending. No manuscript or artifact has been submitted.

The ACM review source now exists at [main.tex](main.tex), using the prescribed `sigconf,review,anonymous` settings. It contains the method diagram, contract table, verified development counts and explicit confirmatory placeholders. Source checks passed for balanced braces and environments, six citation keys, and identifiable local strings. The existing machine has no pdflatex, LuaLaTeX, XeLaTeX or Tectonic compiler. PDF compilation, layout inspection and the resulting page count therefore remain blocked by that resource. [Source-check receipt](../execution/master_01/continuation_20261111/acm_source_verification.json)

The [replication candidate](candidate_20261111_02.zip) passed a fresh-process scorer replay and extracted-archive verification. Its automatic identifier scan passed. It is tracked in the public development branch; final human anonymity and redistribution-rights checks remain open for a separate conference release. The corrected candidate preserves B2's graph-free interface and matches all stored decisions. Its historical build receipt retains the original local-only distribution state. [Candidate receipt](../execution/master_01/continuation_20261111/candidate_20261111_02_receipt.json)

The [15 November IFV aggregate supplement](ifv_aggregate_20261115_02.zip) adds
original and post-hoc sensitivity counts with a standalone consistency verifier.
It passed fresh-process and extracted-archive checks. Raw review content remains
private; verifying aggregate arithmetic does not reproduce human labels or
establish independent adjudication. [Receipt](../execution/master_01/ifv_20261115/aggregate_receipt.json)
