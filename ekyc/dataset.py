"""Reconcile renamed JPEG labels with originals using visual content, never row order."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.optimize import linear_sum_assignment

from .config import ROOT, LABELS
from .io import write_json


def thumbnail(path):
    with Image.open(path) as image:
        return np.asarray(image.convert('RGB').resize((32, 32), Image.Resampling.BICUBIC), dtype=np.float32).reshape(-1)


def document_number(document):
    return int(document[4:]) if document.startswith('doc_') else int(document.split('_')[0])


def split_for(document):
    # Same physical document in MIDV500 and MIDV2019 MUST have the same split.
    number = document_number(document)
    ordered = sorted(range(1, 51), key=lambda n: hashlib.sha256(f'ekyc-42-{n}'.encode()).hexdigest())
    index = ordered.index(number)
    return 'test' if index < 8 else 'val' if index < 16 else 'train'


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare(root=ROOT, workers=8):
    root = Path(root).resolve()
    dataset = root / 'full_dataset_original'
    output = root / 'data'
    output.mkdir(exist_ok=True)
    labels = list(csv.DictReader((root / 'Multilabel.csv').open(encoding='utf-8-sig')))
    if len(labels) != 21000 or len({r['image_name'] for r in labels}) != 21000:
        raise ValueError('Expected exactly 21000 unique original label rows')
    if any(r['label'] not in LABELS for r in labels):
        raise ValueError('Unknown quality label')
    groups = defaultdict(list)
    for row in labels:
        groups[row['document']].append(row)
    references = sorted((dataset / 'midv2019_dataset').glob('*.tif'))
    if len(references) != 50:
        raise ValueError(f'Expected 50 MIDV2019 references, found {len(references)}')
    manifest, unresolved = [], []
    cache = output / 'thumbnail_cache'
    cache.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for group_index, (document, rows) in enumerate(groups.items(), 1):
            number = document_number(document)
            source = 'midv2019' if document.startswith('doc_') else 'midv500'
            if source == 'midv2019':
                paths = sorted((dataset/'midv2019_dataset').glob(f'*/*{number:02d}_*.tif'))
            else:
                paths = sorted((dataset/'midv500_dataset'/document/'images').glob('*/*.tif'))
            if len(paths) != len(rows):
                raise ValueError(f'{document}: {len(paths)} originals vs {len(rows)} labels')
            metadata = [(str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns) for p in paths]
            signature = hashlib.sha256(json.dumps(metadata).encode()).hexdigest()
            cache_path = cache / f'{source}_{number:02d}.npz'
            candidates = None
            if cache_path.exists():
                with np.load(cache_path) as stored:
                    if str(stored['signature']) == signature:
                        candidates = stored['vectors']
            if candidates is None:
                candidates = np.stack(list(pool.map(thumbnail, paths)))
                np.savez_compressed(cache_path, signature=signature, vectors=candidates)
            targets = np.stack(list(pool.map(thumbnail, [root/'dataset_224'/r['image_name'] for r in rows])))
            # Pairwise MSE without materializing an N x N x pixels array.
            distances = (np.sum(targets**2, axis=1)[:, None] + np.sum(candidates**2, axis=1)[None, :] - 2*targets@candidates.T) / targets.shape[1]
            distances = np.maximum(distances, 0)
            order = np.argsort(distances, axis=1)
            assigned_rows, assigned_columns = linear_sum_assignment(distances)
            chosen = dict(zip(assigned_rows.tolist(), assigned_columns.tolist()))
            assigned_labels = {column: rows[index]['label'] for index, column in chosen.items()}
            for index, row in enumerate(rows):
                best = chosen[index]
                second = next(int(column) for column in order[index] if int(column) != best)
                rmse = float(np.sqrt(distances[index, best]))
                ratio = float(distances[index, best] / max(float(distances[index, second]), 1e-6))
                # Adjacent near-identical frames may have no unique filename match.
                # Transfer a label only if EVERY plausible candidate has that same label.
                plausible = np.flatnonzero(distances[index] <= max(float(distances[index, best])*2, 1.5))
                equivalent = all(assigned_labels[int(column)] == row['label'] for column in plausible)
                mapping_kind = 'visual_unique' if ratio <= .50 else 'visual_equivalent_label'
                if rmse > 8 or (ratio > .50 and not equivalent):
                    unresolved.append(dict(row, best_candidate=str(paths[best].relative_to(root)), rmse=rmse, ratio=ratio))
                    continue
                manifest.append(dict(image_name=row['image_name'], relative_path=paths[best].relative_to(root).as_posix(),
                    document=f'{number:02d}', original_document=row['document'], label=row['label'],
                    source=source, origin='Multilabel.csv', split=split_for(document),
                    match_rmse=round(rmse, 5), match_ratio=round(ratio, 6), is_reference=0, mapping_kind=mapping_kind))
            print(f'[{group_index}/{len(groups)}] {document}: {len(rows)} rows; unresolved={len(unresolved)}', flush=True)
    additions = []
    for path in references:
        number = document_number(path.stem)
        additions.append(dict(image_name=f'midv2019_reference_{path.stem}.tif', relative_path=path.relative_to(root).as_posix(),
            document=f'{number:02d}', original_document=path.stem, label='Clean', source='midv2019',
            origin='user_requested_clean', split=split_for(path.stem), match_rmse='', match_ratio='', is_reference=1,
            mapping_kind='explicit_user_label'))
    write_csv(output/'midv2019_extra_clean.csv', additions)
    excluded = sorted((dataset/'midv500_dataset').glob('*/images/*.tif'))
    report = dict(original_label_rows=len(labels), matched_rows=len(manifest), added_clean=len(additions),
        unresolved_count=len(unresolved), unresolved=unresolved,
        excluded_midv500_references=[p.relative_to(root).as_posix() for p in excluded],
        input_labels_sha256=hashlib.sha256((root/'Multilabel.csv').read_bytes()).hexdigest())
    if unresolved:
        write_json(output/'dataset_report.json', report)
        raise ValueError(f'{len(unresolved)} ambiguous mappings. See data/dataset_report.json; no final manifest written.')
    manifest += additions
    assert len(manifest) == 21050
    assert len({r['relative_path'] for r in manifest}) == 21050
    report.update(total_images=len(manifest), label_counts=dict(Counter(r['label'] for r in manifest)),
                  mapping_counts=dict(Counter(r['mapping_kind'] for r in manifest)),
                  split_counts=dict(Counter(r['split'] for r in manifest)))
    write_csv(output/'manifest.csv', manifest)
    write_json(output/'dataset_report.json', report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('excluded_midv500_references', 'unresolved')}, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    prepare(args.root, args.workers)
