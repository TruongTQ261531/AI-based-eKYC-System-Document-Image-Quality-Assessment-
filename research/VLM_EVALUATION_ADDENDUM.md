# Supplementary output-format analysis, declared before test,2026-11-01

The frozen primary parser accepts only a JSON object with scalar string/number
values. Its `valid_json` flag is a strict extraction-format success flag, NOT
pure JSON syntax validity: null/bool/nested values and fenced prose fail that
contract. Primary metrics/learning/source are unchanged.

To avoid interpreting format learning alone as improved image reading, also
score a declared secondary parser on exactly the same saved outputs:

- Optionally unwrap one entire Markdown code fence (`json` or no language).
  Never search free-form prose for guessed field/value spans.
- Parse the full remaining JSON; reject duplicate keys and non-object roots.
- Treat null and empty string values as abstentions (omit those keys).
- Retain string/number values, ignore bool/nested values but count them as
  unsupported value types. Keep field names and all observed values unchanged.
- Apply the SAME frozen canonical field scorer and physical-ID roles.

Publish strict-schema and secondary F1 side by side, plus syntactic JSON
success, dropped-null count, fenced-output count and bad-type count. No new
OCR call, model inference, value repair, ground-truth key assignment or test
tuning is introduced. The analysis is exploratory and does not change which
checkpoint is selected on development. ExistingOCR returns Python dicts by
construction; its schema success should not be mistaken for a generative
JSON formatting benchmark. No result from the new test has been opened at the
time this addendum/code was authored.
