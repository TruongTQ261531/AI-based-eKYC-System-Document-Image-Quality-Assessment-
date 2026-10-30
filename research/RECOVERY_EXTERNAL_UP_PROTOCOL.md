# Additional MIDV-UP transfer diagnostic,2026-10-31

Declared before new V4 test scoring and before any MIDV-UP model predictions.
This does not amend or replace the frozen540-case/588-execution V4 study.
The user has no newly self-captured dataset. Additional public acquisition
does not pretend to fill that missing collection with synthetic renders.

Source: author `ftp://smartengines.com/midv-up/dataset.zip`, README and
CC BY-SA2.5 license, [ICDAR2025 paper](https://doi.org/10.1007/978-3-032-04627-7_35).
The ZIP metadata lists eight photo strata: four document types, two cameras
(Samsung/iPhone),125 images each. Choose the minimum SHA256 of
`up-transfer-20261031/ENTRY_NAME`, three distinct document IDs per stratum,
excluding an ID already chosen in the other camera for the same type.
Total24 document IDs/photos; no accuracy/language-dependent image selection.

Read bounded ZIP ranges; check local headers, per-entry CRC32 and byte count.
Save source block/input/annotation hashes. Read PNG IHDR for matching template
dimensions with its chunk CRC; do not claim whole archive/template validation
when only a prefix was read. Do not upload source photos, faces or values.

Apply the already locked V4 Latin selector, fixed padded completion, and raw
image OCR, on two fresh passes with counterbalanced method order.144 actual
request units. No additional fitting, review-threshold choice, dictionary
repair or label hints. Confirm zero overlap with primary study input hashes.

Use the same spatial fully-visible Latin/alphanumeric-field exact/CER contract.
Count excluded non-Latin fields and unsupported alphabet characters explicitly;
retain all24 images in runtime/review counts, even with zero eligible fields.
Report device/type strata descriptively. Persian/Urdu transcription capability,
pretraining disjointness and semantic KIE are not established by a Latin reader.
No statistical claim from three photos/type/camera, and no threshold retuning
after this external diagnostic. Keep all outcomes including zeros/failures.
