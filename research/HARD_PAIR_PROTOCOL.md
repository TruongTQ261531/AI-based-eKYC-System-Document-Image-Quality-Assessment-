# Paired evidence masks: registered intervention after the completed R2/V3 study

This study responds to development errors in which partial training suppresses
unsupported keys but still omits whole neighboring body fields. Previous R2/V3
test results are already known. The present method and all hyperparameters are
therefore new hypotheses; previous tests will not be reused as confirmation.
No first-invention or CORE B acceptance claim is made.

## Training intervention

Use the exact previously inventoried32 train document instances, selected by
train geometry and development-only error-key frequencies.29 are photographed
mock IDs and3 are authored specimens. No development identity enters training.
For each eligible identity choose two nearby, originally supported keys A/B,
ranked by those development error frequencies, then distance and stable ID hash.
Nearby means a body-region bounding-box gap at most8% of the image diagonal.
Require a whole body realization of the retained key after masking.

Replace only that identity's slot3/4 with opposite full-frame masks: hide all
declared evidence realizations of A while retaining B; then hide all declared
realizations of B while retaining A. Masks use the same dark color and1.04 polygon
expansion as the earlier value-mask generator. A body/MRZ duplicate is not treated
as absent while an associated alternative survives. Unusable pairs are retained
as original training slots and counted; never silently drop an identity.
This is a geometric evidence proxy, not independently verified human legibility.

Keep128 document instances,640 ordered slots, two epochs/1280 presentations,
320 AdamW updates, accumulation4, seeds42/31415, LoRA r8/alpha16 and final320
checkpoints, identical to the source-supervised V3 controls. All unchanged slots
and ID/slot sampling orders must match. Every new run starts from the same pinned
Vintern base, not from the control adapter. Input rect2, optional17-key prompt,
384-token generation budget, vision/projector freeze and optimizer stay fixed.
The two existing source-supervised V3 adapters are the matched uniform controls.
This design tests the whole selected-pair intervention; it does not isolate
hard selection from generic paired augmentation. Actual loss-token exposure,
changed slots, duration, allocated/reserved memory and interruptions are reported.

## Development, test and selection

Development keeps the prior72 inputs from24 identities and adds one pair-mask
input per identity when possible; fallback retains a standard value-mask image
and is flagged. The old development has already informed error-type selection,
so only the new test is confirmatory for this intervention. No old test output
is read for hard-case selection, tuning, early stopping or promotion.

New test:24 author MIDV photographs from TAR members13/14 per type plus member15
for four types selected by SHA256('hard-pair-v1-extra/'+type), and24 new fictional
IDs rendered in Calibri/Cambria with two new layouts. Source IDs/raster hashes and
complete key-value fingerprints must not overlap any prior train/development/test.
Report actual camera EXIF and font hashes; this is not a newly collected camera
population, independently verified natural-person split, or unknown-pretraining
guarantee. Preserve original author license/portrait attribution.

Development/test pair choice uses geometry and stable ties only, without error
frequencies or model outputs. Each new test identity has full, field_clip, ordinary value_mask and pair_mask
views,192 cases total. Failed pair eligibility uses a flagged ordinary-mask
fallback rather than dropping difficult cases. Primary all-view micro KV F1 is
paired by seed (hard42-uniform42; hard31415-uniform31415). Also report regular
views, pair-mask subset, source/type/device/view slices, declared-hidden outputs,
whole-body-neighbor recall/omissions/wrong values, date precision and JSON errors.
Paired ID-cluster percentile bootstrap:10000 resamples, seed20261104, stratify
24 authored/24 photographs. Individual fields/views are not independent IDs.
Within-test exact raster duplicates are retained and counted. Also report a
predeclared bootstrap sensitivity that joins document IDs connected by any
identical raster before resampling source-stratified connected components.

Development chooses an optional hard candidate by F1, then fewer unsupported
outputs, then seed number. Promotion requires higher development F1 than both
uniform controls and no more unsupported outputs or whole-neighbor omissions
than either. Test never changes this decision. A failed gate keeps the existing
web model. Do not run inference with reference values/boxes or expected keys.

Publish this code/protocol/data hash before training. Before any test inference,
publish a second seal binding all four adapter hashes, dataset hash, prompt/input
and development decision. Raw predictions/labels/photos/weights stay local;
public artifacts contain counts/hashes only. Retain every error, OOM and negative
outcome. Resume complete checkpoints; do not overwrite incompatible caches.

## Verification and runtime

Replay all new raw predictions with the same scorer, verify source-mask target
construction, optimizer steps/LoRA tensors, input/slot matching and every feature
cache hash. Freshly re-extract features for changed training and new eval images;
reuse unchanged old features only with identical input/preprocessing hashes.
Repeat pixel-level inference twice on a hash-selected8-input/4-ID test panel for
the development-selected hard candidate, even if the web promotion gate fails;
keep all hash differences. Cached generation timing and fresh end-to-end latency
are separate. CPU SOTA superiority and certified identity/PAD are outside scope.

Use existing optional CUDA runtime and weights, no new venv or bulk install.
Temporarily release only the research OCR GPU server while training, then restore
it. Supervisor states, stdout, events and checkpoints are saved continuously.
