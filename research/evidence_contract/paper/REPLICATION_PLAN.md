# Replication artifact plan

The first reusable bundle should contain fictional development fixtures, format and provenance schema, the frozen method/baseline code, safe example outputs, exact commands, lock/seed/budget metadata, aggregate results, and the claim-to-evidence ledger. Provide a score-only mode with no predictor loader. Report expected valid/invalid/uncertain counts and evidence that each actual call was linked to a completed raw payload.

| Layer | Include or reproduce | Hold private or document |
|---|---|---|
| Setup | Python version, pinned environment/overlay dependencies, package/reader/checkpoint and preprocessing hashes, CPU/GPU configuration | Weights without release rights and machine-specific absolute paths |
| Inputs | Release-approved fictional specimens or deterministic generators and input hashes. Separate roles and lineage. Include minimum valid and invalid controls | Unlicensed corpora, private annotations, raw reviewer data |
| Run | Registry of readers, expected manifest and call budget, cache schema, audit log for actual calls, restore/replay instructions | Credentials, personal embeddings and local filesystem identifiers |
| Score | Baseline, ablations and stats scripts, frozen method versus reviewer join policy, verified role labels, aggregate effect sizes and raw denominator counts | Analyst joins containing reviewer observations or predictions that cannot be public |
| Verify | Compact fixture self-test, receipt SHA and replay digest; document how to check anonymous files and reconstruct same results | Public or identifiable Git history before review |

A local [development candidate](candidate_20261111_02.zip) now implements the score-replay portion of this plan. It contains 19 files, including the original code for A/B0/B2/B3/A_flat, fictional development graphs and cached outputs, aggregate stage/control records, a manifest and verification entry point. A fresh Python process, with inherited repository paths ignored, reproduced 660 method decisions on 132 cases. The extracted ZIP passed the same check. A modified-copy fixture was rejected by its hash check. The archive uses fixed timestamps and its scan found no configured local identity strings. [Build receipt](../execution/master_01/continuation_20261111/candidate_20261111_02_receipt.json) · [Archive verification](../execution/master_01/continuation_20261111/archive_verification.json)

After extracting into a local folder, run `python -I -B verify_results.py` for the standard-library integrity and aggregate check. Use `python -I -B verify_results.py --oracle` in the existing research Python environment for the five frozen scorers. The candidate records NumPy, Pillow and OpenCV versions. Both entry points make zero model calls.

The verified subset concerns stored development decisions. Original image validity, human readability, independent replication, model-inference reproduction and confirmatory findings remain separate obligations. Rights and final human anonymity review are required before publication. The bundle has stayed local. [Technical replay](../TASK7_REPLAY_AND_REPORTING.md) · [Claim ledger](CLAIM_TO_EVIDENCE.md) · [Submission checklist](SUBMISSION_READINESS.md)
