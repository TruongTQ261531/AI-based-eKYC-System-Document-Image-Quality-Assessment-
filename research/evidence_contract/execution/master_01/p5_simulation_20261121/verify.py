"""Check published MC denominators and replay selected points using only synthetic inputs."""
from pathlib import Path
import argparse
import hashlib
import json
from math import isclose

from research.evidence_contract.oracle_reliability import p5_simulation as sim


def check(ok, message):
    if not ok:
        raise ValueError(message)


def verify(folder):
    design=json.loads((folder/'design.json').read_bytes())
    observed=json.loads((folder/'operating_points.json').read_bytes())
    check(hashlib.sha256((folder/'design.json').read_bytes()).hexdigest()==observed['design_sha256'], 'Design hash')
    profiles=observed['profiles']
    check(set(profiles)==set(design['profiles']), 'Profile coverage')
    cohorts=draws=invalid=short=0
    for name, entry in profiles.items():
        assumptions = sim.Assumptions(**(design['defaults'] | design['profiles'][name]))
        planned = list(sim.profile_grid(assumptions,design))
        check(len(planned)==len(entry['points']), 'Grid size')
        for (label,a,e), p in zip(planned, entry['points'],strict=True):
            n=design['trials']
            check((p['label'],p['effect'],p['assumptions'])==(label,e,sim.asdict(a)), 'Grid point')
            check(tuple(p['target'])==a.targets(e), 'Population targets')
            c,s,d=p['target']
            if label.startswith('null_'):
                check(c < .8 or s < .8 or d <= .05,'False null assumption')
            check(p['issued'] + p['short_clusters'] + p['invalid_bootstrap_cohorts'] + p['degenerate_any']==n, 'Guard accounting')
            check(p['joint_pass']['k'] <= p['issued'] and p['insufficient']['k']==n-p['issued'], 'Pass accounting')
            check(p['joint_pass']['n']==n and p['bootstrap_draws']==(n-p['short_clusters'])*sim.v3.REPLICATES,'Denominator')
            check(all(m['n']==p['issued'] for m in p['coverage_if_issued'].values()),'CI denominator')
            check(p['pass_if_only_coverage_degeneracy_waived']['k']-p['joint_pass']['k']==p['additional_passes_if_waived']['k']
                  <=p['degenerate_by_metric']['decision_coverage'],'Paired guard comparison')
            for metric in [p['joint_pass'],p['insufficient'],*p['coverage_if_issued'].values()]:
                check(metric==sim.wilson(metric['k'],metric['n']), 'MC interval')
            cohorts+=n
            draws+=p['bootstrap_draws']
            invalid+=p['invalid_bootstrap_draws']
            short+=p['short_clusters']
        check(all(entry[k]==v for k,v in sim.summarize(entry['points'],design).items()), 'Decision or MDE')
    a=sim.Assumptions(**design['defaults'])
    seed=[design['seed'],int.from_bytes(hashlib.sha256(b'reference').digest()[:4],'big')]
    p=next(x for x in profiles['reference']['points'] if x['label']=='effect_grid' and isclose(x['effect'],.1))
    replay = sim.operating_point(a,.1,design['trials'],seed,'effect_grid')
    check(json.loads(json.dumps(replay,allow_nan=False))==p,'Reference point deterministic replay')
    # New data seed, same frozen bootstrap rule. This replication is reported separately.
    replication={}
    for label, params, effect in sim.profile_grid(a,design):
        if label=='null_sensitivity' or (label=='effect_grid' and isclose(effect,.1)):
            point=sim.operating_point(params,effect,2400,[628104,17],label)
            replication[label]=dict(joint_pass=point['joint_pass'], coverage_if_issued=point['coverage_if_issued'],
                                    insufficient=point['insufficient'])
    return dict(main_grid_cohorts=cohorts, attempted_bootstrap_draws=draws, invalid_bootstrap_draws=invalid,
                insufficient_before_bootstrap=short, reference_same_seed_exact=True,
                independent_data_seed=[628104,17], independent_replication=replication)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path, nargs='?', default=Path(__file__).resolve().parent)
    print(json.dumps(verify(parser.parse_args().folder),indent=2,allow_nan=False))
