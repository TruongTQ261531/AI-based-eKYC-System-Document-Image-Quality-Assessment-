"""Independent stdlib D4 file/frame/paired arithmetic verifier; no policy import."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from .verify_reporting_v2 import verify as arithmetic


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def verify(folder):
    folder=Path(folder);read=lambda name:json.loads((folder/name).read_bytes())
    manifest=read('manifest.json')
    for name,h in manifest['files'].items():assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==h,name
    rows=read('control_results.json');spec=read('expected_controls.json');summary=read('summary.json');divergences=read('divergences.json')
    assert len(rows)==len(spec)==summary['controls']==len({r['name'] for r in rows})
    assert digest(spec)==manifest['source_spec_sha256']
    expected={c['name']:c for c in spec};projected=Counter();observed=[];costs={a:Counter() for a in ('checked_v2','mrz_metadata_asserted')}
    for r in rows:
        assert r['truth']==expected[r['name']]['truth'] and r['expected']==expected[r['name']]['expected_by_tier']
        assert r['physical_ids']==0 and set(r['panels'])=={'1','2'}
        for tier,panel in r['panels'].items():
            assert panel['shared_input_sha256']==digest(dict(r['shared_input'],tier=int(tier)))
            assert panel['minimum_grade']==int(tier) and panel['approved_reference_count']==0
            assert not panel['independent_gold'] and not panel['scientific_go']
            assert panel['cost']['model_calls']==panel['cost']['training_runs']==0
            different=False
            for arm,value in panel['arms'].items():
                assert [value[e]['state'] for e in ('pointwise','relation','structure')]==r['expected'][tier][arm]
                for i,e in enumerate(('pointwise','relation','structure')):
                    d=value[e];assert d['alarm']==(d['state'] in ('FAULT','STRUCTURAL_ERROR'))
                    projected[('constructed_D4_tier'+tier,r['family'],r['shared_input']['context']['contract'],'symbolic_not_physical',arm,e,r['truth'][i],d['state'],d['reason'])]+=1
                costs[arm].update(panel['cost']['arms'][arm])
            a,b=(panel['arms'][arm] for arm in ('checked_v2','mrz_metadata_asserted'))
            different=any(a[e]!=b[e] for e in ('pointwise','relation','structure'))
            if different:
                assert r['family']=='literal_mrz_intervention';observed.append((r['name'],int(tier)))
            if r['name'] in summary['valid_MRZ_parity_cases']:assert not different
    assert sorted(observed)==sorted((d['name'],d['tier']) for d in divergences)
    assert len(observed)==summary['divergence_tier_pairs'] and len({n for n,t in observed})==summary['divergence_unique_controls']
    names=('dataset','partition','contract','cluster','method','endpoint','truth','state','reason')
    published=Counter()
    for cell in read('aggregate_cells.json'):published[tuple(cell[k] for k in names)]+=cell['count']
    assert projected==published
    assert {a:dict(c) for a,c in costs.items()}==summary['costs']
    assert costs['mrz_metadata_asserted']['literal_td3_calls']==0
    assert summary['paired_evaluations']==2*len(rows) and summary['arm_evaluations']==4*len(rows)
    assert summary['model_calls']==summary['training_runs']==summary['reference_approvals_created']==0
    assert summary['scientific_gate']=='NO_GO_SUPERIORITY' and not summary['prospective_started']
    a=arithmetic(folder/'aggregate_cells.json',folder/'accounting.json')
    return dict(status='PASS',controls=len(rows),paired_tier_evaluations=2*len(rows),divergence_tier_pairs=len(observed),
        arithmetic=a,shared_input_fingerprints_checked=2*len(rows),physical_ids=0,scope='Independent accounting/binding, not empirical truth or efficacy')


if __name__=='__main__':print(json.dumps(verify(sys.argv[1]),indent=2))
