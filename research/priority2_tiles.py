"""Compare two tile budgets on the existing photographed development pairs."""

import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel

from research import labels_study
from research.labels_common import OUT as LABEL_OUT
from research.labels_common import ROOT, digest, read, sample_rows, save, sha, uid
from research.labels_metrics import summary
from research.v2_common import CONFIG
from research.v2_runtime import VLM
from research.vlm_final_report import paired_interval
from research.vlm_train import process_lock


CACHE = ROOT / 'research/cache/priority2_tiles_v1'
OUT = ROOT / 'research/results/priority2_tiles_v1'
PROFILES = ('rect2', 'rect4')


def measure(model, image, profile):
    model.profile = profile
    torch.cuda.synchronize()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    result = model.fresh(image)
    return dict(result, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                peak_reserved_bytes=torch.cuda.max_memory_reserved())


def main():
    source_signature = labels_study.verify_lock()
    manifest = read(LABEL_OUT / 'models.json')
    for name, expected in manifest['reused_sources'].items():
        if sha(ROOT / 'research' / name) != expected:
            raise ValueError(f'Frozen preprocessing, reader or scorer changed: {name}')
    adapter = ROOT / manifest['adapter_path']
    for filename, key in (('adapter_model.safetensors', 'adapter_sha256'),
                          ('adapter_config.json', 'adapter_config_sha256')):
        if sha(adapter / filename) != manifest[key]:
            raise ValueError(f'Frozen adapter asset changed: {filename}')
    if CONFIG['generation_max_new_tokens'] != manifest['max_new_tokens']:
        raise ValueError('Generation budget differs from the frozen checkpoint evaluation')

    rows = sorted((row for row in sample_rows('development') if row['source'] == 'midv2020'),
                  key=lambda row: (row['physical_id'], row['capture']))
    grouped = Counter((row['physical_id'], row['capture']) for row in rows)
    ids = sorted({row['physical_id'] for row in rows})
    expected = Counter((item, capture) for item in ids for capture in ('full', 'value_mask'))
    if len(ids) != 8 or grouped != expected:
        raise ValueError('Expected eight photographed development pairs')

    runs = []
    for index, row in enumerate(rows):
        order = PROFILES if sum(divmod(index, 2)) % 2 == 0 else PROFILES[::-1]
        runs.extend((row, profile) for profile in order)
    plan = dict(scope='Exploratory, photographed development only', roles=['development'],
                source_signature=source_signature, runner_sha256=sha(Path(__file__)),
                model='partial_42', adapter_sha256=manifest['adapter_sha256'],
                profiles=PROFILES, documents=len(ids), views=len(rows),
                schedule=[(uid(row['uid']), row['input_sha256'], profile) for row, profile in runs],
                warmup_calls_per_process=2, seed=42, host_threads=2,
                max_new_tokens=manifest['max_new_tokens'],
                timing_scope='Decoded RGB through rectification, vision and text generation',
                memory_scope='Peak PyTorch CUDA allocated/reserved, allocator cache cleared before each call',
                gpu=torch.cuda.get_device_name(), torch_version=torch.__version__,
                endpoint='Micro field F1, unsupported outputs, omissions, latency and memory',
                bootstrap_unit='physical_id', bootstrap_seed=20261104, decision='development only')
    signature = digest(plan)
    lock_path = OUT / 'plan.json'
    if lock_path.exists():
        if digest(read(lock_path)) != signature:
            raise ValueError('Existing priority 2 comparison was locked with different inputs')
    else:
        save(lock_path, plan)

    torch.set_num_threads(plan['host_threads'])
    model = VLM(plan['seed'], PROFILES[0])
    model.model.language_model = PeftModel.from_pretrained(model.model.language_model, str(adapter), is_trainable=False)
    model.model.eval()
    warmup = labels_study.open_image(rows[0])
    for profile in PROFILES:
        measure(model, warmup, profile)
        print('WARMUP', profile, flush=True)

    scores = {profile: [] for profile in PROFILES}
    raw_hashes = []
    for index, (row, profile) in enumerate(runs, start=1):
        path = CACHE / profile / f"{uid(row['uid'])}.json"
        contract = dict(signature=signature, input_sha256=row['input_sha256'], profile=profile)
        cached = path.exists()
        if cached:
            record = read(path)
            if record['contract'] != contract:
                raise ValueError('Stored inference no longer matches the run contract')
        else:
            image = labels_study.open_image(row)
            result = measure(model, image, profile)
            save(path, dict(contract=contract, result=result))
            record = read(path)
        result = record['result']
        scores[profile].append(labels_study.record(row, result, plan['model'], signature))
        raw_hashes.append(sha(path))
        print('RESUMED' if cached else 'MEASURED', index, len(runs), profile,
              round(result['wall_seconds'], 2), flush=True)

    results = {}
    for profile, records in scores.items():
        results[profile] = dict(
            all_views=summary(records),
            by_capture={capture: summary([r for r in records if r['capture'] == capture])
                        for capture in ('full', 'value_mask')},
            latency_median_seconds=float(np.median([r['wall_seconds'] for r in records])),
            latency_p95_seconds=float(np.percentile([r['wall_seconds'] for r in records], 95)),
            peak_allocated_bytes=max(r['peak_allocated_bytes'] for r in records),
            peak_reserved_bytes=max(r['peak_reserved_bytes'] for r in records),
        )
    baseline = read(LABEL_OUT / 'evaluation_partial_42.json')
    original = {row['uid']: row['prediction_sha256'] for row in baseline['rows'] if row['role'] == 'development'}
    comparison = paired_interval(scores['rect4'], scores['rect2'], seed=plan['bootstrap_seed'])
    save(OUT / 'comparison.json', dict(
        signature=signature, completed_measured_calls=len(runs), completed_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        results=results, paired_rect4_minus_rect2=comparison, raw_records_digest=digest(raw_hashes),
        rect2_match_to_priority1=sum(r['prediction_sha256'] == original[r['uid']] for r in scores['rect2']),
    ))
    print('PRIORITY2_COMPARISON_COMPLETE', flush=True)


if __name__ == '__main__':
    with process_lock():
        main()
