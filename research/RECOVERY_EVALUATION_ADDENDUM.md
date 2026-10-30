# Pre-test semantic evaluation clarification,2026-10-30

Declared while the588-case inference is running, before fitting selectors or
computing any new test score. Frozen prediction code/protocol/cache signature
remain unchanged. Primary spatial transcription exact/CER remain literal NFC,
uppercase and whitespace normalized, with no spelling/digit correction.

Source review found that the reused semantic extractor deliberately converts
dates to ISO YYYY-MM-DD and male/female to Vietnamese Nam/Nữ. Synthetic printed
references contain DD/MM/YYYY and may contain English gender words. Comparing
those strings literally penalizes a correct semantic conversion. Preserve the
frozen runner's literal semantic metric as a formatting diagnostic; add a
separately hashed canonical semantic evaluator before test release:

- Dates: parse only the existing documented formats via date_value, convert
  prediction and reference to ISO, never invent a missing/invalid value.
- Gender: the same explicit male/m/nam and female/f/nữ mapping on both sides.
- Names, IDs, addresses and other values: unchanged NFC uppercase/whitespace;
  no 0/O repair, dictionary substitution or GT-guided completion.

Eligibility and denominator are unchanged. Missing predictions remain wrong.
Report literal and canonical semantic exact separately, both only on authored
specimens with known semantic field keys. No test annotation enters fitting,
OCR inference, field naming or review-threshold selection. This is a schema
comparison correction identified from code, not an outcome-selected new target.

For selector rows the frozen runner reconstructs execution costs from measured
unique raster stages. These estimates omit selector evaluation overhead and
are not online request latency. Report fresh actual online traces separately
and keep both sets, even if the estimate is inaccurate. Do not claim that all
views were skipped during the exhaustive candidate-generation experiment.

Pre-test secondary reader ablation: on the same fixed24-case panel, additionally
run existing VietOCR on original colour predicted-line crops, compare with the
locked grayscale-crop VietOCR and EasyOCR paths. Use CRAFT predicted boxes and
0/180 confidence selection, no GT crops or language hints. Report all three
legacy alternatives, shared detector cost and source hashes. This panel-only
colour ablation cannot substitute for the full540-case reader comparison.

Also report geometric-truncation diagnostics for the fixed review decisions:
fraction of retained images containing any annotated field clipped by the
capture frame, and recall of the review flag for these images. This is a
geometric capture diagnostic, not a universal legal requirement or a claim of
human illegibility. A visible-fields-only transcription score must never be
presented as evidence that the complete identity document was verified.

Source-geometry review, before test release, also shows that a vertical field
clip can truncate every left-aligned value on an authored card. Such images
remain in latency/routing but can have zero fully-visible whole-field targets.
Therefore report a secondary **visible-reference transcription** metric on
authored cards, using their already-generated character support rectangles:
retain characters with at least.995 geometric visibility, then compare OCR
against that visible substring. Associate predictions using the visible
intersection of the field polygon; use the original field transform for line
order. Explicitly report partial-field count and number with no visible target.
Character rectangles derive from font advances/bounding boxes, not pixel masks
or human legibility labels; fully/partly readable edge glyphs can differ from
this conservative proxy. Keep the original full-string reference and report
both metrics. Do not change the locked selector training target or primary OCR
denominator in response to this diagnostic.
