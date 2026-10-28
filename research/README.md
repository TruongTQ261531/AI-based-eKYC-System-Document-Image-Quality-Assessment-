# Research extension: support-preserving document crops

This directory is separate from the mentor eKYC runtime. Its branch is
`research/document-recovery-core-b`; mentor baseline is
`mentor/ekyc-v3.2.0` at `4110f22`.

Read `PROTOCOL.md` before interpreting any numbers. This is a feasibility
benchmark with no claim of guaranteed novelty, SOTA or CORE B acceptance.
No new environment or dependency is required on the original machine.

From this worktree, using the existing Python environment:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m pytest research/tests -q
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.fetch_annotations
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.benchmark --data-root D:/laptrinhcuatao/Ekyc/full_dataset_original --workers 3
```

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
