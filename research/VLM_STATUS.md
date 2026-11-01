# Local VLM LoRA checkpoint, 2026-11-01

Research branch: research/document-recovery-core-b. Mentor and all locked V4
sources/results are unchanged. This is an additional exploratory experiment.

## Completed before weight updates

- Reviewed pinned Vintern custom model/config/conversation source. No network
  or process execution in those files; model loading will be local-only.
- Optional training libraries extracted from checksum-pinned wheels to ignored
  cache. Original Python environment is not modified; no new venv.
- New SPECIMEN corpus720rasters/144mockIDs:96train,16dev,8calibration,24test,
  fiveviews each. Generator uses two spatial arrangements/twofonts; not a new
  camera collection. Exact regeneration of all artifacts passed.
-18data/scoring tests pass. Three tinyCPU training-stack tests pass: real
  adapter-only updates, answer-only causal loss and exact optimizer resume.
  These tiny tests ARE NOT fine-tuning the actual Vintern checkpoint.
- Architecture/tokenizer probe:938193024parameters,629697920language parameters,
  256visual tokens per tile. Prefix masking checked. No checkpoint loaded there.
- Existing CPU OCR+KIE baseline completed80development images: canonical
  fieldF1=.809677,251/306correct references,7opaque-masked field outputs.
  Test scores have not been opened. No VLM accuracy is available yet.

## Active preparation

Weights3,752,849,256bytes and CUDA wheel2,716,982,502bytes are downloading in
resumable HTTP ranges. Network throughput is the current delay. Download
segments are retained across restarts, then merged and validated with upstream
SHA256. Do not call a model download an optimizer/training step.

Owned exec sessions at this checkpoint:model5388,runtime70816. Inspect their
status before restarting downloads. No actual1B GPU training has started yet.
Current code/config:VLM_LORA_PROTOCOL.md,vlm_config.json,vlm_data.py,
vlm_runtime.py,vlm_train.py,vlm_setup.py,vlm_baseline.py.

## Next actions

1. Finish model/runtime download and verifyCUDA torch works from cache.
2. Run real20-step smoke + exact10-step disk-resume comparison and measure
   memory. Native generation/cache parity is included. Preserve failures.
3. Fix only engineering issues before main training; record any amendment.
   CPU baseline checkpoints from earlier code signatures remain private and
   must be rerun/revalidated after the final training source is frozen.
4. Train seeds42/31415 for192optimizer steps; choose checkpoints by dev loss.
   Generate on development for original and both adapters. Save test lock,
   commit/push it BEFORE any test scoring.
5. Test all three models and two fresh repeat panels; replay public metrics
   from private predictions; add fresh-online timings, an honest report and
   an opt-in local demo only if development results support deployment.

Launch with existing interpreter through `python -m research.vlm_setup run --
-m research.vlm_train ...`; use absolute existing .venv interpreter if Python
on PATH differs. `research/start-vlm-training.ps1` hasPrepare/Smoke/Train/
Development/Seal/Test stages. Do not runSeal thenTest without saving the
pre-test choice inGit. Cache/weights/data must not be staged or pushed.
