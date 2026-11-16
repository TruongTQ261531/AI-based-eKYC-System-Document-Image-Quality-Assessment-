# Strict reviewer intake, version 2 (17 November 2026)

This layer validates an already-issued portable package and its returned export.
It preserves the original bytes, checks the assigned package hash and sealed
phase order, and quarantines new submissions privately. It never creates gold,
closes a review round, changes a role, overwrites a historical import, or approves
a reference. Existing ZIPs and historical importers are unchanged.

From the research repository root, using the project Python environment:

```powershell
python -m research.evidence_contract.reviewer_tools.intake validate-review RETURNED.json --package ISSUED.zip --package-sha256 EXPECTED_SHA256 --reviewer ASSIGNED_CODE
python -m research.evidence_contract.reviewer_tools.intake ingest-review RETURNED.json --package ISSUED.zip --package-sha256 EXPECTED_SHA256 --reviewer ASSIGNED_CODE --dry-run
```

The organizer obtains the expected hash and code from the independently held
issuance receipt, not from the returned file. `validate-review` and `--dry-run`
write nothing. Removing `--dry-run` from `ingest-review` stores exact raw bytes,
canonical normalized JSON and a receipt in `local/reviewer_intake_v2/`. This is a
quarantine, not the old scientific-label import path. Duplicate canonical content
is rejected, including reformatted copies and existing legacy submissions.

Checks include UTF-8/JSON, duplicate keys, nonfinite values, exact export/item
schemas, enums/types, completeness declarations, known unique slots/cases,
package manifest/image hashes, assigned reviewer and own sealed phase 1. Partial
exports may contain completed entries; they remain explicitly incomplete.
Phase 2 exports do not contain their own reviewer code: binding uses the unique
phase-1 snapshot and package job. This cannot prove who physically filled a ZIP
or verify a person's independence. Human provenance still requires organizer
records. Original role mistakes are preserved; corrections are separate records.

`synthetic.py` creates explicitly `unit_injected` fixtures with `SYNTHETIC_`
identities. They cannot enter the human mode. No actual reviewer export is
generated, altered, resubmitted or used to test a write operation.

Private paths, reviewer notes, per-case joins, images and raw returned JSON must
not be published. Aggregate counts and hashes may be synchronized to GitHub.
