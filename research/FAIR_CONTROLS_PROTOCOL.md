# Priority4: prospective matched controls after the completed hard-pair study

The previous hard-pair test has been opened and its results are known. This
study therefore uses fresh test identities and never calls that old test a new
confirmation. It evaluates ablations, not a newly tuned algorithm or a claim of
CORE B acceptance. Old V1/V4/R2/V3/HP artifacts are preserved by hashes.

## Four fixed arms, two fixed seeds

Reuse the frozen uniform-source V3 and hard-pair adapters at final320 for seeds
42/31415. Train random and repeat adapters from the same pinned Vintern base.
All arms retain128 training identities,640 ordered slots,320 AdamW updates,
accumulation4 and1280 presentations; r8/alpha16, target modules, prompt, rect2,
optimizer, answer-only per-image CE and final checkpoint remain fixed. Never
warm-start a new arm from another adapter. Four new runs and four reused runs
are reported separately.

Random uses the same eligible all-source A/B masking and development-derived
key-frequency prior as hard, but selects32 IDs by seeded random sampling.
Match the hard arm's source/layout stratum counts. Enumerate all stratified
subsets, with a cap of1000000 distinct combinations, and retain those with
exactly the same aggregate answer-loss token exposure as hard. Among those,
maximize the number of IDs outside the hard selected set; choose uniformly by
seeded reservoir sampling (seed20261105) among all maximal-contrast subsets.
Require at least4 changed IDs and stop if infeasible. This is conditional
random sampling, not unconstrained uniform sampling. Identity overlap, full
enumeration counts and all conditioning variables are reported. This limited support bounds the strength
of the mining contrast; it is not a broad random32-versus-hard32 population
comparison. An unpublished initial preparation with four different IDs and a
failed1000000-draw attempt to attain the six-ID geometric bound are preserved
locally with hashes and a pre-optimizer revision reason. Exact enumeration
determines the joint stratum/token support bound, rather than silently relaxing
the token budget or presenting repeated draws as model trials. New-test
outputs are never used.

Repeat uses exactly the hard arm's32 IDs and two slots. For each ID repeat
either mask A or mask B in both slots, instead of presenting both orientations.
A deterministic hash-ordered dynamic program chooses16 A/16 B identities with
exactly the same total answer-loss tokens as hard; stop before training if
infeasible. Repeated pixels are intentional and not independent images.
The loss has no explicit pair coupling. This contrast tests opposite-view
diversity, not removal of a nonexistent pair loss; per-key/per-step exposure
can still differ and is reported.

Primary hard/random/repeat have matched aggregate answer tokens as well as
ID/slot/update exposure. Uniform is a secondary whole-intervention comparator:
its historical token exposure differs. Equal total tokens do not imply equal
FLOPs or time because sequence-length distributions differ. Historical training
allocator conditions also differ; no training-speed superiority is claimed.

## Inputs, development and genuinely new test

Use the existing96 development views/24 identities without tuning any new
hyperparameter. Reuse old uniform/hard development outputs only when inference
host threads remain2 and every input/prompt/model hash matches; score them again
and mark reuse. New random/repeat development outputs are actual generation.
No candidate is selected for deployment in this ablation study.

Fresh test: author MIDV TAR members16/17 per document type and member18 for
four types ranked by SHA256('fc1-extra/'+type),24 photos total;24 new authored
identities from the unchanged HP generator at indices1000..1023, with its
Calibri/Cambria layouts. Four views per identity: full, field_clip, value_mask,
pair_mask;192 views/48 identities shared by all eight adapters. Pair eligibility
uses geometry only, never model outputs. Retain fallback value masks and exact
raster duplicates; count them. There is no new-layout/font/camera-population
claim. Check all prior role IDs, encoded and decoded pixel hashes and full-answer
fingerprints for overlap before training. No expected keys/boxes/values are
passed at inference.

Keep the old, bounded source-reference scorer. Before new test inference,
publish an annotation-only inventory of photos with declared MRZ text but no
recognized TD3 source. Primary evaluation retains all192 cases. A predeclared
coverage sensitivity excludes exactly those inventoried IDs, retains the same
outputs, and reports both results. It does not repair transcripts or prove
missing-source outputs are hallucination. Legibility remains a geometric proxy;
there are no independent human labels or newly collected consented photos.

## Comparisons and uncertainty

Primary comparisons: hard-random and hard-repeat, paired separately at each of
the two seeds (four comparisons). Primary measure is all-view micro key/value
F1. Report ordinary95% and Bonferroni98.75% percentile CIs from10000 paired
source-stratified ID-cluster bootstrap resamples, seed20261106. Views and fields
of one ID are never independent resampling units. Also report a sensitivity
joining ID components connected by identical test rasters.

For each primary contrast use10000 document-level paired label-swap
permutations (all views swapped together; seed20261107), two-sided absolute F1
statistic and (extreme+1)/(10000+1). Holm adjustment covers the four primary
p-values. The exchangeability assumption and the small two-seed sample remain
limitations; no seed-population guarantee is inferred. Hard-uniform and source,
view, device, hidden-output, neighbor-omission/wrong/recall, JSON, token-limit
and pair-success analyses are secondary/descriptive. Do not pick a winning
test subset or promote a model based on test.

## Runtime, publication, audit and recovery

An exploratory four-input development probe compares host threads2/1 using the
frozen uniform42 adapter, two24-token warmups and eight384-token calls. Choose1
only if all generated token IDs match and its median is lower; otherwise2.
Save both timings, hashes and scope before training. Training stays at2 threads.
Apply the chosen inference runtime to all arms. The probe does not establish
global numerical equivalence. Use the existing CUDA overlay and weights, child
allocator garbage_collection_threshold:0.6, no new venv or bulk installation.

Publish code, data hashes, selections, preflight and this protocol before the
first new optimizer update. Publish a second seal binding all eight adapter
hashes, data, runtime and analysis plan before any new test prediction. Each
raw generation and checkpoint is saved, with headers validated on resume.
Do not delete incompatible or failed artifacts; report interruptions and
discarded/replayed updates separately from effective320.

Replay all2304 score rows (8 models times96 dev+192 test), including any reused
development rows. Verify all final optimizer steps/cursors/tensors and old
checkpoint hashes, ID/slot order, source-mask targets, token counts and fresh
feature parity for all distinct inputs. Freshly read from pixel a fixed panel
of4 test inputs (one hash-selected ID per source, full/pair_mask), twice per
model:64 calls, compare hashes even on negative outcomes. Report timing scope,
resource counters and every mismatch; bootstrap/rescoring are not model calls.

Only numeric artifacts/hashes and code are published. Data, OCR values and
weights stay local. A durable supervisor serializes GPU work, prevents system
sleep, releases only the existing research8003 service and restores it in
finally. Mentor8000 stays unchanged. Restore the previously selected partial42
web model; this protocol does not authorize replacing it with a test winner.
