"""Paired synthetic D4 operating characteristics. No case files, images or reader calls."""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from time import perf_counter
import tracemalloc

import numpy as np

from . import protocol_v4_candidate as inference
from .p5_simulation import wilson

F, N, U, I = 'FAULT', 'NO_FAULT', 'UNKNOWN', 'INVALID_TEST'
METHODS = ('v3', 'cluster_t', 'bounded')
METRICS = ('coverage', 'sensitivity', 'far_difference')


@dataclass(frozen=True)
class Cell:
    fault: bool
    checked: str
    asserted: str
    known: bool
    probability: float

    def counts(self):
        return (1, self.checked in (F, N), self.known and self.fault,
                self.known and self.fault and self.checked == F, self.known and not self.fault,
                (self.known and not self.fault) * (int(self.asserted == F) - int(self.checked == F)))


def population(a):
    """Construct and validate the full joint law *before* sampling any cohort."""
    family = a['family']
    if family not in ('mixed','active','stress'):
        raise ValueError('Unknown family')
    for name in ('prevalence','truth','miss_multiplier','icc','template_copy','coverage','sensitivity',
                 'effect','reverse','invalid','lost_fault'):
        if not 0 <= a[name] <= 1:
            raise ValueError('Infeasible probability: ' + name)
    if not (1 <= a['ids'] <= 200 and a['sizes'] and all(isinstance(m,int) and 1 <= m <= 4 for m in a['sizes'])
            and 1 <= a['template_size'] <= a['ids'] and a['ids'] % a['template_size'] == 0):
        raise ValueError('Invalid design frame')
    p, s, e, i, lost = (a[k] for k in ('prevalence','sensitivity','effect','invalid','lost_fault'))
    if not 0 < p < 1:
        raise ValueError('The conditional scenario design requires both latent truth strata')
    reverse = a['reverse']
    if family != 'stress' and reverse:
        raise ValueError('D4 forbids checked-only alarms')
    if family == 'active':
        if a['coverage'] or s or i or lost:
            raise ValueError('Active-literal panel requires all checked results UNKNOWN')
        fault = [(U,F,.8),(U,N,.2)]
        nonfault = [(U,F,e),(U,N,1-e)]
    else:
        plus = e + reverse
        positive_state = N if family == 'stress' else U
        extra = (1-a['coverage']-i-p*lost)/(1-p) - (plus if positive_state == U else 0)
        fault = [(F,F,s),(U,F,lost),(I,I,i),(N,N,1-s-lost-i)]
        nonfault = [(positive_state,F,plus),(F,N,reverse),(F,F,.025),(I,I,i),
                    (U,N,.2*extra),(U,U,.8*extra),(N,N,1-plus-reverse-.025-i-extra)]
    cells = []
    for flag, weight, rows in ((True,p,fault),(False,1-p,nonfault)):
        if any(q < -1e-12 for _,_,q in rows) or not np.isclose(sum(q for _,_,q in rows), 1, atol=1e-12,rtol=0):
            raise ValueError('Infeasible joint transition probabilities')
        for checked, asserted, q in rows:
            availability = a['truth'] * (a['miss_multiplier'] if flag and checked != F else 1)
            for known, prob in ((True,availability),(False,1-availability)):
                mass = weight*max(q,0)*prob
                if mass:
                    cells.append(Cell(flag,checked,asserted,known,mass))
    return cells


def estimands(cells):
    weights = np.array([c.probability for c in cells])
    means = weights @ np.array([c.counts() for c in cells])
    return [float(means[x]/means[y]) if means[y] else None for x,y in zip(inference.NUM,inference.DEN)]


def sample(rng, a, cells, batch):
    ids, g = a['ids'], a['template_size']
    sizes = np.resize(a['sizes'],ids)
    slots = int(sizes.max())
    cdf = np.cumsum([c.probability for c in cells])
    cdf[-1] = 1.
    draws = rng.random((batch,ids,slots))
    shared_id = rng.random((batch,ids,1)) < a['icc']
    draws = np.where(shared_id, draws[:,:,:1], draws)
    draws = draws.reshape(batch,ids//g,g,slots)
    shared_template = rng.random((batch,ids//g,1,1)) < a['template_copy']
    draws = np.where(shared_template, draws[:,:,:1,:1], draws).reshape(batch,ids,slots)
    mask = np.arange(slots) < sizes[:,None]
    vectors = np.array([c.counts() for c in cells],dtype=np.int64)
    return (vectors[np.searchsorted(cdf,draws,side='right')] * mask[None,:,:,None]).sum(axis=2)


def evaluate(a, cells, repetitions, seed):
    truth = estimands(cells)
    rng = np.random.default_rng(seed)
    methods = {m:dict(status=Counter(), joint=0, passes=np.zeros(3,int), covers=np.zeros(3,int),
                      joint_covers=0, seconds=0., peak_bytes=0) for m in METHODS}
    for start in range(0,repetitions,16):
        counts = sample(rng,a,cells,min(16,repetitions-start))
        b, ids, _ = counts.shape
        group = a['template_size']
        independent = counts.reshape(b,ids//group,group,6).sum(axis=2)
        for name, state in methods.items():
            tracemalloc.reset_peak()
            mem = tracemalloc.get_traced_memory()[0]
            begin = perf_counter()
            bounds, status = inference.infer(counts if name=='v3' else independent, name, a['family']!='stress')
            state['seconds'] += perf_counter()-begin
            state['peak_bytes'] = max(state['peak_bytes'], tracemalloc.get_traced_memory()[1]-mem)
            state['status'].update(status.tolist())
            hit = bounds <= np.array(truth,dtype=float) + 1e-12
            decision = inference.passes(bounds)
            state['passes'] += decision.sum(axis=0)
            state['joint'] += int(decision.all(axis=1).sum())
            state['covers'] += hit.sum(axis=0)
            state['joint_covers'] += int(hit.all(axis=1).sum())
    output = {}
    for name,s in methods.items():
        issued = s['status']['issued']
        output[name] = dict(status=dict(s['status']), issued=issued, insufficient=repetitions-issued,
                            joint=s['joint'], passes=s['passes'].tolist(), covers=s['covers'].tolist(),
                            joint_covers=s['joint_covers'], inference_seconds=s['seconds'],
                            peak_traced_bytes=s['peak_bytes'])
    return output


def run(design, stage):
    spec = design['stages'][stage]
    output = {}
    for label, overrides in design['scenarios'].items():
        a = design['defaults'] | overrides
        try:
            cells = population(a)
        except ValueError as exc:
            if not a.get('expect_rejection'):
                raise
            output[label] = dict(rejected=str(exc))
            continue
        if a.get('expect_rejection'):
            raise ValueError('Expected preflight rejection for ' + label)
        target = estimands(cells)
        seed = [spec['seed'],int.from_bytes(hashlib.sha256(label.encode()).digest()[:4],'big')]
        methods = evaluate(a,cells,spec['repetitions'],seed)
        output[label] = dict(target=target, seed=seed,
                             cells=[vars(c) for c in cells], methods=methods)
    return output


def verdict(points, method, repetitions):
    ref = points['mixed_200']['methods'][method]
    power = wilson(ref['joint'],repetitions)
    sizes = []
    for j, name in enumerate(('null_coverage','null_sensitivity','null_far')):
        s = points[name]['methods'][method]
        sizes.extend([wilson(s['joint'],repetitions),wilson(s['passes'][j],repetitions)])
    both = points['null_joint']['methods'][method]
    sizes.extend(wilson(k,repetitions) for k in [both['joint'],*both['passes']])
    cover = [wilson(k,ref['issued']) for k in ref['covers']]
    if (power['hi'] < .8 or any(m['lo'] > .05 for m in sizes)
            or any(m['hi'] is not None and m['hi'] < .95 for m in cover)):
        return 'INFEASIBLE'
    if (power['lo'] >= .8 and all(m['hi'] <= .05 for m in sizes)
            and all(m['lo'] is not None and m['lo'] >= .95 for m in cover)):
        return 'FEASIBLE'
    return 'INSUFFICIENT_EVIDENCE'


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('design',type=Path)
    cli.add_argument('stage',choices=('calibration','held_out'))
    cli.add_argument('output',type=Path)
    args=cli.parse_args()
    if args.output.exists():
        cli.error('Choose a fresh output')
    raw=args.design.read_bytes()
    design=json.loads(raw)
    tracemalloc.start()
    points=run(design,args.stage)
    n=design['stages'][args.stage]['repetitions']
    result=dict(design_sha256=hashlib.sha256(raw).hexdigest(),stage=args.stage,n=n,points=points,
                verdicts={m:verdict(points,m,n) for m in METHODS})
    with args.output.open('x',encoding='utf8',newline='\n') as f:
        json.dump(result,f,indent=2,allow_nan=False)
        f.write('\n')
