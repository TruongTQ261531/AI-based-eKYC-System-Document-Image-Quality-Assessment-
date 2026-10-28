# Mentor baseline: eKYC 3.2.0

Frozen on 2026-10-28, before the separate paper/research extension.

- Branch: `mentor/ekyc-v3.2.0`.
- Original running workspace is retained; experiments belong to a separate worktree/branch.
- Runtime source in `ekyc/` and `web/` is copied from the tested local baseline without research changes.
- Baseline local validation: 110 Python tests and 15 frontend tests passed. One Python test requires the external MIDV images.
- On a source-only clone: `python -m pytest --ignore=tests/test_manifest.py -q`. This does not replace the dataset integration check.
- Dataset metadata/quality labels are included; raw document/selfie images, session data, caches and personal debug images are excluded.
- Active quality checkpoint and training report are included. Download the other public weights explicitly with `python -m ekyc.download_models` and `python -m scripts.setup_identity_models`.
- Third-party code/weights retain their source terms. See `models/*sources.json` and `docs/ocr_and_pad.md`; the repository MIT license does not relicense upstream assets.

This is a development baseline, not PAD certification or a paper-acceptance claim. The legacy quality checkpoint has uncertain historical training provenance; do not present it as a leakage-free research result.
