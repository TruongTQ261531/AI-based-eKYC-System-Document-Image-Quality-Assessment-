# Frozen neural comparator: supplementary, before neural outcomes

2026-10-28, after v1/v2, before DocAligner inference. This is exploratory.

Use author-released DocAligner 1.1.1 FastViT-SA24 heatmap model, SHA256
`7f9f5a8935b2eb22b3ee0245d34996063f54562df390d34714af2d76928695bc`,
83,084,930 bytes, Apache-2.0 as listed on the author's model page:
https://docsaid.org/fr/models/docaligner . Upstream reference implementation:
https://github.com/DocsaidLab/DocAligner/blob/main/docaligner/heatmap_reg/infer.py .

Use existing ONNX Runtime CPU, no new packages. A small independent adapter
matches documented preprocessing/postprocessing: BGR input, bilinear 256x256,
NCHW float32 /255, each heatmap resized to source dimensions, threshold .3,
uint8 conversion, Otsu, largest external contour, contour mass centroid.
No center crop. Reject nonfinite/nonconvex/degenerate quads and retain full-frame
review fallback. Verify model hash, IO names and output shape before scoring.
Record that numeric cross-check against the installed upstream package is not
available; do not call a reimplementation bit-identical without that evidence.

Select only primary frame15 from every clip: expected 700 frames, all 50 IDs
and both sources. This reduces expensive source-size heatmap postprocessing.
Use the original five whole-ID test splits, 420 frames per split. Compare
against original single/adaptive predictions on exactly these same frames.
Report the neural quad and the neural quad with a fixed 5%-sqrt-area margin;
no new neural tuning or calibration. Include the 20 external identities once
their acquisition completes; transfer no GT to inference.

Save every scored row, source/input/model/adapter hashes, wall time and
localization failures. These pretrained weights may have seen MIDV-related
training data; training split provenance is not independently established.
This is an existing neural-system comparator, **not** evidence of leakage-free
SOTA, novel learning or pristine unseen-template generalization. Do not tune
thresholds/margins after inspecting its results.
