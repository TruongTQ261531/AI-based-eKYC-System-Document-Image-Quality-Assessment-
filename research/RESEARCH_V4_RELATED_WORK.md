# Prior art and honest contribution boundary,2026-10-30

This follows the earlier literature review, with primary-source updates.
Do not present a renamed crop, standard regressor or familiar cascade as new
theory. The final contribution decision must use the locked test results.

| Primary source | Already established | What this study can test separately |
|---|---|---|
| [DocAttentionRect, BMVC2025](https://bmvc2025.bmva.org/proceedings/39/) | Learned rectification explicitly addresses partial/missing boundaries. | Missing boundaries alone are not novelty. Test downstream information and budget on identity-document captures. Paper/code availability must be disclosed; its numbers on other datasets are not measured baselines here. |
| [ArbDR / Cascaded Robust Rectification](https://github.com/chaoyunwang/ArbDR) | Cascaded document correction and OCR/layout-aware evaluation, including incomplete boundaries. | A new acronym for staged rectification is insufficient. Our controlled visibility references, identity splits and actual CPU traces are the proposed evaluation focus. |
| [DocRes, CVPR2024](https://openaccess.thecvf.com/content/CVPR2024/html/Zhang_DocRes_A_Generalist_Model_Toward_Unifying_Document_Image_Restoration_Tasks_CVPR_2024_paper.html) | Unified document restoration. | No generalist restoration/SOTA claim; use lightweight source-preserving operations and report their limits. |
| [DocAligner source](https://github.com/DocsaidLab/DocAligner/tree/3275b0f07f8e99d8c01cb0774dea2549be1416b6) | Corner heatmaps, ONNX CPU inference, multiple backbones. | Pin models, compare FastViT and LCNet, execute author numerical preprocessing/decoding, preserve earlier adapter results and edge-case differences. |
| [DocAligner training datasets](https://docsaid.org/en/docs/docaligner/dataset) and [author demo](https://docsaid.org/en/playground/docaligner) | MIDV500/2019 are mentioned in training construction; the demo identifies seen training examples. | New MIDV study IDs cannot automatically be called unseen-pretraining. Separately authored specimen images address known-source exposure, with limited photographic realism. |
| [RapidOCR author implementation](https://github.com/RapidAI/RapidOCR), [version1.4.4 model documentation](https://rapidai.github.io/RapidOCRDocs/v1.4.4/model_list/) | CPU OCR from published Paddle models and ONNX Runtime. | Compare the unchanged official1.4.4 inference code at explicit max960/thread2 settings. Latin PP-OCRv5 recognition paired with PP-OCRv4 detection is a mixed pipeline, not a claim to have run the complete latest PP-OCRv5 system. |
| [MIDV-2020](https://arxiv.org/abs/2107.00396) | A much larger identity-document dataset with mock identities and annotations already exists. | Do not claim our60 photos or their transformed variants are a new real collection. The prospective artifact adds controlled capture/visible-reference contracts and newly authored bilingual specimens. |
| [SIDTD, Scientific Data2024](https://www.nature.com/articles/s41597-024-04160-9) | Synthetic/forged identity-document datasets and metadata already exist. | A synthetic document dataset alone is not novel; our scope concerns frame clipping and downstream transcription/review rather than forgery detection. |
| [DocXPand / DocXPand-25k](https://github.com/quicksign/docxpand) | A public synthetic identity-document generator and a larger generated dataset already exist. | Ninety newly drawn specimen IDs are not by themselves a sufficient dataset novelty claim. Focus on controlled visibility contracts, semantic fields, exact regeneration, ID/layout separation and downstream cost/review evaluation. |
| [Kim et al., IJDAR2026](https://link.springer.com/article/10.1007/s10032-026-00620-7) | SHC separates visible/full transcripts, and ConfRoute studies confidence-based OCR/VLM escalation. | Neither dual references nor confidence routing is first introduced here. Our candidate distinction is partial ID geometry, non-generative view rereading, explicit semantic fields and strict document-role splits. The paper itself discloses historical source-role overlap; our source separation still does not establish unseen model pretraining. |
| [DocOCR-Eval](https://arxiv.org/abs/2607.16203) | OCR assessment/tool selection without manual labels is already studied. | Confidence-based selection itself is not a new idea. Compare naive confidence with development-fitted and budgeted alternatives, including costs and negative results. |

## Baselines actually available on this machine

1. Published FastViT-SA24 and LCNet100 DocAligner weights, common pinned
   author numerical path; raw, strict, padded completion, bbox, contour and
   predicted-line deskew controls.
2. Official RapidOCR1.4.4 wheel PP-OCRv4 default models at the stated CPU
   configuration; official Latin PP-OCRv5 recognizer as a language alternative.
   No package installation, no reimplementation of its OCR postprocessor.
3. Existing CRAFT/EasyOCR English and VietOCR, plus a colour-crop ablation,
   cross-checked on the same fixed24-case panel rather than all540 cases.

Commercial OCR APIs are not claimed tested: no account, token, cost agreement
or permission to send document photographs to third parties was provided.
Published paper numbers on other datasets/hardware are not copied into our
experimental tables. An unavailable neural rectifier is recorded as unavailable,
not assigned a fabricated result. These comparators do not justify a universal
market-leading or state-of-the-art claim.

## What could constitute a useful paper contribution

An auditable partial-capture evaluation that separates visible-content OCR,
semantic schema extraction and whole-document review, plus evidence that a
bounded online cascade improves a meaningful accuracy/latency/review trade-off
against simple completion on held-out identities/layouts. Show all alternatives,
do not hide a winning baseline, and distinguish actual online time from
exhaustive-view cost estimates. If the cascade does not improve the trade-off,
the algorithm-superiority claim fails; a carefully scoped empirical artifact
paper would need its own novelty and external-validity justification.
