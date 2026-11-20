"""Read-only paired production-gate replay of the same 46 historical cases."""
import argparse
from collections import Counter
import json
from pathlib import Path

from . import policy
from .mrz_ablation_v1 import compare_pair
from ..task55.data import EC,FrozenPilot,read,save_new,digest
from ..task55 import ifv


def run(output,private):
    output=Path(output).resolve();private=Path(private).resolve()
    if not output.is_relative_to((EC/'execution').resolve()) or not private.is_relative_to((EC/'local').resolve()):raise ValueError('Output scope')
    if output.exists() or private.exists():raise ValueError('Preserve previous replay')
    pilot=FrozenPilot()
    links=read(ifv.JOINS/'d7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223.json')
    rows=[];counts={a:{e:Counter() for e in policy.ENDPOINTS} for a in ('checked_v2','mrz_metadata_asserted')}
    for link in links.values():
        r=link['row'];ctx=policy.PairContext(r['contract_id'],r['field_key'],r['original_pixel_sha256'],r['followup_pixel_sha256'],digest(['historical_gate_probe',link['identity_sha256']]),r['validity'],'unassessed')
        result=compare_pair(None,ctx,pilot.outputs[r['reader'],r['original_pixel_sha256']],pilot.outputs[r['reader'],r['followup_pixel_sha256']],production=True)
        assert result['arms']['checked_v2']==result['arms']['mrz_metadata_asserted']
        assert result['approved_reference_count']==0
        for a,v in result['arms'].items():
            for e in policy.ENDPOINTS:counts[a][e][v[e]['state']]+=1
        rows.append(dict(identity=link['identity_sha256'],stratum=r['stratum'],result=result))
    pilot.assert_read_only();save_new(private/'rows.json',rows)
    public=dict(status='PASS_HISTORICAL_GATE_REPLAY',cases=len(rows),primary_cases=42,primary_physical_ids=3,
        state_counts={a:{e:dict(c) for e,c in v.items()} for a,v in counts.items()},parity_pairs=len(rows),
        private_rows_sha256=digest(rows),actual_cached_outputs=len(pilot.outputs),raw_reviews_imported=0,
        production_approvals=0,model_calls=0,training_runs=0,truth_labels_used=False,
        selective_risk_pointwise=None,selective_risk_relation=None,round_status='OPEN',
        scope='No bound approved reference; semantic endpoints abstain. Structural status comes from the frozen parser, not adjudicated truth. Replaying outputs is not new inference.')
    save_new(output/'summary.json',public);return public


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--private',required=True,type=Path)
    a=p.parse_args();print(json.dumps(run(a.output,a.private),indent=2))
