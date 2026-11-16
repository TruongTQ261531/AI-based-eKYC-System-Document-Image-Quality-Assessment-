# Reference authority and adjudication development workflow

17 November 2026. **PREPARATORY ONLY. Production authority is unconfigured;
approved production references = 0.** Install the pinned extra dependency in
`workflow_requirements.txt` to run the signed workflow tests.

The candidate registry binds the frozen v2 reference, image/mutation context,
physical-instance hash, source artifact/version, field, value kind, declared
precision, rights record and author. Mechanical schema validity and a content
hash are never semantic approval. Lexical proposals in `semantic_registry.json`
also remain unapproved. Unsupported or ambiguous mappings remain UNKNOWN.

## State and authorization contract

`MECHANICALLY_VALIDATED -> REVIEWER_PROPOSED -> ADJUDICATED -> OWNER_APPROVED`.
An adjudicator may instead record REJECTED or UNRESOLVED. An approved candidate
can become REVOKED or SUPERSEDED; terminal candidates cannot be reapproved.
An unresolved decision needs a new versioned candidate/amendment, not an in-place
edit. The `supersedes_id` field on a SUPERSEDED event points to its replacement
candidate (it does not approve that replacement).

Two distinct reviewer proposals, a separate adjudicator and a separate reference
approver are development workflow guards. They do not establish a statistically
sufficient panel or verified independence. The owner must accept or amend this
workflow before production use. Author and reference approver may be the same
person, but that approver cannot substitute for the two assessors/adjudicator.

Every journal event requires an Ed25519 signature from a separately designated
public key and role, exact bindings, version, timestamp, evidence hashes, sequence
and previous-event hash. Candidate authors cannot submit their own public key as
authority. `production_trust.json` deliberately contains no authorities, protocol
approval or journal checkpoint. `approved_ids()` therefore returns the empty set.
Once configured by the owner, the expected checkpoint detects a truncated journal;
missing signatures, incorrect versions/bindings and revoked candidates fail closed.

The production entry point is `reference_registry.evaluate_production()`. Frozen
low-level policy APIs are preserved for reproducibility and accept explicitly
supplied ID sets; those APIs are not a production authorization boundary. A person
with write access to code/trust configuration can bypass software controls.
Signatures authenticate assertions by designated keys, not identity, independence,
truth, license compliance or source correctness. The code cannot provide those
scientific judgments. Private signing keys must never be committed.

## Adjudication preparation

`adjudication.workflow.normalized_view()` validates the original export and an
organizer-held one-to-one join; the join digest, raw hash and package job remain
bound. A signed round-closure decision must name the exact immutable views and
dated cutoff basis. No such production closure has been made. Round 1 is OPEN.

After authorized closure, `build_packet()` preserves each judgment and reports
pairwise exact agreement before discussion, with its common-item denominator.
Exact agreement includes coincident uncertain answers and is not a reliability
coefficient or evidence of truth. Disagreement/uncertainty are retained. A distinct
adjudicator supplies an explicit signed ACCEPT/REJECT/UNRESOLVED decision with
basis hashes; ACCEPT only proposes a candidate and cannot approve a reference or
replace labels. Published results require a later independently audited join.

Run the self-contained demonstration with:

```powershell
python -m research.evidence_contract.adjudication.synthetic_dry_run
```

All keys, assessors, decisions and evidence in that command are SYNTHETIC. The
demonstration exercises agreement, disagreement, uncertainty, explicit decisions,
approval and revocation while production remains empty. It never sends a message,
imports real submissions, changes historical labels, or opens scientific GO.

## Corpus and C2 boundaries

The new audit hashes all inspected JSON twice and stores per-instance lineage and
file inventory privately. Public results contain only aggregates and digests.
Explicit study records establish exposure; missing records produce
EXPOSURE_UNKNOWN, never unexposed. Cache links rely on recorded hashes; original
image bytes, decoded pixels and near duplicates have not been re-audited. Other
MIDV versions and pretraining overlap remain outside this audit's completeness.

C2 inventory is a source-pair feasibility list from cached provider annotations.
It does not select a cohort. All seven eligibility conditions must be explicitly
true, including supported backup after mutation and separately approved semantic
equality/provenance/reference. A literal match, check digit, lexical field alias
or source count cannot satisfy these conditions. Full-date and YYMMDD precision
differences remain distinct. Provider `id_number` is only a lexical proposal; its
semantic role must be checked against that document type before body/MRZ equality.

Method reference: [cryptography Ed25519 API](https://cryptography.io/en/50.0.2/hazmat/primitives/asymmetric/ed25519/).
