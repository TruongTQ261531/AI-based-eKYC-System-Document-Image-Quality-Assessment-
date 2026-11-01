"""Repeat PUBLISHED training in separate ignored outputs; not a fresh test study."""
import argparse
import json

from research.vlm_setup import CACHE,OUT,sha,save


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,choices=[42,31415],default=42)
    seed=parser.parse_args().seed
    from research import vlm_train as training
    reference=json.loads((OUT/f'train_seed_{seed}.json').read_text(encoding='utf-8'))
    destination=CACHE/'reproductions'/f'seed_{seed}'
    destination.mkdir(parents=True,exist_ok=True)
    # Hold the original GPU mutex before redirecting outputs; never overwrite
    # the published main study's checkpoints, predictions, results or lock.
    with training.process_lock():
        training.CACHE=destination/'private';training.OUT=destination/'results'
        training.CACHE.mkdir(parents=True,exist_ok=True);training.OUT.mkdir(parents=True,exist_ok=True)
        training.train(seed)
        result=json.loads((training.OUT/f'train_seed_{seed}.json').read_text(encoding='utf-8'))
        report=dict(seed=seed,published_signature=reference['signature'],reproduction_signature=result['signature'],
            published_adapter_sha256=reference['selected_adapter_sha256'],
            reproduced_adapter_sha256=result['selected_adapter_sha256'],
            byte_identical=reference['selected_adapter_sha256']==result['selected_adapter_sha256'],
            fresh_unseen_test_claim=False,main_study_overwritten=False,
            note='Numerical equality across different devices/drivers is not guaranteed; report differences.')
        save(destination/'reproduction.json',report);print(json.dumps(report),flush=True)


if __name__=='__main__':main()
