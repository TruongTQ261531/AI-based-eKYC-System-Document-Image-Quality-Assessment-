# GitHub synchronization at completed milestones

The user's instruction of 16 November 2026 requires every completed milestone
to be recorded locally and synchronized to GitHub after relevant validation.
The standing project instructions are in [AGENTS.md](AGENTS.md).

The user's subsequent explicit instruction on 16 November consolidates all
completed progress into `main`, the sole working and synchronization branch.
The progress branch was fast-forwarded into main at `df9f937`; its redundant
branch references are removed after verifying the remote main includes it.
Fetch first, inspect the exact diff, stage explicit project
paths, commit, push normally and verify local HEAD against `git ls-remote`.
Do not report synchronization from a local commit alone. Do not force-push.

Historically, automatic approval review rejected the initial bulk main push,
so work used an isolated progress branch. The user's later explicit consolidation
request authorized the main update, which succeeded without a force-push.
Earlier receipts and notes about a pending main merge retain their historical meaning.

Publish code, progress documents, aggregate results and hashes. Raw human
reviews, reviewer identities/notes, analyst joins, image bundles awaiting release
approval, weights, caches and credentials stay local. Standalone reviewer ZIPs
are private handoff artifacts; public package receipts document their hashes.

The parent application's completed changes are archived under
`engineering/application_20261114/` with source hashes and a patch. The frozen
research reader is not silently replaced to make the runtime copy identical.

Historical receipts preserve their state at creation. A 15 November receipt
whose archive was then local remains immutable; current repository distribution
is recorded by the later synchronization receipt. A public development repository
is distinct from an anonymous, rights-reviewed conference supplement.
