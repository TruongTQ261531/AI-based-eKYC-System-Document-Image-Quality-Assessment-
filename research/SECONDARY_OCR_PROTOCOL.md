# Secondary OCR harm diagnostic

Added while primary prediction extraction is running, before inspecting any
benchmark outcome. This is an explicitly secondary/exploratory diagnostic,
not a retroactive change to the primary geometry protocol.

- First seed's 30 held-out physical IDs only; both MIDV sources.
- For each ID/source, choose one deterministic fully visible annotated Latin
  text field, length 4..64, with a minimum source-side span of 5 pixels.
  Sort eligibility by a fixed SHA256 of frame/field key, never by method/OCR outcome.
- Use annotated source field quadrilaterals only to isolate the effect of
  cropping, with the same oracle field normalization for every method.
  Mask source pixels outside each predicted support region, then recognize
  the resulting field. The unmasked oracle field is a diagnostic upper
  reference, not a competitive end-to-end baseline.
- Evaluate all nine primary methods with two frozen local readers: EasyOCR
  English and VietOCR. Uppercase NFC, collapse whitespace; no 0/O repair,
  dictionary lookup or post-correction. CER can exceed one.
- Save edit counts, true/predicted lengths, keys and confidence only; do not
  publish source/recognized personal text strings or images.
- Report per-field CER/exact match and paired physical-ID bootstrap for
  crop-induced error differences. Field crops are oracle-controlled, so these
  numbers must never be described as end-to-end card OCR/KIE accuracy.
- A narrow Latin subset and two OCR readers do not establish performance on
  all languages, live Vietnamese CCCD, face matching or spoofing.
