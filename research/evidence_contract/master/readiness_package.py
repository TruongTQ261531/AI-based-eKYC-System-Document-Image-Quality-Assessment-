"""Package only public, authored development evidence and its parser replay.

This archive is not an anonymous conference submission. Images, private reviews,
weights, caches and the downloaded TeX toolchain are deliberately outside it.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from ..task55.data import EC, digest, read, save_new, sha

OUT = EC / 'execution/master_01/readiness_20261116'


def build():
    target = EC / 'paper/readiness_replay_20261116.zip'
    extracted = EC / 'local/master_01/readiness_20261116/public_archive_replay'
    if target.exists() or extracted.exists():
        raise FileExistsError('Archive and extracted-run paths must both be fresh')
    files = {}
    def include(path, name):
        if name in files or Path(name).is_absolute() or '..' in Path(name).parts or ':' in name:
            raise ValueError('Unsafe/duplicate archive path')
        files[name] = path.read_bytes()
    for path in sorted((OUT / 'parser_run_01').rglob('*')):
        if path.is_file() and path.suffix in ('.json', '.py'):
            include(path, 'parser/' + path.relative_to(OUT / 'parser_run_01').as_posix())
    for name in ('cases.json', 'results.json', 'source_states.json'):
        include(OUT / 'representation_run_01' / name, 'representation/' + name)
    include(EC / 'master/readiness_verify.py', 'verify_parser.py')
    for name in ('parser_faults.py', 'representation_audit.py'):
        include(EC / 'master' / name, 'provenance/' + name)
    include(OUT / 'plan.json', 'provenance/plan.json')
    include(OUT / 'pdf_build_receipt.json', 'provenance/pdf_build_receipt.json')
    include(EC / 'paper/output/pdf/emerging_20261116.pdf', 'paper/emerging_20261116.pdf')
    for name in ('emerging_20261116.tex', 'references.bib', 'readiness_references.bib'):
        include(EC / 'paper' / name, 'paper/' + name)
    files['README.md'] = b'''# Public development replay (16 November 2026)

This is not a final anonymous conference supplement. Inputs and requirements
are authored after two historical parser faults were known. No image, human
review submission, model output cache, weights or compiler is included.

With standard Python 3.10+, from this extracted directory:

    python -I -B verify_parser.py parser

The verifier checks five pinned parser versions, 118 authored cases and two
minimal witnesses (596 calls). It validates computational reproduction against
the saved author requirements, not independent reference truth. It does not
independently replay timings or budget permutations. They are descriptive
development measurements; two fault families are not 76 independent defects.

The representation files contain 255 abstract source configurations and 164
injected boundary controls. They are not natural-model outputs. Their full
re-execution uses the repository renderer and frozen oracle dependencies;
provenance code is included for inspection, not a standalone image replay.

The PDF is a three-page internal Emerging Results draft. Author/novelty review,
final anonymity, redistribution and conference-format checks remain open.
MANIFEST.json binds every included file. Hashes establish integrity, not truth.
'''
    manifest = dict(schema='public-readiness-replay/1', scope='PUBLIC_DEVELOPMENT_NOT_ANONYMOUS_SUBMISSION',
                    files={name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()})
    files['MANIFEST.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (2026, 11, 16, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, payload)
    with zipfile.ZipFile(target) as archive:
        if len(archive.namelist()) != len(files) or len(set(archive.namelist())) != len(files):
            raise ValueError('Archive membership differs')
        for name, payload in files.items():
            if archive.read(name) != payload:
                raise ValueError('Archive byte verification failed')
        for name in archive.namelist():
            resolved = (extracted / name).resolve()
            if not resolved.is_relative_to(extracted.resolve()):
                raise ValueError('Extraction escapes its fresh directory')
        archive.extractall(extracted)
    execution = subprocess.run([sys.executable, '-I', '-B', str(extracted / 'verify_parser.py'), str(extracted / 'parser')],
                               capture_output=True, text=True, encoding='utf-8', check=False)
    with (OUT / 'extracted_archive_replay.log').open('x', encoding='utf-8') as stream:
        stream.write(execution.stdout + execution.stderr)
    if execution.returncode != 0:
        raise ValueError('Extracted archive replay failed; inspect the preserved log')
    verification = json.loads(execution.stdout)
    if verification['status'] != 'PASS_PINNED_PROGRAM_REPLAY':
        raise ValueError('Unexpected replay status')
    receipt = dict(schema='public-readiness-package/1', archive='paper/' + target.name,
        archive_sha256=sha(target), bytes=target.stat().st_size, files=len(files), manifest_sha256=digest(manifest),
        byte_verification=True, isolated_extracted_replay=verification, model_calls=0,
        private_review_files_included=False, image_files_included=False, downloaded_compiler_included=False,
        final_anonymous_release=False)
    save_new(OUT / 'package_receipt.json', receipt)
    return receipt


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
