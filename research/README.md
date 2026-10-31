# Research extension: support-preserving document crops

This directory is separate from the mentor eKYC runtime. Its branch is
`research/document-recovery-core-b`; mentor baseline is
`mentor/ekyc-v3.2.0` at `4110f22`.

Read `PROTOCOL.md` before interpreting any numbers. This is a feasibility
benchmark with no claim of guaranteed novelty, SOTA or CORE B acceptance.
No new environment or dependency is required on the original machine.

The completed2026-10-31 expansion is documented in [the V4 evidence report](RECOVERY_RESULTS_VI.md),
[manuscript draft](MANUSCRIPT_DRAFT.md), [claim boundaries](CORE_B_SUBMISSION_GATES.md)
and [resume status](STATUS.md). Earlier results remain in [REPORT_VI.md](REPORT_VI.md).
Read the V4
[locked protocol](RESEARCH_V4_PROTOCOL.md), [dataset card](DATASET_CARD_V4.md),
[pre-test evaluation clarification](RECOVERY_EVALUATION_ADDENDUM.md) and
[updated closest prior](RESEARCH_V4_RELATED_WORK.md). Main inference completed588/588;
15288 published rows were independently re-scored/replayed. The full final
regression passed162 Python + 21 frontend tests. Fresh validation includes144
online calls,24legacy cases,144MIDV-UP calls and288spatial-stress calls.
The additional440-case semantic-parser ablation reuses fixed OCR outputs;
it is not440 new OCR inferences. All negative outcomes are retained.

The separate localhost research workbench uses the original Python environment:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\research\start-research.ps1
```

Open **http://127.0.0.1:8001/** in Chrome/Edge. Mentor remains on8000.
The workbench does not invent results while the model lock is absent; camera
photos/OCR text are memory-only and are not research training inputs.
Sample buttons use authored test-configuration/extra-layout SPECIMEN cards, not a lookup
database of identities used to recognize user documents.

The deployed parser validates source/model hashes from
`results/recovery_v4/kie_deployment.json`; inference does not open training
annotations or use an identity lookup. The offline `recovery_deploy.py`
exporter binds that seal to the development lock. Camera data remains in
memory; benchmark regeneration and demo images are separate from prediction.

The development-locked spatial parser improves test key-value exact from
66.67% to76.27%, and42.19% to79.69% on the separate synthetic layout stress
set. Its main-set comparison is explicitly post hoc. It is an established
label-assignment technique, not a new learning theory. The primary learned
cascade matches completion accuracy, and completion loses to raw on the
additional layouts/MIDV-UP. New camera collection and independent legibility
annotation are absent. Do not claim guaranteed CORE B readiness, SOTA or
production eKYC/PAD security from these results.

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
