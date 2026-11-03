"""Paired document-cluster intervals and the four registered primary tests."""
import numpy as np
from research.fc_common import SEEDS


def holm(values):
    order=sorted(range(len(values)),key=lambda i:values[i]);result=[None]*len(values);last=0.
    for rank,index in enumerate(order):
        last=max(last,min(1.,(len(values)-rank)*values[index]));result[index]=last
    return result


def f1(totals):
    return 2*totals[...,0]/np.maximum(1,totals[...,1]+totals[...,2])


def analyze(records, joined=False, permutations=True):
    rows=records['uniform_42']['rows'];ids=sorted({r['physical_id'] for r in rows})
    parent={p:p for p in ids}
    def root(p):
        while parent[p]!=p:p=parent[p]
        return p
    if joined:
        seen={}
        for row in rows:
            digest=row['pixel_sha256'];pid=row['physical_id']
            if digest in seen:parent[root(pid)]=root(seen[digest])
            else:seen[digest]=pid
    groups={p:root(p) for p in ids};clusters=sorted(set(groups.values()))
    sources={g:{r['source'] for r in rows if groups[r['physical_id']]==g} for g in clusters}
    if any(len(s)!=1 for s in sources.values()):raise ValueError('Cross-source pixel component cannot be source-stratified')
    rng=np.random.default_rng(20261106)
    draws=np.concatenate([rng.choice([i for i,g in enumerate(clusters) if sources[g]=={s}],
        (10000,sum(v=={s} for v in sources.values())),replace=True)
        for s in ('authored','midv2020') if any(v=={s} for v in sources.values())],axis=1)
    columns=('correct','reference','predicted','neighbor_correct','neighbor_reference_keys','declared_hidden_outputs')
    arrays={};values={}
    expected={(r['uid'],r['input_sha256']) for r in rows}
    for key,record in records.items():
        if len(record['rows'])!=len(rows) or {(r['uid'],r['input_sha256']) for r in record['rows']}!=expected:
            raise ValueError('Unpaired evaluation cases')
        array=np.array([[sum(r[f] for r in record['rows'] if groups[r['physical_id']]==g) for f in columns] for g in clusters],dtype=float)
        arrays[key]=array;totals=array[draws].sum(axis=1)
        values[key]=dict(f1=f1(totals),neighbor_recall=totals[:,3]/np.maximum(1,totals[:,4]),hidden_outputs=totals[:,5])
    comparisons=[]
    for seed in SEEDS:
        for other in ('random','repeat','uniform'):
            a,b=f'hard_{seed}',f'{other}_{seed}';primary=other!='uniform';result=dict(a=a,b=b,primary=primary)
            for metric in ('f1','neighbor_recall','hidden_outputs'):
                differences=values[a][metric]-values[b][metric]
                field='declared_hidden_outputs' if metric=='hidden_outputs' else metric
                result[metric]=dict(delta=records[a]['summary'][field]-records[b]['summary'][field],
                    ci95_low=float(np.percentile(differences,2.5)),ci95_high=float(np.percentile(differences,97.5)))
                if primary:
                    result[metric].update(ci9875_low=float(np.percentile(differences,.625)),
                                          ci9875_high=float(np.percentile(differences,99.375)))
            comparisons.append(result)
    if permutations:
        rng=np.random.default_rng(20261107);swaps=rng.integers(0,2,(10000,len(clusters)),dtype=np.int8)
        primary=[r for r in comparisons if r['primary']];pvalues=[]
        for result in primary:
            a,b=arrays[result['a']][:,:3],arrays[result['b']][:,:3]
            if not np.array_equal(a[:,1],b[:,1]):raise ValueError('Reference exposure differs in primary pair')
            observed=float(f1(a.sum(axis=0))-f1(b.sum(axis=0)))
            if abs(observed-result['f1']['delta'])>1e-12:raise ValueError('Point estimate differs from aggregated scores')
            moved=swaps@(a-b);delta=f1(a.sum(axis=0)-moved)-f1(b.sum(axis=0)+moved)
            extreme=int(np.count_nonzero(np.abs(delta)>=abs(observed)-1e-12))
            p=(extreme+1)/10001;pvalues.append(p)
            result.update(p_permutation=p,permutation_extreme_count=extreme)
        if len(primary)!=4:raise ValueError('Registered family must have exactly four comparisons')
        for result,p in zip(primary,holm(pvalues)):result['p_holm']=p
    return dict(bootstrap_seed=20261106,resamples=10000,permutation_seed=20261107,
        permutations=10000 if permutations else 0,primary_family_size=4,
        document_instances=len(ids),resampling_clusters=len(clusters),
        cluster_definition='Connected components of identical decoded test pixels' if joined else 'Document ID',
        condition='Fixed templates/cameras and trained adapters; no seed-population or new-camera guarantee',
        comparisons=comparisons)
