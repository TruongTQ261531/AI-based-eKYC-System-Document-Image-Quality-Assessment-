# Small external identity check, fixed before external inference

2026-10-28. Exploratory follow-up after v1 and v2, not confirmatory evidence.
Source: author-published `ftp://smartengines.com/midv-2020/`, as identified by
[the dataset paper](https://arxiv.org/abs/2107.00396). CC BY-SA 2.5; generated
portraits credited to Generated Photos by the author licence. No raw images,
annotations or text are published in this Git repository.

Select the **first two JPEG entries in each of the ten document-type directories
in the author's photo.tar archive**, independent of outcomes, for 20 different
physical mock documents. This bounded sample is chosen for practical transport
cost, not random representativeness. Record all chosen IDs, conditions, bytes
and hashes. Use metadata file sizes to skip TAR bodies; read only the selected
image bodies, metadata and small JPEG prefixes from templates.tar. Validate
TAR headers/checksums and metadata byte lengths; block SHA256 is provenance,
not authentication of the legacy FTP transport or whole-archive MD5 validation.

Use template annotations for text-field rectangles, project with the annotated
photo `doc_quad` from the canonical template image dimensions. Verify the
selected template filenames and dimensions against JPEG headers. Exclude
portrait, signature and face regions from the text-field target. No annotation
goes into the predictor. Keep fields/text local; publish numeric metrics only.

Run unchanged v1 localizer and all nine v1 methods; transfer calibration from
seed13 of the primary experiment. Also run all eight v2 operating points using
their already fixed seed13 parameters. **No external calibration or tuning.**
Report every image/method, geometry and field preservation, automatic coverage,
harmful automatic count and conditional harm. Report acquisition failures and
abort the complete experiment if any selected case is unavailable/malformed.

These are new physical IDs/text/portraits relative to MIDV500/2019, but the
ten template types overlap: this is **not unseen-template validation**.
Twenty cases are too few for strong statistical or robustness claims; report
counts alongside percentages and no significance test. In particular the
in-domain CRC assumptions do not imply a 10% OOD error guarantee here.
