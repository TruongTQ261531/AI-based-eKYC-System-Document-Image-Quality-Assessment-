# Research checkpoints (active V4 expansion:2026-10-30)

## Active V4 expansion requested after e7e4602

Read RESEARCH_V4_PROTOCOL.md first. Core study locked/pushed in6e871cc.
540 images/150 identities:360 newly authored SPECIMEN captures from90 IDs,
180 derivatives of60 additional MIDV photo IDs. Disjoint roles40 development,
30 calibration,80 test IDs. Two reader architectures (Rapid PP-OCRv4 and Latin
PP-OCRv5), two localizer architectures (FastViT-SA24 and LCNet100), seven views,
ridge/stump selector alternatives and budgeted actual online cascade.

Inference currently running with588 scheduled executions:540 plus two fresh
24-image panels. Private checkpoints at research/cache/recovery_v4/pass1..3.
Test scores are not computed by inference. Only after inference run fit,
commit selector_models/selector_lock, and then evaluate. Never edit protocol
or recovery_assets/acquire/data/runtime/upstream/selection/study while this
run is active: code/input/model hashes invalidate cache on changes.
The process lock prevents simultaneous invocations. Inspect current OS process
and checkpoint count before attempting resume after usage interruption.

After infer exits0, run fit twice BEFORE opening test scores and verify the
model/threshold JSON bytes match. Save fit_repeat.json; deterministic refitting
does not add independent data. Commit/push selector_models.json and selector_lock
before evaluate. Frozen inference has no test scores; keep that guarantee.

Remaining commands from this worktree, using the original environment:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_study infer
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_study fit
# Commit the numeric selector lock before viewing test scores.
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_study evaluate
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_analysis
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_validate online
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_validate legacy
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_audit
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_release
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.recovery_report
```

Do not re-launch infer while its original process is still running. Planned
follow-up: independent rescoring/publication audit, physical-ID bootstrap,
24-case legacy OCR check, fresh actual-online timing/output checks, localhost
web validation, regression tests and a transparent updated paper decision.
Local web implemented separately in research/recovery_web.py and research/web;
launcher research/start-research.ps1 uses port8001, mentor8000 stays untouched.
Web must not emit invented fields/results while selector lock is unavailable.
Current research web source was updated after its initial server startup;
restart only the owned research server8001 after models/audit are ready, then
verify held-out full/student/licence demos through the browser. No physical
camera-motion test has been performed. Save and embed an actual UI screenshot.
The pre-test RECOVERY_EVALUATION_ADDENDUM.md preserves literal OCR metrics,
adds canonical date/gender KIE and conservative visible-substring metrics,
and discloses trace-estimated selector cost versus actual online timings.
Do not modify the locked predictor to implement these analysis-only additions.
Camera inputs remain memory-only. User explicitly chose localhost, not public
deployment. No venv/site-packages changes; optional official code/models live
in Git-ignored cache. Eight source-level adapter/native OCR parity checks pass;
this is not an entire upstream-package installation/every-path test.

Upstream training exposure is now positively documented: author pages mention
MIDV500/2019 and training examples in the MIDV2020 demo. Do not label new MIDV
study IDs unseen-pretraining. New SPECIMEN identities/layouts provide separately
authored data, but no new real-world camera collection has been performed.

User explicitly answered that no additional self-captured research-permitted
images are available. MIDV-UP public-source acquisition is an additional
bounded transfer diagnostic, declared separately before any test result:
RECOVERY_EXTERNAL_UP_PROTOCOL.md; recovery_up_external acquire/run.24 photos,
four new-to-selector template types,two camera strata,three fixed methods,
two fresh passes(144 online units). This is not a new self-captured collection
and does not prove unseen pretraining or Urdu/Persian capability. After the
primary model lock run the external check, audit it and report every result.
Do not let this supplement alter primary540-case fitting/metrics/thresholds.

---

## Completed end-to-end OCR follow-up, 2026-10-30

Prediction-only end-to-end OCR completed with exit0 after13459.884 seconds
(224.33 minutes),225/225 image executions,2700 public rows. Nothing remains
running in this OCR study. Read [E2E_RESULTS_VI.md](E2E_RESULTS_VI.md).
Read E2E_OCR_PROTOCOL.md and E2E_OCR_PROVENANCE.md. Protocol/code initially
locked in8819841; runtime-only161/32/32 schedule amended in8cef538 before
accuracy inspection. Six original engineering pilot images are retained
separately under e2e_ocr_v1, excluded from main results.

Final schedule: all161 images once (91 three-corner,50 controls,20 external),
then32 fixed distinct-ID cases repeated twice with fresh OCR. Six policies,
CRAFT predicted text regions, EasyOCR English and existing VietOCR. GT is used
only for post-inference spatial field-transcription scoring. Not semantic KIE.
Do not claim three full161-image runs. No new dependencies or weights.

Audit:225 private checkpoints re-scored;2700 public rows match private numeric
projections;144 summary rows re-aggregated; zero score/timing/hash mismatches
and zero failure events.32-image repeat panel:384 image-policy-reader groups,
zero canonical prediction or field-score mismatches across three fresh passes.
225 actual localizer calls,731 unique within-image/pass OCR rasters; this is
not2700 independent inferences. All tests passed:134 Python and15 frontend.
One pre-existing dependency deprecation warning; no packages were changed.

Main finding on91 neural-three-corner images (VietOCR): raw22.09%, support
27.69%, expanded parallelogram32.64% pooled field exact; mean wall time
14.78/16.25/12.76 seconds/image. Masking adds no pooled exact over bbox.
English has the same descriptive ordering. Support-vs-parallelogram VietOCR
ID-level accuracy CI includes zero, so do not claim universal statistical
superiority. This removes the missing OCR measurement, but does not establish
a novel superior support-mask algorithm or CORE B submission readiness.
Final source/data/model signature:
31c00e69dad9ee35916e692ee7d17e4691b827caa48936f50db6a0d9a6ef62d1.

After a chat/usage interruption, inspect the OS process and progress first:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match '\s-m\s+research\.e2e_benchmark(?:\s|$)' } | Select-Object ProcessId,ParentProcessId
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_progress
```

**Do not start another benchmark while the original process is running.**
Windows can show the venv launcher and its child interpreter for one invocation.
Only when an invocation has stopped with missing checkpoints, resume from this
worktree. This study already has all225, so no OCR rerun is currently needed:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_benchmark
```

The benchmark verifies its signature and skips only completed atomic image
checkpoints within the same scheduled pass. Different passes never share OCR
predictions. Do not edit e2e_data/eval/pipeline/benchmark or the protocol while
this experiment is running; that intentionally invalidates its cache signature.
Private text checkpoints are Git-ignored at research/cache/e2e_ocr_v2.
Analysis, alphabet audit, independent audit, plots and Vietnamese report are
complete. See research/README.md for analysis-only commands. Do not overwrite
earlier negative studies or retune on these exposed test identities.

---

User target: **CORE B conference**, separate from the mentor assignment.
Current conclusion: substantial reproducible feasibility evidence exists,
but **submission readiness and sufficient novelty are not established**.

## Durable state

- Mentor branch: `mentor/ekyc-v3.2.0`, `4110f22b94699d30950cd1c0b23532ee9ccaaa59`.
- Research branch: `research/document-recovery-core-b`.
- Worktree: `D:/laptrinhcuatao/Ekyc/versions/research-document-recovery`.
- Original data: `D:/laptrinhcuatao/Ekyc/full_dataset_original`.
- Existing Python: `D:/laptrinhcuatao/Ekyc/.venv/Scripts/python.exe`.
- No mentor runtime file changed, no venv/dependency installation.
- Raw data/model/cache are local and Git-ignored. Numeric rows/plots are tracked.

## Completed experiments; do not start them over unnecessarily

1. Original author annotations: 21,000 frame records, 100 references; primary
   deterministic sample 3,500 frames, 50 physical documents.
2. V1: nine policies, five 20/30 whole-ID splits, all rows saved. Conformal
   worst-frame containment degenerates to huge crops/no automatic cases.
3. V2: eight document-risk policies, 105,000 monotonicity checks, five splits.
   Adaptive CRC cap reduces harmful auto decisions but loses utility/coverage.
4. OCR diagnostic: 58 oracle fields, 29 physical IDs, two readers, 1,160 rows.
   This is crop-induced harm measurement, not end-to-end OCR accuracy.
5. Reproducibility: repeated analysis byte-identical; 100 images genuinely
   inferred again, 300 localizer calls, all input/prediction hashes match.
6. MIDV-2020: 20 new physical IDs, ten overlapping template types, photo05/59.
   EXIF evaluation bug corrected without changing IDs; invalid rows retained
   and explicitly excluded. CRC does not establish external risk control.
7. Neural comparator: pinned DocAligner FastViT-SA24, 700 same-frame primary
   images plus 20 external. Stronger than the old geometry-only localizer.
8. V3: exactly-three-corner support rescue, 203 failures decoded again; 92
   three-corner cases. Support raises routing coverage but not geometric
   accepted utility appreciably; full-frame routing has the same coverage.
9. Post-hoc full-frame and padded-parallelogram controls: all results retained;
   parallelogram+5% has higher utility with some additional field harm.
10. End-to-end predicted-region OCR on161 images with32-image fresh replication
    twice:225 image runs,2700 rows, both readers, clustered intervals, confidence
    review curves, independent re-scoring and publication audit. Simple padded
    completion beats support descriptively; no unique mask advantage established.

Protocol commits: v1 `3e3c781`, secondary OCR `a808d77`, v2 `ccfdac1`,
external `7bb5133`, neural `716935c`, EXIF correction `d9512b1`, v3 `4c134a4`.
Later code/analysis checks are in the research Git history and audit manifest.

## Conclusions to preserve

- Do not claim novel conformal theory, a world-first missing-corner method,
  SOTA, guaranteed CORE B acceptance, verified PAD, or zero deployment risk.
- The three deterministic views and neighbouring video frames are correlated.
- Five overlapping ID splits are not five independent trainings/test sets.
- 3,500/700/20-image tables have different scopes; compare matching images.
- Upstream neural training split and adapter numeric equivalence are unresolved.
- Partial support is a visible-content region, not a complete rectified card
  and not authorization to accept incomplete ID documents in the mentor flow.
- Full-frame control shows that extra routing coverage alone is not novelty.

## Next work that would materially improve a paper

1. Validate the adapter against the upstream package and audit pretrained-data
   provenance; keep model/code pinned. Add another strong localizer.
2. Use the now-completed OCR benchmark to characterize failures of padded
   completion. Any new selector/refinement needs separate development IDs and
   fresh locked evaluation; preserve full-frame/bbox/completion controls.
   Semantic KIE is still unmeasured. Confidence is not ground truth.
3. Expand external identities and capture conditions with a new locked protocol.
   Keep unseen identity versus unseen template claims separate.
4. Reassess closest prior on incomplete-boundary rectification and line-based
   corner completion before drafting novelty claims. Read REPORT_VI.md and
   PAPER_OUTLINE.md; no restart of completed cached inference is needed.

At the historical 2026-10-28 checkpoint, all then-launched experiments had
completed. The2026-10-30 OCR follow-up at the top of this file is now complete
as well. The local
mentor server was not listening at the latest read-only health check; this
research did not restart or change it. Tests do not substitute for a live
camera/security deployment assessment.
