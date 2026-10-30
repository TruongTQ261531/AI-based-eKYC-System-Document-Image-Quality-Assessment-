# Exploratory layout-aware KIE ablation,2026-10-31

Motivation follows release of the primary V4 aggregate results: Latin
completion has80% spatial field exact but66.667% canonical semantic exact on
authored test cards. Preserve V4 and its frozen extractor/results. This new
extractor is an exploratory application improvement, not the prespecified
V4 primary method or a claim that label-value assignment is a new algorithm.

Use printed-label aliases from the existing mentor parser and its public
field labels, and geometric right/below relations between predicted OCR
boxes. Match unique candidate values to labels with rectangular assignment;
support unknown explicit colon labels as editable extra fields. No expected
value, family-specific required-field list, GT box or dataset ID enters
prediction. Reuse existing date/gender/value validation. Do not infer text
missing from the image.

Debug on development-role authored OCR only; lock source before evaluating
the primary test labels or the additional spatial-layout outcomes with this
extractor. Primary V4 test results have already been seen in aggregate, so
all main-set comparisons here are post hoc. The separate80-image stress
set's baseline outcomes have not been inspected when this protocol is written;
two examples were visually reviewed for generator geometry. Do not call it a
newly collected or entirely unseen design distribution.

Compare original versus spatial parsing on identical Latin completion OCR
predictions:360 authored primary cases, then80 spatial stress cases, first
passes only. Reconstruct the prediction-only completion coordinate frame
using the same frozen localizer. Do not execute additional OCR or pass
annotation crops into the extractor. Report literal/canonical key-value exact,
missing/incorrect key-value counts and actual parser/coordinate setup CPU/wall
cost separately from OCR. Repeated parser evaluations on the same predictions
check determinism, not independent OCR inference. Keep all negative changes
and source/split breakdowns. Public output contains numeric scores and hashes;
text/values remain in ignored caches. Independent audit rescoring is required.

Only after a development-only implementation lock may the localhost research
workbench use this parser as an explicitly labelled alternative. Preserve the
original mentor runtime and all V4 prediction/selector signatures. Existing
SciPy is available; no installation or new environment. This ablation cannot
by itself establish CORE B novelty or new-camera validity.

Deployment selection uses development canonical key-value correctness only:
enable spatial parsing if its total correct count is at least the original
parser's on the same development OCR and relevant unit tests pass. Otherwise
retain the original parser and report the failed alternative. Do not change
this decision based on test/stress outcomes.
