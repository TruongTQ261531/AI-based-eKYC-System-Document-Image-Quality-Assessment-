"""Bounded retries for transient Windows locks; identical serialization/payload."""
import time
from pathlib import Path
from research.fc_common import CACHE, OUT, save as original_save


def save_retry(path,value):
    path=Path(path).resolve()
    if not path.is_relative_to(CACHE.resolve()) and not path.is_relative_to(OUT.resolve()):
        raise ValueError('I/O retry is restricted to this study namespace')
    for attempt in range(8):
        try:
            return original_save(path,value)
        except PermissionError:
            if attempt==7:raise
            time.sleep(min(.05*2**attempt,.5))
