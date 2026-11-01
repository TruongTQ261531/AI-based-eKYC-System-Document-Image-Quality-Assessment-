# Supplemental supervision ablation,2026-11-01, before test scoring

Motivation came from DEVELOPMENT only: originalVintern strict fieldF1=.3165,
format-tolerantF1=.5310 with high recall but many extra fields. No new test
prediction/score has been opened. Main training/source/selection remain frozen.

Add ONE conventional LoRA control to distinguish output-format adaptation from
the value of training with incomplete/occluded content. This is a supplemental
development-motivated experiment, not part of the original prespecifiedV1.
It is not evidence that the standard LoRA algorithm itself is novel.

Control uses the SAME Vintern revision, frozen vision/projector/base weights,
r8/alpha16, seed42, learning-rate schedule,192optimizer steps, four microbatches
per step, and minimum token-weighted development loss at48/96/144/192.
Train only full,corner_clip,blur_glare captures:288rasters from the SAME96train
IDs; exclude field_clip/value_mask. Its ordinary labels come unchanged from
the main corpus. It gets no test examples or labels. Development remains80
images including clipping/masking, identically to the main candidates.

Compute budget and identities match; unique raster count and number of repeated
epochs do not:768presentations/288rasters versus768/480 in main training.
Report this explicitly; do not call it a perfectly matched data-volume study.

Choose checkpoint on development, seal its SHA BEFORE any test score and
commit/push that supplemental seal together with the main pre-test choice.
Evaluate all120test images, two repeat12-image panels and the same strict/
secondary metrics. Publish per-capture slices, masked-field outputs and
grouped intervals. Use control results as an ablation; do not retroactively
change the primary main candidate or hide a winning control.

The wrapper redirects outputs and provenance in its OWN process only; it
reuses frozen training/evaluation functions without editing their source.
It holds the original GPU mutex, stores separate checkpoints/results, and
binds its code/protocol/filter to a separate signature. It runs after main
development completes and before main/control test scoring. This adds one
training run, not a broad hyperparameter search or independent camera study.
