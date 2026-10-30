# Research extension: support-preserving document crops

This directory is separate from the mentor eKYC runtime. Its branch is
`research/document-recovery-core-b`; mentor baseline is
`mentor/ekyc-v3.2.0` at `4110f22`.

Read `PROTOCOL.md` before interpreting any numbers. This is a feasibility
benchmark with no claim of guaranteed novelty, SOTA or CORE B acceptance.
No new environment or dependency is required on the original machine.

Start with [the Vietnamese evidence report](REPORT_VI.md),
[literature/venue review](LITERATURE_REVIEW.md) and [resume status](STATUS.md).
The V4 expansion requested on2026-10-30 is tracked in STATUS.md. Read its
[locked protocol](RESEARCH_V4_PROTOCOL.md), [dataset card](DATASET_CARD_V4.md),
[pre-test evaluation clarification](RECOVERY_EVALUATION_ADDENDUM.md) and
[updated closest prior](RESEARCH_V4_RELATED_WORK.md). Do not mistake a running
experiment for a completed result. Its final generated reports are
RECOVERY_RESULTS_VI.md and MANUSCRIPT_DRAFT.md once all validation finishes.

The separate localhost research workbench uses the original Python environment:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\research\start-research.ps1
```

Open **http://127.0.0.1:8001/** in Chrome/Edge. Mentor remains on8000.
The workbench does not invent results while the model lock is absent; camera
photos/OCR text are memory-only and are not research training inputs.
Sample buttons use newly authored held-out-layout SPECIMEN cards, not a lookup
database of identities used to recognize user documents.

On a new machine with the required packages already available, the V4 asset
and data cache can be rebuilt with `python -m research.recovery_setup --data`.
The script downloads bounded author sources/pinned assets without pip or venv
creation. Optional legacy-reader checks additionally require the existing
EasyOCR/VietOCR files; set EKYC_MODELS_DIR to their model root if necessary.
Do not run acquisition/generation over an active experiment's immutable data.
Primary results, including failed candidates, remain unchanged. Subsequent
protocols explicitly identify their exploratory timing.

The completed2026-10-30 follow-up is [end-to-end OCR evidence](E2E_RESULTS_VI.md):
161 distinct images plus two fresh32-image panel repetitions,225 image
executions,2700 result rows, and independent checkpoint/publication re-scoring.
Support improves over raw but loses to the simple padded-parallelogram control
in descriptive three-corner accuracy and latency; this is not a superiority
or submission-readiness claim. No mentor runtime changes were made.

Inspect progress before resuming a stopped chat; a usage interruption does not
necessarily stop its Python process. Never launch a duplicate invocation.
After all225 checkpoints exist, reproduce the analysis/audit/report with:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_progress
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_analysis
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_alphabet_audit
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.audit_e2e
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_report
```

These commands do not re-run OCR. Raw text predictions stay in the local
Git-ignored cache; published artifacts contain numeric metrics/hashes only.

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
