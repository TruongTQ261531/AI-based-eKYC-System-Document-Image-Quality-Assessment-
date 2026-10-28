"""Re-run one fixed hash-selected frame per physical ID/source, no cache reuse."""
import argparse
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from research.benchmark import worker, save, digest


def prediction_hash(prediction):
    return hashlib.sha256(json.dumps(prediction, sort_keys=True, allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-root', required=True)
    args = parser.parse_args()
    samples = json.loads(Path('research/data/primary_samples.json').read_text(encoding='utf-8'))
    cached = {r['uid']: r for r in map(json.loads, Path('research/cache/predictions.jsonl').read_text().splitlines())}
    by_group = {}
    for sample in samples:
        by_group.setdefault((sample['physical_id'], sample['source']), []).append(sample)
    selected = [min(group, key=lambda s: hashlib.sha256(('repeat-20261028/'+s['uid']).encode()).digest())
                for _, group in sorted(by_group.items())]
    started = time.monotonic()
    with ProcessPoolExecutor(max_workers=3) as pool:
        repeated = list(pool.map(worker, [(args.data_root, s) for s in selected]))
    rows = [dict(uid=row['uid'], prediction_sha256=prediction_hash(row['prediction']),
                 previous_prediction_sha256=prediction_hash(cached[row['uid']]['prediction']),
                 prediction_identical=row['prediction'] == cached[row['uid']]['prediction'],
                 input_identical=row['input_sha256'] == cached[row['uid']]['input_sha256']) for row in repeated]
    result = dict(code_sha256=digest(__file__), selected_images=len(rows), physical_ids=len({s['physical_id'] for s in selected}),
                  new_localizer_calls=len(rows)*3, cached_inference_reused=False,
                  prediction_mismatches=sum(not r['prediction_identical'] for r in rows),
                  input_mismatches=sum(not r['input_identical'] for r in rows),
                  elapsed_seconds=round(time.monotonic()-started, 2), rows=rows)
    save('research/results/reproducibility/inference_repeat.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}), flush=True)


if __name__ == '__main__': main()
