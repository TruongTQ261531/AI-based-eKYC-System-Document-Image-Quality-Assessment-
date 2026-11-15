# GitHub synchronization at completed milestones

The user's instruction of 16 November 2026 requires every completed milestone
to be recorded locally and synchronized to GitHub after relevant validation.
The standing project instructions are in [AGENTS.md](AGENTS.md).

Use the active progress branch `codex/ekyc-progress-20261116` while its changes
are under review. Fetch first, inspect the exact diff, stage explicit project
paths, commit, push normally and verify local HEAD against `git ls-remote`.
Do not report synchronization from a local commit alone. Do not force-push.

The initial bulk push to `main` was rejected by automatic approval review.
The safer alternative is the isolated progress branch and a reviewable pull
request. `main` stays unchanged until an approved merge; branch synchronization
must not be described as a completed merge into `main`.

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
