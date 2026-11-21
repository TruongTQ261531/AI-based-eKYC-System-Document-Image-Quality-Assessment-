"""Independent arithmetic and seed replay. Does not import P5B simulator or candidate."""
import argparse
from collections import Counter
from functools import lru_cache
import hashlib
import json
from math import ceil, log, sqrt
from pathlib import Path
import random

import numpy as np
from scipy.stats import binomtest, t


def need(condition, label):
    if not condition:
        raise ValueError(label)


def limits(k,n):
    if not n:
        return None,None
    ci=binomtest(k,n).proportion_ci(method='wilson')
    return ci.low,ci.high


def qualify(points,m,n):
    ref=points['mixed_200']['methods'][m]
    size=[]
    for i,k in enumerate(('null_coverage','null_sensitivity','null_far')):
        row=points[k]['methods'][m]
        size.extend([row['joint'],row['passes'][i]])
    joint=points['null_joint']['methods'][m]
    size += [joint['joint'],*joint['passes']]
    power=limits(ref['joint'],n)
    covers=[limits(k,ref['issued']) for k in ref['covers']]
    if power[1]<.8 or any(limits(k,n)[0]>.05 for k in size) or any(h is not None and h<.95 for _,h in covers):
        return 'INFEASIBLE'
    if power[0]>=.8 and all(limits(k,n)[1]<=.05 for k in size) and all(l is not None and l>=.95 for l,_ in covers):
        return 'FEASIBLE'
    return 'INSUFFICIENT_EVIDENCE'


def seed_replay(row,a,n):
    """Rebuild independent units from the published categorical law. Compare score
    acceptance at the three nulls and the true parameters without solving a quadratic.
    For the reference, separately replay the frozen order statistic via counting draws.
    """
    cells=row['cells']
    mass=[c['probability'] for c in cells]
    need(min(mass)>0 and abs(sum(mass)-1)<1e-11,'probability normalization')
    cat=[]
    for c in cells:
        h=c['checked']=='FAULT'
        f=c['fault'] and c['known']
        non=not c['fault'] and c['known']
        cat.append((1,c['checked'] in ('FAULT','NO_FAULT'),f,f and h,non,
                    int(non)*(int(c['asserted']=='FAULT')-int(h))))
        if a['family']!='stress':
            need(c['checked']==c['asserted'] or c['checked']=='UNKNOWN' and c['asserted'] in ('FAULT','NO_FAULT'),'transition support')
    values=np.array(cat,int)
    mean=np.array(mass) @ values
    den=[0,2,4]
    num=[1,3,5]
    truth=np.divide(mean[num],mean[den],out=np.full(3,np.nan),where=mean[den]!=0)
    np.testing.assert_allclose(row['target'] if None not in row['target'] else np.array(row['target'],float),truth,equal_nan=True)
    spec=[a['coverage'],a['sensitivity']/(a['sensitivity']+(1-a['sensitivity'])*a['miss_multiplier']) if a['truth'] else np.nan,
          a['effect'] if a['truth'] else np.nan]
    np.testing.assert_allclose(truth,spec,atol=1e-12,equal_nan=True)
    rng=np.random.default_rng(row['seed'])
    ids=a['ids']
    g=a['template_size']
    slots=np.resize(a['sizes'],ids)
    cdf=np.cumsum(mass)
    cdf[-1]=1.
    threshold=np.array([.8,.8,.05])
    methods=['cluster_t','bounded']
    if a.get('reference'):
        methods.append('v3')
    result={m:Counter() for m in methods}
    for start in range(0,n,16):
        b=min(n-start,16)
        u=rng.random((b,ids,max(slots)))
        same_id=rng.random((b,ids))<a['icc']
        u[same_id]=np.broadcast_to(u[:,:,:1],u.shape)[same_id]
        u=u.reshape(b,ids//g,g,-1)
        same_template=rng.random((b,ids//g))<a['template_copy']
        u[same_template]=np.broadcast_to(u[:,:,:1,:1],u.shape)[same_template]
        bins=values[np.digitize(u.reshape(b,ids,-1),cdf)]
        id_counts=(bins*(np.arange(max(slots))<slots[:,None])[None,:,:,None]).sum(axis=2)
        for m in methods:
            units=id_counts if m=='v3' else id_counts.reshape(b,ids//g,g,6).sum(axis=2)
            eligible=(np.count_nonzero(units[:,:,2],axis=1)>=30)&(np.count_nonzero(units[:,:,4],axis=1)>=30)
            z=units[eligible]
            if not len(z):
                continue
            x,y=z[:,:,num],z[:,:,den]
            if m=='v3':
                w=weights(ids)
                res=(z.transpose(0,2,1).astype(np.float32) @ w.T).astype(float)
                with np.errstate(invalid='ignore', divide='ignore'):
                    draws=res[:,num]/res[:,den]
                issue=(np.ptp(draws,axis=2)>0).all(axis=1) & np.isfinite(draws).all(axis=(1,2))
                # 500th lower rank >= t iff fewer than 500 draws < t (strict > uses <=).
                passed=(draws<threshold[None,:,None]).sum(axis=2)<500
                passed[:,2]=(draws[:,2]<=.05).sum(axis=1)<500
                covered=(draws<=truth[None,:,None]+1e-12).sum(axis=2)>=500
            else:
                k=z.shape[1]
                if m=='bounded':
                    width=[1,1,2 if a['family']=='stress' else 1]
                    crit=np.sqrt((z[:,:,0]**2).sum(axis=1)*log(20)/2)[:,None]*width
                    issue=np.ones(len(z),bool)
                    def statistic(r):
                        return (x-r*y).sum(axis=1)-crit
                else:
                    crit=t.ppf(.95,k-1)*sqrt(k)
                    ratio=x.sum(axis=1)/y.sum(axis=1)
                    issue=((y.sum(axis=1)>crit*y.std(axis=1,ddof=1)) &
                           (np.ptp(x-ratio[:,None,:]*y,axis=1)>1e-10)).all(axis=1)
                    def statistic(r):
                        score=x-r*y
                        return score.sum(axis=1)-crit*score.std(axis=1,ddof=1)
                at_null=statistic(threshold)
                passed=at_null>=0
                passed[:,2]=at_null[:,2]>0
                covered=statistic(truth)<=1e-9
            out=result[m]
            out['issued']+=int(issue.sum())
            for key,flags in [('passes',passed),('covers',covered)]:
                count=flags[issue]
                out['joint' if key=='passes' else 'joint_covers']+=int(count.all(axis=1).sum())
                for i,k in enumerate(count.sum(axis=0)):
                    out[key,i]+=int(k)
    for m,out in result.items():
        original=row['methods'][m]
        for key in ('issued','joint','joint_covers'):
            need(out[key]==original[key],f'{m}/{key}: {out[key]} vs {original[key]}')
        for key in ('passes','covers'):
            need([out[key,i] for i in range(3)]==original[key],m+'/'+key)


@lru_cache(maxsize=1)
def weights(ids):
    rng=random.Random(20261121)
    return np.array([np.bincount(rng.choices(range(ids),k=ids),minlength=ids) for _ in range(10000)],np.float32)


def sizing():
    # Split beta among three lower-bound tests and two contributing-unit guards.
    u=sqrt(log(20)/2)
    v=sqrt(log(25)/2)
    gaps=[.08,.2*.9*(.94-.80),.8*.9*(.10-.05)]
    endpoint=[ceil(((u+v)/d)**2) for d in gaps]
    clusters=[ceil(((v+sqrt(v*v+120*q))/(2*q))**2) for q in [.18,.72]]
    return dict(endpoint_sufficient_ids=endpoint,guard_sufficient_ids=clusters,
                all_sufficient_ids=max(endpoint+clusters))


def verify(folder):
    raw=(folder/'design.json').read_bytes()
    design=json.loads(raw)
    stages={}
    seeds=set()
    for stage,spec in design['stages'].items():
        report=json.loads((folder/(stage+'.json')).read_bytes())
        n=spec['repetitions']
        need(report['n']==n and report['stage']==stage and report['design_sha256']==hashlib.sha256(raw).hexdigest(),'design binding')
        need(set(report['points'])==set(design['scenarios']),'complete grid')
        for name,params in design['scenarios'].items():
            a=design['defaults']|params
            row=report['points'][name]
            if a.get('expect_rejection'):
                need('rejected' in row and a['effect']*(1-a['prevalence'])>1-a['coverage'],'impossible mechanism')
                continue
            want=[spec['seed'],int.from_bytes(hashlib.sha256(name.encode()).digest()[:4],'big')]
            need(row['seed']==want and tuple(want) not in seeds,'seed')
            seeds.add(tuple(want))
            for s in row['methods'].values():
                need(sum(s['status'].values())==n and s['issued']==s['status'].get('issued',0)
                     and s['insufficient']==n-s['issued'],'issuance')
                need(0<=s['joint']<=min(s['passes'])<=max(s['passes'])<=s['issued'],'pass denominators')
                need(0<=s['joint_covers']<=min(s['covers'])<=max(s['covers'])<=s['issued'],'coverage denominators')
            seed_replay(row,a|dict(reference=name=='mixed_200'),n)
        expected={m:qualify(report['points'],m,n) for m in design['methods']}
        need(expected==report['verdicts'],'qualification')
        stages[stage]=expected
    return dict(status='PASS',stages=stages,distinct_seed_pairs=len(seeds),
                candidate_replay='all issued, marginal decisions, interval coverages and joint tallies across both stages',
                v3_replay='reference point both stages, all counts; independent v3 entrypoint parity test on unequal sizes',
                sizing=sizing())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder',type=Path)
    print(json.dumps(verify(parser.parse_args().folder),indent=2))
