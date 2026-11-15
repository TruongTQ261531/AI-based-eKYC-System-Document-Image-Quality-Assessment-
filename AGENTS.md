# Project instructions

- The user requires GitHub synchronization at every completed work milestone.
  This is standing authorization to commit and push completed project code,
  documentation, aggregate results and validation receipts to the configured
  repository, after relevant checks pass. Do not wait for a repeated request.
- Fetch and inspect the remote before pushing. Use a normal fast-forward push;
  never force-push or discard another contributor's changes. Verify local HEAD
  equals the remote branch after a successful push. Report a concrete failure
  if synchronization cannot finish; do not call local-only work synchronized.
- Stage explicit, reviewed project paths. Keep raw human submissions, reviewer
  identities/notes, local analyst joins, model caches, credentials, weights and
  unapproved image bundles out of the public repository. Publish aggregate
  progress and hashes instead. Do not send messages to reviewers unless asked.
- Preserve the frozen A/baseline implementations, samples, raw inference logs,
  review exports and prior receipts. Develop exploratory variants under new
  names and report endpoint differences, exclusions, costs and negative results.
- The application at the parent project root is a separate runtime copy from
  this research worktree. Archive and hash its completed source changes under
  `engineering/` when syncing progress; do not silently replace frozen readers.
