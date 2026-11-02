# Secondary practical baseline, registered before test

Added after observing development performance, before any R2/V3 test prediction.
The original eight-model source-policy study and its training/reference signatures
remain unchanged. This is a secondary engineering comparison, not a claim that
MRZ fusion is a new invention.

For each of the eight fixed VLM outputs, apply the already implemented
`v3_cpu.fallback(fields, rapid_v4_predictions, strict=True)`. The CPU recognizer
is fixed from its completed development baseline. It receives only the same
pixel-derived rectified view. Fill missing keys only; never overwrite a VLM
value, repair OCR characters, infer a century or treat checksum as authenticity.
Names/gender/nationality require the numeric core/composite checks, but are not
individually checksum protected. No author boxes, field sets or values enter
fusion at inference. Optional MRZ data is not automatically a personal number.

Report all eight hybrid configurations and their plain counterparts. No new
VLM training or benchmark VLM generation is introduced by reprocessing cached
outputs. CPU raw OCR calls are shared with the registered CPU comparison and
this sharing is disclosed. Compare F1, omissions, wrong values, outside-contract
keys and date precision. These are additional descriptive comparisons, not a
replacement of the original paired training-policy hypothesis.

The web VLM component is always the original V3 choice made on development.
Use its fixed hybrid only if development F1 strictly improves and outside-key
count does not increase; otherwise retain plain VLM. Keep the development
deployment gate against the best registered CPU comparator. Publish and verify
the hybrid code/configuration lock together with both primary locks before test.
Do not select a VLM component, threshold, reader or merge policy using test.

If the hybrid is promoted on development, repeat it from image pixels on the
same eight-input/four-ID fresh panel twice, with new VLM and CPU calls (16
additional hybrid calls), and compare output hashes with its cached test
composition. Otherwise keep the plain VLM's existing fresh repetitions and
report zero additional hybrid fresh calls. Always replay every hybrid test
composition, including negative findings. Report freshness separately
from the existing VLM fresh repetitions and from CPU-sharing counts. Expose
field provenance on the research web and retain manual-edit provenance. No
identity/liveness approval follows from OCR or checksum. Human legibility
validation remains unperformed; the user reports no available helpers.
