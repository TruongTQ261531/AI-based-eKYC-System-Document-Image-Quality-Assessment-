# Local multimodal fine-tuning pilot, V1, 2026-11-01

This is a new exploratory engineering/research experiment. Frozen recovery_v4
and layout_kie source, results, locks and the mentor application are untouched.
Fine-tuning an existing VLM is not itself a novel algorithm or proof of CORE B
acceptance. No new real-camera collection or human legibility labels exist.

## Model and execution

Use 5CD-AI/Vintern-1B-v3_5 at immutable revision
b98f263eab246eb5269ade64edbdca8a887dc44d. Author weights are MIT; download
3,752,849,256-byte safetensors and validate upstream SHA256. Review pinned
custom source before execution. Use only local files during training.

An optional CUDA PyTorch 2.7.1 runtime and narrowly pinned Transformers/PEFT
dependencies are extracted into ignored research/cache/vlm_lora_v1/site.
Reuse the existing Python interpreter, create no venv and do not mutate its
site-packages or the running OCR web environment. Weights/checkpoints stay
outside Git. Publish model revision, hashes, code, config and aggregate logs.

The first attempt is BF16/FP16 LoRA on the language model, with vision encoder,
projector and original language-model parameters frozen. Frozen visual feature
caching is allowed and recorded; it adds preprocessing/storage and is not
reported as online inference speed. No full fine-tuning or extra GPU rental.
6GB VRAM capacity must be measured using backward AND optimizer steps.

## Data and isolation

Create a separately named, deterministic synthetic SPECIMEN corpus with fresh
mock identities and varied Vietnamese/English names, document numbers, dates,
addresses and document families. Identity and source-image hashes are disjoint
across train/development/calibration/test and checked against prior corpora.
Train on train only, choose checkpoints on development only, lock selected
checkpoint/config before opening test predictions/scores. Published earlier
V4 test sets can only be retrospective diagnostics, never newly unseen tests.
Do not train an OCR model from Clean/Blur/Glare labels alone.

Fixed corpus: 96 train,16 development,8 calibration,24 test mock IDs, five
captures each (full,corner_clip,field_clip,blur_glare,value_mask):720 rasters.
Four generator style indices are two spatial arrangements and two fonts;
styles are shared across roles. No held-out-layout or real-camera claim.
Random field ordering, names, numbers and dates are independent of role.
Value-mask captures cover 1 to 5 values with opaque rectangles and omit them
from references. This tests withheld values, not learned real-world glare PAD.

Target is a JSON object of printed field names mapped to values. Omit fields
whose label or value is clipped; retain no inferred missing digits. A geometric
visibility rule is a synthetic proxy, not independent human legibility truth.
Use identical prompts and image processing for original and adapted VLM.

## Stages and claims

1. Unit tests for splitting, labels, masking, scoring and checkpoints.
2. Model loading and original-model output check. Training smoke run with
   actual updates; save/resume optimizer and RNG; compare resumed vs continuous.
3. Two fixed-seed training repetitions if the measured hardware budget fits.
   No hyperparameter sweep on test. Publish failures/OOM and any protocol
   amendment before dependent training/evaluation, with superseded attempts.
4. Compare original vs selected adapted model on identity-disjoint cases using
   key-value exact precision/recall/F1, JSON validity, unsupported extra output,
   missing fields and clipped-field inventions. Report fresh inference time,
   image preprocessing, RAM/VRAM, train time and repeated-panel consistency.
5. Keep web integration opt-in and fail closed to existing OCR; only deploy
   after measured development benefit. A negative fine-tuning result remains
   a negative result and does not justify silently replacing the OCR baseline.

Initial local smoke settings: LoRA r8/alpha16/dropout0, attention projections,
batch1, short output, gradient accumulation and checkpointing if required.
Choose the final feasible settings on smoke/training/development only and
record them before the test lock. Training and validation are resumable from
completed, checksummed checkpoints, not files actively being synchronized.

Final initial settings are research/vlm_config.json: two seeds42/31415,
192 optimizer steps each, four single-image microbatches per step, learning
rate2e-4, 12-step warmup and cosine decay. Evaluate token-weighted development
loss at48/96/144/192 and choose the minimum, breaking ties toward earlier.
Then evaluate generation on development and lock the deployment choice before
test. The small finite training budget is an engineering pilot, not convergence
or exhaustive hyperparameter optimization. Images are aspect-preserving padded
to896x448 and split into two448 tiles; same preprocessing for original/LoRA.
This differs from the author's default dynamic/thumbnail preprocessing and is
reported as our bounded-input setting. Cache512x896 frozen visual features;
publish actual feature setup and fresh-online times separately from cached
language-model generation. Preserve source/native generation parity checks.

Evaluation uses canonical date/gender agreement (valid dates toISO; English
sex labels toNAM/NỮ); retain literal exact counts separately for all methods.
Strict JSON object parsing rejects explanations, fenced text, duplicate keys
and nested values. Out-of-reference keys are not automatically factual
hallucinations: a value may be visible while its printed label was clipped.
Report opaque-mask field outputs separately because those values are entirely
withheld by construction. Still no independent human legibility annotation.

After the full120-image test for each of original/seed42/seed31415, rerun the
same fixed12-image panel twice: six test IDs chosen bySHA256('vlm-repeat-v1/'+ID),
full and value_mask views. These are fresh language-model inference calls on
cached vision features, not three independent120-image datasets. Separately
time a fresh image/vision/generation path; never label cached time end-to-end.

The opt-in deployment approval requires adapted developmentF1 greater than
originalVLM and at least the existingOCR baseline; no increase in masked-field
outputs relative to either comparator; JSON validity no lower than original.
This is a small-sample engineering gate, not calibrated identity assurance.

Sources: https://huggingface.co/5CD-AI/Vintern-1B-v3_5 ;
https://internvl.readthedocs.io/en/latest/internvl2.5/finetune.html ;
https://huggingface.co/docs/peft/en/developer_guides/quantization ;
https://pytorch.org/get-started/previous-versions/ .
