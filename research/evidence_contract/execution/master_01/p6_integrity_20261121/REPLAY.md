# P6 · Reproduction and limitations

Baseline `6ff44ed9d7a9001e31778c2abb814e0705fb4e11`, branch main. Inputs are immutable research artifacts or local historical caches. All commands run from the repository root. Public verification needs Git history through the baseline. Private verification also requires the authorized P2 snapshot, archived study data, evaluation caches, upstream model assets and selected adapter directories. Model bytes are read only to compute digests. No OCR, model construction, training, new reviews or prospective work is part of this procedure.

~~~powershell
$py = '..\..\.venv\Scripts\python.exe'
$m = 'research.evidence_contract.execution.master_01.p6_integrity_20261121'
$b = 'research/evidence_contract/execution/master_01/p6_integrity_20261121'
& $py -X utf8 -B -m "$m.verify" $b
$out = 'research/evidence_contract/local/p6_' + [guid]::NewGuid().ToString('N')
& $py -X utf8 -B -m "$m.audit" $out
& $py -X utf8 -B -m "$m.verify" $out --private $out
& $py -X utf8 -B -m "$m.tables" "$out/aggregate.json" "$out/D4_STRATA.md"
(Get-FileHash "$out/aggregate.json").Hash -eq (Get-FileHash "$b/aggregate.json").Hash
& $py -X utf8 -B -m research.evidence_contract.oracle_reliability.verify_d4 research/evidence_contract/execution/master_01/d4_development_20261117/controls_01
& $py -X utf8 -B -m pytest -q -p no:cacheprovider research/evidence_contract/tests/test_p6_integrity.py --basetemp "$out/target"
& $py -X utf8 -B -m pytest -q -p no:cacheprovider research/evidence_contract/tests --basetemp "$out/full"
$files = (Get-ChildItem research/evidence_contract/tests/test_*.cjs).FullName
node --test --test-isolation=none @files
~~~

The generator refuses a destination outside the private local root and requires a fresh directory. It stores per-group evidence references, evaluation links, training row/slot hashes and private source provenance there. Share only the public projection and hash receipts. Published source digests are distinct from machine-dependent mtimes. For reproduction on another host, match scientific aggregates and Git blobs. The private-source receipt can change when paths or mtimes change.

The verifier independently groups the P2 rows, decodes candidate pixels, reconstructs both training epochs, checks training/evaluation checkpoint bindings, recomputes group verdicts, checks the projected arm states and reasons, and scans the release for private membership. Public verification checks the source history, P2 counts, selected checkpoints, evaluation records and frozen D4 totals; recovering private membership requires the private inputs.

The universe is the 24 P2 groups with conflicting collection roles. The 44 downstream model/split tables count reused adapters as separate evaluations. A full chronology and actual inference receipts exist for the main V4 run. Weights and hashes identify the evaluated model, not upstream pretraining membership. Probe checkpoints, other unlinked benchmarks, all template-level dependencies, and a global audit of every derived image are outside the 24-group conclusion. Equality of decoded pixels is distinct from an image declared to be derived from another source. Filesystem timestamps do not attest to data use. The D4 corpus contains constructed truth and unadjudicated archived outputs. No real-world missed-fault count can be recovered from those artifacts.
