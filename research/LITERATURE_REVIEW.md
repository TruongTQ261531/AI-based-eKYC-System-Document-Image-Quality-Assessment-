# Research and venue review, checked 2026-10-28

Priority requested by the user: CORE B conference. Rankings and CFPs are
time-dependent; dates/ranks below are checked against primary sources.
Paper acceptance and an exhaustive novelty guarantee cannot be promised.

## Current directions and relevance

| Direction | Primary work | Implication for this project |
|---|---|---|
| Document-specific perceptual and OCR-aware quality | [DocIQ, ISCAS 2026 / arXiv 2509.17012](https://arxiv.org/abs/2509.17012); [VQualA 2025 DIQA challenge](https://doi.org/10.1109/ICCVW69036.2025.00351) | MOS/quality-head modelling and document-aware feature fusion already exist. A Clean-vs-defect classifier alone is weak novelty. |
| Predicting OCR usability from lightweight features | [Krithika et al., 2026](https://doi.org/10.3389/frsip.2026.1779355) | Handcrafted quality features plus a regressor to predict OCR quality are already studied. Merely replacing MobileNet with XGBoost is not a persuasive new contribution. |
| Joint geometry, illumination and layout-aware evaluation | [Cascaded Robust Rectification, 2025](https://arxiv.org/abs/2511.23150); [DocCPLNet, 2025](https://doi.org/10.3390/s25206304) | Geometry evaluation should detect content loss, not only visual straightness. Training another dewarping network is comparatively expensive on this CPU-only machine. |
| Restoration plus semantic OCR correction | [PreP-OCR, ACL 2025](https://aclanthology.org/2025.acl-long.749/) | A restoration/OCR pipeline is not automatically novel. Semantic correction requires special care on identifiers: plausible text is not ground truth. |
| MLLM quality assessment | [Q-Doc, 2025](https://arxiv.org/abs/2511.11410) | Benchmarking quality reasoning and distortion severity is active. Large-model prompting alone would add cost and needs independent labels. |
| Reliable KIE and selective review | [Rombach & Mehdiyev, IJDAR 2026](https://doi.org/10.1007/s10032-026-00572-y) | Split conformal prediction and uncertainty-driven human review in document extraction are established prior work. |
| Adaptive spatial uncertainty | [Timans et al., ECCV 2024](https://arxiv.org/abs/2403.07263); [SeqCRC, 2025](https://arxiv.org/abs/2505.24038); [Ries et al., 2026](https://arxiv.org/abs/2605.07549) | Conformal box expansion, adaptive scales and sequential risk calibration are not new inventions in this project. |
| Expanded crops followed by recognition | [TriCCOT, BMVC 2026](https://arxiv.org/abs/2609.08659) | Especially close conceptual precedent: conformal enlargement before a downstream classifier. A document-specific claim must differ beyond renaming. |
| Unified physical/digital face attack detection | [MAYA, ICCVW 2025](https://openaccess.thecvf.com/content/ICCV2025W/FAS2025/html/Kim_MAYA_Multi-Attack_Yielding_Augmentation_for_Unified_Face_Attack_Detection_ICCVW_2025_paper.html); [FaceCoT, CVPR 2026](https://openaccess.thecvf.com/content/CVPR2026/html/Zhang_Harnessing_Chain-of-Thought_Reasoning_in_Multimodal_Large_Language_Models_for_Face_CVPR_2026_paper.html) | Screen replay and digital injection are different threats. MIDV document photographs do not supply PAD training/evaluation labels. New collection/access and subject/device splits would be required. |
| Efficient cross-domain PAD with frozen features | [Feng et al., CVPRW 2026](https://openaccess.thecvf.com/content/CVPR2026W/BIOM2026/html/Feng_Benchmarking_Vision_Foundation_Models_for_Domain-Generalizable_Face_Anti-Spoofing_CVPRW_2026_paper.html) | Frozen foundation-model PAD is a relevant alternative, but current MiniFASNet integration is not a new PAD algorithm or evidence of replay resistance. |

## Narrow candidate investigated here

Working title: **Field-preserving support regions for mobile identity-document
rectification under boundary uncertainty**.

The useful question is whether a low-cost intervention can preserve downstream
text regions while avoiding an arbitrarily large crop. The particular candidate
uses document-group calibration, per-edge geometric uncertainty, and annotated
text-field survival as the calibration target. It is assessed against an
uncalibrated version, constant-scale calibration and fixed margins.

The contribution being investigated is **the document/field-specific objective,
video-group protocol, decision trade-off and evidence**. Half-plane geometry,
multi-view consistency, order-statistic conformal calibration and box enlargement
are established ideas. Calling their combination a wholly new statistical
theory, or claiming to be the first uncertainty-aware OCR pipeline, would be
unsupported.

The code is small, training-free and CPU compatible. It fits the existing
document problem more directly than building a new VLM/dewarping/PAD model.
Whether it reaches CORE B contribution level depends on measured utility,
closest-prior comparisons and a realistic external validation, not an acronym.

## Venue evidence

| Venue | Verified rank | Current opportunity / constraint |
|---|---|---|
| ACM DocEng | **B, ICORE2026**, [official ranking](https://portal.core.edu.au/conf-ranks/2003/) | [DocEng 2027](https://doceng.org/doceng2027): 24–27 August 2027, Calgary. Official page says more information forthcoming; no verified 2027 submission deadline yet. Best topical fit for a rigorous document-workflow/measurement paper. |
| ICPR | **B, ICORE2026**, [official ranking](https://portal.core.edu.au/conf-ranks/1169/) | [IAPR schedule](https://iapr.org/conferences/conference-schedule/) lists the new virtual 2027 event and 1 March 2027 deadline. Confirm how the new ICPRv edition is recognised by the institution; do not automatically assume that a series ranking resolves that administrative question. |
| ICIP | **B, ICORE2026**, [official portal row](https://portal.core.edu.au/conf-ranks/?by=all&page=31&sort=afor1&source=all) | Relevant to image-processing methods; a current 2027 deadline has not been verified in this review. Needs a stronger method-focused comparison. |
| CAIP | **C, ICORE2026**, [official ranking](https://portal.core.edu.au/conf-ranks/955/) | Older B listings are outdated for this target; not recommended as a current CORE B choice. |

These are conference ranks, not journal quartiles. A short/demo track or workshop
must not be represented as a full main-conference research-paper acceptance.

## Evidence required for a submission decision

1. All prespecified runs and failures, physically disjoint calibration/test IDs,
   input/code hashes, paired ID-level uncertainty intervals and runtime.
2. Utility beyond trivially retaining the whole camera frame; report area cost
   and automatic-processing coverage as well as text retention.
3. OCR character-error evidence distinguished from oracle-controlled geometry
   diagnostics; no use of confidence or OCR consensus as true character labels.
4. Comparison to a strong independent neural localizer and the closest conformal
   localization baselines before making a SOTA claim.
5. A new external identity/template set: the mentor geometric heuristic was
   developed/reviewed on some MIDV examples before this study. Randomly splitting
   the same 50 IDs now does not erase that historical exposure.

Until these points are assessed, the honest label is a candidate with measured
feasibility, not a guaranteed CORE B paper.
