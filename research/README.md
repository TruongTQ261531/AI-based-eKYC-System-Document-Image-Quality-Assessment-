# Research extension: support-preserving document crops

This directory is separate from the mentor eKYC runtime. Its branch is
`research/document-recovery-core-b`; mentor baseline is
`mentor/ekyc-v3.2.0` at `4110f22`.

Read `PROTOCOL.md` before interpreting any numbers. This is a feasibility
benchmark with no claim of guaranteed novelty, SOTA or CORE B acceptance.
No new environment or dependency is required on the original machine.

Start with [the Vietnamese evidence report](REPORT_VI.md),
[literature/venue review](LITERATURE_REVIEW.md) and [resume status](STATUS.md).
Primary results, including failed candidates, remain unchanged. Subsequent
protocols explicitly identify their exploratory timing.

From this worktree, using the existing Python environment:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m pytest research/tests -q
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.fetch_annotations
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.benchmark --data-root D:/laptrinhcuatao/Ekyc/full_dataset_original --workers 3
```

Additional existing-environment runners (run from this worktree):

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.risk_policy
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.ocr_diagnostic --data-root D:/laptrinhcuatao/Ekyc/full_dataset_original --models-root D:/laptrinhcuatao/Ekyc/models
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.reproducibility --data-root D:/laptrinhcuatao/Ekyc/full_dataset_original
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.prepare_external_cache --include-model
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.external_midv2020
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.neural_baseline
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.partial_support
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.posthoc_controls
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.summarize_evidence
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.summarize_extensions
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.audit_evidence
```

The external acquisition and neural runners require their local author-source
cache. Raw images/annotations/weights are intentionally excluded from Git.
External archive source, bounded sampling, licence and weight SHA are recorded
in `EXTERNAL_PROTOCOL.md` and `NEURAL_BASELINE_PROTOCOL.md`. The supplementary
neural comparator is an independently implemented adapter; upstream package
numeric equivalence and its training-split provenance have not been established.

Annotation download reads only JSON entries via FTP REST from the legacy
author-published MIDV source. No downloaded executable/pickle is run and
ZIP contents are not extracted. Cache/raw annotations remain local.
The raw image dataset is read from its original directory, not copied.

Predictions are cached once with source/input hashes. Five seeds repeat
document-group calibration/test assignments; they are not five trainings.
Per-image results, all methods, split IDs, source/quality strata, runtimes
and paired physical-document bootstrap intervals are retained.
`per_image.jsonl.gz` is a deterministic compressed copy of the full raw table.

To repeat analysis without changing inference:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.benchmark --data-root D:/laptrinhcuatao/Ekyc/full_dataset_original --analyze-only --output research/results/repeat
```

The geometric baseline is the frozen **geometry-only localizer**, not the
entire eKYC system with its specialized ScanOCR detector, OCR and PAD.
Geometric/field area retention is not character recognition accuracy or
identity-verification accuracy. Keep those distinctions in any paper.
