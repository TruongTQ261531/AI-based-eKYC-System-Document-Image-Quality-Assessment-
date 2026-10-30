# Research checkpoint, 2026-10-28

## Active follow-up, 2026-10-30

Prediction-only end-to-end OCR has been implemented separately and launched.
Read E2E_OCR_PROTOCOL.md and E2E_OCR_PROVENANCE.md. Protocol/code initially
locked in8819841; runtime-only161/32/32 schedule amended in8cef538 before
accuracy inspection. Six original engineering pilot images are retained
separately under e2e_ocr_v1, excluded from main results.

Final schedule: all161 images once (91 three-corner,50 controls,20 external),
then32 fixed distinct-ID cases repeated twice with fresh OCR. Six policies,
CRAFT predicted text regions, EasyOCR English and existing VietOCR. GT is used
only for post-inference spatial field-transcription scoring. Not semantic KIE.
Do not claim three full161-image runs. No new dependencies or weights.

Resume after interruption using the existing environment from this worktree:

```powershell
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_progress
D:\laptrinhcuatao\Ekyc\.venv\Scripts\python.exe -m research.e2e_benchmark
```

The benchmark verifies its signature and skips only completed atomic image
checkpoints within the same scheduled pass. Different passes never share OCR
predictions. Do not edit e2e_data/eval/pipeline/benchmark or the protocol while
this experiment is running; that intentionally invalidates its cache signature.
Private text checkpoints are Git-ignored at research/cache/e2e_ocr_v2.
After completion run e2e_analysis and e2e_alphabet_audit, inspect all policies,
write the Vietnamese results report, run regression tests, update this status
and push the research branch. Do not overwrite earlier negative studies.

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
2. Benchmark actual OCR/KIE, crop bounding boxes and wall latency for support,
   full-frame and padded-parallelogram at comparable error/coverage. Confidence
   is not ground truth; use annotated character/field accuracy.
3. Expand external identities and capture conditions with a new locked protocol.
   Keep unseen identity versus unseen template claims separate.
4. Reassess closest prior on incomplete-boundary rectification and line-based
   corner completion before drafting novelty claims. Read REPORT_VI.md and
   PAPER_OUTLINE.md; no restart of completed cached inference is needed.

All launched experiment processes completed before this checkpoint. The local
mentor server was not listening at the latest read-only health check; this
research did not restart or change it. Tests do not substitute for a live
camera/security deployment assessment.
