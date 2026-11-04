"""Fixed source-aware scoring and paired, descriptive layout/font effects."""
import numpy as np
from research.v3_metrics import scoring,summary
from research.labels_synth import CONDITIONS

def evaluate(sample,text):return scoring(sample,text)[0]

def micro(array):return 2*array[...,0]/np.maximum(1,array[...,1]+array[...,2])

def effects(rows,capture='full',role='test'):
    selected=[r for r in rows if r['source']=='authored' and r['role']==role and r['capture']==capture]
    ids=sorted({r['physical_id'] for r in selected})
    if len(selected)!=4*len(ids) or not ids:raise ValueError('Complete paired four-cell panel required')
    lookup={(r['physical_id'],r['condition']):r for r in selected}
    if len(lookup)!=len(selected):raise ValueError('Duplicated factorial cell')
    array=np.array([[[lookup[p,c][k] for k in ('correct','reference','predicted')] for c in CONDITIONS] for p in ids],dtype=float)
    if any(not np.array_equal(array[:,0,1],array[:,i,1]) for i in range(1,4)):raise ValueError('Reference exposure differs within the factorial')
    rng=np.random.default_rng(20261109);draws=rng.integers(0,len(ids),(10000,len(ids)))
    estimates=micro(array.sum(axis=0));replicates=micro(array[draws].sum(axis=1))
    contrasts={'layout_at_seen_font':[-1,1,0,0],'font_at_seen_layout':[-1,0,1,0],
               'combined_shift':[-1,0,0,1],'layout_font_interaction':[1,-1,-1,1]}
    result={}
    for name,weights in contrasts.items():
        delta=float(estimates@weights);values=replicates@weights
        result[name]=dict(delta=delta,ci95_low=float(np.percentile(values,2.5)),ci95_high=float(np.percentile(values,97.5)))
    return dict(document_instances=len(ids),capture=capture,role=role,bootstrap=10000,seed=20261109,
        conditions={c:dict(f1=float(estimates[i]),ci95_low=float(np.percentile(replicates[:,i],2.5)),
                           ci95_high=float(np.percentile(replicates[:,i],97.5))) for i,c in enumerate(CONDITIONS)},
        contrasts=result,inference_scope='Descriptive unadjusted intervals, fixed fonts/templates/model; not a superiority test')

def slices(rows):
    result={}
    for column in ('role','source','capture','condition','device','layout'):
        result[column]={}
        for value in sorted({str(r[column]) for r in rows}):
            subset=[r for r in rows if str(r[column])==value]
            result[column][value]=dict(images=len(subset),**summary(subset))
    return result
