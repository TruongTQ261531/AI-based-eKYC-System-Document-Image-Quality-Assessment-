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
