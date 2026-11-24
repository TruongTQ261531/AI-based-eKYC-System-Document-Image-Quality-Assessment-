"""Compare v2 Python core with v1 CJS for fixed synthetic randomized panels.

Run from repo root: python -m research.evidence_contract.cloud_g01_g03.differential_v2
Use --python-only only for the previously pinned v1 reference, not a Node replay.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
from . import c2_37_fixture_v2 as v

EXPECTED = dict(scenarios=128, comparisons=2688, checksum='b3b46e04')


def python_signature():
    seed, h, comparisons = 20261124, 2166136261, 0
    def rng():
        nonlocal seed
        seed = (seed*1664525+1013904223) & 0xffffffff
        return seed/4294967296
    def feed(x):
        nonlocal h, comparisons
        s = 'NA' if x is None else str(math.floor(x*1e9+0.5))
        for c in s+';':
            h = ((h^ord(c))*16777619) & 0xffffffff
        comparisons += 1
    pairs = [('FAULT','FAULT'),('NO_FAULT','NO_FAULT'),('UNKNOWN','UNKNOWN'),
             ('INVALID_TEST','INVALID_TEST'),('FAULT','UNKNOWN'),('NO_FAULT','UNKNOWN')]
    for _ in range(128):
        rows=[]; nmiss=0
        for c in v.locked_cases():
            a,z=pairs[int(rng()*len(pairs))]; t=rng()<.5
            if nmiss<8 and rng()<.22:
                t=None; nmiss+=1
            rows.append(dict(c,asserted=a,checked=z,truth=t))
        m=v.metrics(rows)
        for arm in v.ARMS:
            z=m['arms'][arm]; b=z['base']
            for value in (b['decision_coverage_all'],z['abstention'],b['sensitivity_all_labeled_faults'],b['FAR_all_labeled_nonfaults'],b['selective_risk']):
                feed(value['value'])
            for k in ('sensitivity_bounds','far_bounds'):
                feed(z[k]['minimum']);feed(z[k]['maximum'])
        feed(m['far_difference']['value']);feed(m['far_difference_bounds']['minimum']);feed(m['far_difference_bounds']['maximum'])
    return dict(scenarios=128,comparisons=comparisons,checksum=f'{h:08x}')


JS = r'''
const fs=require('node:fs'),path=require('node:path');
const dir=process.argv[1];
const {analyzeFixture}=require(path.join(dir,'c2_37_fixture.cjs'));
const fixture=new Function('require','console','process',fs.readFileSync(path.join(dir,'test_c2_37_fixture.cjs'),'utf8')+'\nreturn fixture;')(
  ()=>({analyzeFixture}),{log:()=>{}},{exitCode:0});
let seed=20261124,h=2166136261,comparisons=0;
function rng(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296}
function feed(x){const s=x===null?'NA':String(Math.round(x*1e9));for(const c of s+';')h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;comparisons++}
const pairs=[['FAULT','FAULT'],['NO_FAULT','NO_FAULT'],['UNKNOWN','UNKNOWN'],['INVALID_TEST','INVALID_TEST'],['FAULT','UNKNOWN'],['NO_FAULT','UNKNOWN']];
for(let i=0;i<128;i++){
 const f=fixture();let nmiss=0;
 for(const d of f.decisions){const [a,c]=pairs[Math.floor(rng()*pairs.length)];d.asserted.state=a;d.checked.state=c;let v=rng()<.5;if(nmiss<8&&rng()<.22){v=null;nmiss++}Object.assign(d.truth,{value:v,basis:v===null?null:'SYNTHETIC_INDEPENDENT_FIXTURE',evidence_sha256:v===null?null:'a'.repeat(64)})}
 const m=analyzeFixture(f).metrics;
 for(const arm of ['asserted','checked']){const v=m.arms[arm];for(const k of ['coverage','abstention','sensitivity','far','selective_risk'])feed(v[k].value);for(const k of ['sensitivity_missing_truth_bounds','far_missing_truth_bounds']){feed(v[k].minimum);feed(v[k].maximum)}}
 feed(m.far_difference.value);feed(m.far_difference_missing_truth_bounds.minimum);feed(m.far_difference_missing_truth_bounds.maximum);
}
console.log(JSON.stringify({scenarios:128,comparisons,checksum:h.toString(16).padStart(8,'0')}));
'''


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--python-only',action='store_true');a=p.parse_args()
    result=python_signature();assert result==EXPECTED,(result,EXPECTED)
    if not a.python_only:
        js=json.loads(subprocess.check_output(['node','-e',JS,str(Path(__file__).resolve().parent)],text=True))
        assert js==result,(js,result)
    print(json.dumps(dict(python=result,js_reference=EXPECTED,node_executed=not a.python_only,scope='SYNTHETIC_ONLY'),indent=2))


if __name__=='__main__':main()
