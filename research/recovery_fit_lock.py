"""Seal a deterministic development-only fit, optionally after inference completes."""
import argparse
import json
import time

from research.benchmark import save,digest
from research.recovery_study import OUT,CACHE,fit,process_lock


def main(wait=False):
    while not (OUT/'execution.json').exists():
        if not wait:raise RuntimeError('Inference is not complete')
        time.sleep(2)
    counts=[len(list((CACHE/f'pass{i}').glob('*.json'))) for i in (1,2,3)]
    if counts!=[540,24,24]:raise ValueError('All588 checkpoints are required')
    if (OUT/'summary.json').exists():raise RuntimeError('Test outcomes already released; do not refit')
    while True:
        try:
            with process_lock(CACHE/'process.lock'):
                fit();first={p:digest(OUT/p) for p in ('selector_models.json','selector_lock.json')}
                fit();second={p:digest(OUT/p) for p in first}
                if first!=second:raise ValueError('Repeated fitting is not byte-identical')
                save(OUT/'fit_repeat.json',dict(fit_calls=2,byte_identical=True,hashes=second,
                    checkpoint_counts=counts,test_scores_opened=False,code_sha256=digest(__file__),
                    meaning='Deterministic repeated fitting, not independent samples or performance replications'))
            break
        except RuntimeError as error:
            if wait and 'owns' in str(error):time.sleep(2);continue
            raise
    print('FIT_REPEAT_BYTE_IDENTICAL_LOCK_READY_FOR_COMMIT',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--wait',action='store_true')
    main(parser.parse_args().wait)
