"""Fresh-output corpus/C2 audit entry point. Uses only existing local metadata."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from ..task55.data import EC, ROOT, save_new, sha
from .corpus_audit import scan
from .c2_inventory import build


def run(output, private):
    output, private = Path(output).resolve(), Path(private).resolve()
    if not output.is_relative_to((EC/'execution').resolve()) or not private.is_relative_to((EC/'local').resolve()):
        raise ValueError('Use public execution and private local destinations')
    if output.exists() or private.exists():
        raise FileExistsError('Preserve previous audit')
    started = datetime.now(timezone.utc).isoformat()
    aggregate, lineage, files = scan(ROOT)
    candidates, c2 = build(ROOT, lineage)
    save_new(private/'lineage.json', lineage)
    save_new(private/'input_hashes.json', files)
    save_new(private/'c2_candidates.json', candidates)
    save_new(output/'exposure_audit.json', aggregate)
    save_new(output/'c2_feasibility.json', c2)
    save_new(output/'receipt.json', dict(status='PASS_METADATA_AUDIT', start=started, end=datetime.now(timezone.utc).isoformat(),
        source_hashes={name:sha(Path(__file__).parent/name) for name in ('corpus_audit.py','c2_inventory.py','semantic_registry.py','semantic_registry.json','feasibility.py')},
        private_outputs={name:sha(private/name) for name in ('lineage.json','input_hashes.json','c2_candidates.json')},
        model_calls=0,training_runs=0,approvals_created=0,cohort_selected=False))
    return dict(status='PASS_METADATA_AUDIT', files_scanned=aggregate['files_scanned'], exposure=aggregate['exposure_states'],
                c2_candidates=c2['candidate_pairs'],c2_eligible=c2['eligible_pairs'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--private',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(run(args.output,args.private),indent=2))
