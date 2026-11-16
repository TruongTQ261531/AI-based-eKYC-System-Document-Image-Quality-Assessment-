# Sources and corpus feasibility checked on 16 November 2026

Primary sources below inform implementation or proposals; they do not supply new
project evaluation results. No new image corpus was downloaded or selected.

| Source | Verified fact and use | Limit |
|---|---|---|
| [ICAO catalog](https://www.icao.int/publications/doc-series/doc-9303), [Part 3](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p3_cons_en.pdf), [Part 4](https://www.icao.int/sites/default/files/publications/DocSeries/9303_p4_cons_en.pdf) | Part 3 date/check-digit rules; Part 4 TD3 field/check-digit positions. Used to recalculate checks from literals and preserve date precision | Implemented subset only; names not validated by the selected check digits; no authenticity claim |
| [SelectiveNet, ICML 2019](https://proceedings.mlr.press/v97/geifman19a.html) | Selective prediction motivates reporting risk with coverage | No SelectiveNet training/implementation and no calibrated confidence curve in this work |
| [MIDV-2020 author paper](https://arxiv.org/abs/2107.00396) | Public mock-document corpus with 1,000 distinct document instances; repeated frames are not independent instances | Provider annotations do not establish post-mutation readability or an approved reference |
| [Provider dataset page](https://smartengines.ru/science/dataset/) → [Zenodo record 18786808](https://zenodo.org/records/18786808) | Official provider links this record; release excludes original TIFF/video files | Pin file/version/checksum before using a new artifact; old FTP cache not asserted identical to every Zenodo file |
| [Provider license.txt](https://zenodo.org/records/18786808/files/license.txt?download=1) | CC BY-SA 2.5 Generic; provider also encourages Generated Photos attribution in derivatives | Source-license identification complete; maintain artifact-specific attribution and derivative obligations for any future release |
| [Provider readme.txt](https://zenodo.org/records/18786808/files/readme.txt?download=1) | Ten types, numbered instances, photo/template/scan/clip structure and VIA 2.0.11 annotations | Naming/schema alone cannot certify source survival or unseen status |
| [EASE Research](https://conf.researchr.org/track/ease-2027/ease-2027-papers), [Short/Emerging](https://conf.researchr.org/track/ease-2027/ease-2027-short-papers-and-emerging-results), [RENE](https://conf.researchr.org/track/ease-2027/ease-2027-reproducibility-and-negative-results) | Current format/deadline pages checked; negative findings are within Research scope | Track fit, novelty and empirical adequacy need an author decision; no acceptance prediction |

The license had not been found in the paper alone. Following the provider's
current download link resolved that gap; do not continue to label the dataset's
license as unknown. The record lists `license.txt` as 439 bytes with provider MD5
`2b7400d830c39eb792908265c936565d`. This is provider metadata, not a locally
recomputed checksum of a downloaded license/archive. Earlier repository statements
about CC BY-SA 2.5 are now backed by a directly inspected primary license file.

## Actual cached metadata inspection

[Script](inspect_midv_metadata.py) / [receipt](midv_metadata_feasibility.json).
Read only the already-local annotation headers; no images or output predictions
were viewed. The seven input files were hashed and checked unchanged during the
inspection. Native field names were preserved; no semantic remapping was approved.

| Cached header | Annotation files | Image rows | Regions | Shapes / content |
|---|---:|---:|---:|---|
| Photo | 10 | 1,000 | 2,000 | 1,000 rect + 1,000 polygon; field names only face/doc_quad |
| Template | 10 | 1,000 | 16,194 | Rectangles; native fields include body values, repeated variants and MRZ lines |

Body/MRZ coordinates can support inventory construction, but require a verified
semantic map and image-specific availability/readability evidence after mutations.
All 1,000 metadata rows being present does not mean 1,000 eligible new test IDs.

Five prior manifests were inspected: external_midv2020 selection, VLM v2 R2,
hard pairs, fair controls, and OCR labels. After normalizing numeric instance
spellings within type, their union contains **148 known exposed physical instances
across all 10 types**. This is a lower bound: completeness of all historical
exposure, pixel/near-duplicate lineage and pretraining overlap is unverified.
Do not infer that the remaining 852 instances are unseen or eligible. No sample
was allocated, no confirmatory manifest was created, and no reference was approved.

Existing private metadata/transcripts remain private. A prospective study needs
complete lineage, independent source validation and the design decisions listed in
[the protocol](../../../B_PROSPECTIVE_PROTOCOL_DRAFT.md).
