# Readiness development, 16 November 2026

Scope: known-fault post-fix development and finite oracle reduction. This is not
a confirmatory study, independent human reference, or a graph-superiority result.
The plan was written before these runs, after the pilot and two fixes were known.

## Reproduce actual parser behavior without models or private data

From the repository root, with standard Python 3.10+:

```text
python -I -B research/evidence_contract/master/readiness_verify.py research/evidence_contract/execution/master_01/readiness_20261116/parser_run_01
```

The verifier runs only pinned archived programs and their exact reversions.
It checks 590 matrix outputs plus six minimal-witness outputs. It verifies
reproduction against authored requirements, not the external validity of those
requirements. Timing and the permutation curve are not independently replayed by
this minimal command. No Git history, model, GPU, private label, or image is needed.

## Re-run development experiments

Use the project Python environment and a **new** output folder:

```text
python -B -m research.evidence_contract.master.parser_faults --output research/evidence_contract/local/parser_reproduction_new
python -B -m research.evidence_contract.master.representation_audit --output research/evidence_contract/local/representation_reproduction_new
```

The parser runner requires Git commit `4110f22` and the archived application source.
The representation runner uses the existing renderer, NumPy/Pillow, frozen
contracts, and baselines. It invokes no predictor. Fonts and renderer versions
can change image hashes; recorded source states and arithmetic can still be
inspected independently. Source hash receipts identify the measured code.

## Evidence inventory

- `plan.json`: prospective run factors within post-pilot development.
- `parser_run_01/cases.json`: authored inputs and explicit requirements.
- `parser_run_01/outputs.json`: actual outputs of five parser versions.
- `parser_run_01/subjects/`: pinned old/fixed/reverted program bytes.
- `parser_run_01/results.json`: 118 cases/115 distinct inputs, two known families,
  raw timings, 500-permutation curves, and reduction traces.
- `representation_run_01/`: 255 abstract configurations and 164 injected controls,
  including eleven A/flat counterexamples. No actual-model rows are added.
- `standalone_parser_replay.log`: isolated replay receipt.
- Test/build/preservation receipts and completion manifest are added after checks.

The two historical parser defects were already fixed on 14 November. This run
adds broader isolated patch evidence, not new fixes or new independent faults.
The original A, model outputs, sealed reviews, and reviewer ZIPs are preserved.

Final checks: 260 Python tests plus 6 subtests pass; 460 protected files are
unchanged. The three-page Emerging draft was compiled with pinned Tectonic 0.17.0
and all pages inspected. Earlier layout attempts are preserved in their own logs.
The public 22-file archive is `paper/readiness_replay_20261116.zip` relative to the
Evidence Contract directory; it passed a fresh extracted replay. See
`pdf_build_receipt.json`, `package_receipt.json`, and `preservation_and_replay.json`.
