"""Read cached provider metadata; do not view images, select a cohort or infer."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tarfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(root):
    root = Path(root).resolve()
    result = {}
    for filename in ('head.bin', 'template_head.bin'):
        path = root / 'research/data/midv2020' / filename
        before = sha(path)
        attributes, shapes, names = Counter(), Counter(), Counter()
        files = rows = regions = 0
        with tarfile.open(path, mode='r:') as archive:
            for entry in archive:
                if entry.name.rstrip('/') == 'images':
                    break
                if not entry.name.endswith('.json'):
                    continue
                data = json.loads(archive.extractfile(entry).read())
                files += 1
                for item in data['_via_img_metadata'].values():
                    rows += 1
                    for region in item['regions']:
                        regions += 1
                        attrs = region['region_attributes']
                        attributes.update(attrs.keys())
                        names.update([attrs['field_name']])
                        shapes.update([region['shape_attributes']['name']])
        if before != sha(path) or files != 10 or rows != 1000:
            raise ValueError('Unexpected or modified cached provider metadata')
        result[filename] = dict(sha256=before, annotation_files=files,
            image_metadata_rows=rows, regions=regions, region_attribute_keys=dict(attributes),
            shapes=dict(shapes), field_names=sorted(names), input_unchanged=True)
    rels = ['research/data/midv2020/selection.json',
            'research/data/vlm_lora_v2_r2/sources.json',
            'research/data/hard_pairs_v1/sources.json',
            'research/data/fair_controls_v1/sources.json',
            'research/data/ocr_labels_v1/sources.json']
    groups, sources = set(), {}
    for rel in rels:
        path = root / rel
        before = sha(path)
        data = json.loads(path.read_text(encoding='utf-8'))
        identities = set()
        for row in data:
            # Provider 00/0 spellings denote the same instance within a type.
            stem = Path(row['filename']).stem
            if not stem.isdigit():
                raise ValueError('Unknown provider instance spelling')
            identity = (row['code'], int(stem))
            if 'physical_id' in row:
                parts = row['physical_id'].split('/')
                if parts[:2] != ['midv2020', row['code']] or int(parts[-1]) != int(stem):
                    raise ValueError('Identity/filename binding mismatch')
            identities.add(identity)
        if before != sha(path):
            raise ValueError('Exposure input changed')
        groups.update(identities)
        sources[rel] = dict(sha256=before, rows=len(data), distinct_instances=len(identities))
    return dict(status='METADATA_FEASIBILITY_ONLY', metadata=result,
        inspected_exposure_manifests=sources, known_exposed_instances_lower_bound=len(groups),
        known_exposed_document_types=len({g[0] for g in groups}),
        total_history_completeness_verified=False, pixel_overlap_recomputed=False,
        pretraining_overlap='UNKNOWN', new_cohort_selected=False, new_images_downloaded=0,
        images_visually_reviewed=0, human_annotations_created=0, model_calls=0,
        source_inventory_or_readability_approved=False,
        script_sha256=sha(Path(__file__).resolve()))


if __name__ == '__main__':
    print(json.dumps(inspect(sys.argv[1]), indent=2, ensure_ascii=False))
