# Application source snapshot, 14 November 2026

This directory preserves completed changes from the separate parent application:
conflicting labelled names are omitted rather than concatenated, and custom
one-character values are retained. It also includes the offline regression script,
tests, application documentation and synthetic-only validation reports.

The research worktree's frozen readers were not replaced. This is an archived
application candidate, not an activated research subject or a new IFV result.
The parser matrix improved from 8/12 to 12/12 on authored OCR token fixtures;
backend 113 and camera frontend 15 tests passed. Two synthetic-card pipeline
smokes used real local weights. No weights or human submissions are included.

Source paths below `source/` mirror the application root. Review the patch before
applying it to another checkout. Existing research methods and past receipts
remain unchanged. `source_manifest.json` binds the snapshot bytes.
