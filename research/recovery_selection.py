"""Small auditable selector alternatives; fit only on development identities."""
import hashlib
import math

import numpy as np

from research.recovery_runtime import POLICIES

FALLBACKS=('raw','bbox','contour','lcnet')


def fit_regressor(X,y,kind='ridge',strength=1.):
    X=np.asarray(X,float);y=np.asarray(y,float)
    if kind=='ridge':
        mean=X.mean(axis=0);std=X.std(axis=0);std[std<1e-8]=1.;mean[0]=0.;std[0]=1.
        Z=(X-mean)/std;penalty=np.eye(Z.shape[1])*strength;penalty[0,0]=1e-8
        beta=np.linalg.solve(Z.T@Z+penalty,Z.T@y)
        return dict(kind=kind,mean=mean.tolist(),std=std.tolist(),beta=beta.tolist(),strength=strength)
    base=float(y.mean());prediction=np.full(len(y),base);stumps=[]
    for _ in range(int(strength)):
        residual=y-prediction;best=None
        for j in range(1,X.shape[1]):
            for threshold in np.unique(np.quantile(X[:,j],[.2,.4,.6,.8])):
                left=X[:,j]<=threshold
                if not left.any() or left.all():continue
                a,b=float(residual[left].mean()),float(residual[~left].mean())
                error=float(np.sum((residual-np.where(left,a,b))**2))
                if best is None or error<best[0]:best=(error,j,float(threshold),a,b)
        if best is None:break
        _,j,t,a,b=best;stumps.append([j,t,.2*a,.2*b]);prediction+=np.where(X[:,j]<=t,.2*a,.2*b)
    return dict(kind='stumps',base=base,stumps=stumps,strength=strength)


def predict(model,X):
    X=np.asarray(X,float);single=X.ndim==1
    if single:X=X[None]
    if model['kind']=='ridge':result=((X-np.array(model['mean']))/np.array(model['std']))@np.array(model['beta'])
    else:
        result=np.full(len(X),model['base'])
        for j,t,a,b in model['stumps']:result+=np.where(X[:,int(j)]<=t,a,b)
    return float(result[0]) if single else result


def quality(row):
    fields=row['score']['fields']
    return float(np.mean([f['exact'] for f in fields])) if fields else None


def combined_cost(rows,policies,kind='wall'):
    chosen=[rows[p] for p in dict.fromkeys(policies)];unique={r['raster_sha256']:r for r in chosen if r['raster_sha256']}
    # Unique OCR stages; shared fastvit localization charged once, LCNet once.
    wall=sum(r['ocr_'+kind] for r in unique.values())+sum(r['transform_'+kind]+r['semantic_map_'+kind] for r in chosen)
    wall+=max((r['localize_'+kind] for r in chosen if r['policy'] in ('strict','completion','bbox')),default=0.)
    wall+=max((r['localize_'+kind] for r in chosen if r['policy']=='lcnet'),default=0.)
    if 'text_deskew' in policies and rows['text_deskew']['probe_wall'] and rows['raw']['raster_sha256'] not in unique:
        wall+=rows['raw']['ocr_'+kind]
    return wall


def cascade_input(base,policy):return list(base['features'])+[float(policy==p) for p in FALLBACKS]


def cascade_decision(model,base_features):
    options=[]
    for p in FALLBACKS:
        f=list(base_features)+[float(p==q) for q in FALLBACKS]
        gain=predict(model['regressor'],f)-.002*model['expected_fallback_wall'][p]
        options.append((gain,p))
    gain,policy=max(options)
    return policy if gain>.02 else None


def choose(rows,method,models):
    if method=='fixed_completion':return 'completion',rows['completion']['total_wall']
    if method=='max_confidence':
        p=max((p for p in POLICIES if rows[p]['routed']),key=lambda p:(rows[p]['features'][6],-POLICIES.index(p)))
        return p,combined_cost(rows,POLICIES)
    if method.startswith('allviews_'):
        m=models[method];p=max((p for p in POLICIES if rows[p]['routed']),key=lambda p:(predict(m['regressor'],rows[p]['features']),-POLICIES.index(p)))
        return p,combined_cost(rows,POLICIES)
    fallback=cascade_decision(models[method],rows['completion']['features'])
    if not fallback or rows[fallback]['raster_sha256']==rows['completion']['raster_sha256']:
        return 'completion',rows['completion']['total_wall']
    return fallback,combined_cost(rows,('completion',fallback))


def train_model(groups,kind,strength,mode):
    X=[];y=[]
    for group in groups:
        base=group['completion'];qbase=quality(base)
        if qbase is None:continue
        for p in POLICIES if mode=='allviews' else FALLBACKS:
            q=quality(group[p])
            if q is None:continue
            X.append(group[p]['features'] if mode=='allviews' else cascade_input(base,p))
            y.append(q if mode=='allviews' else q-qbase)
    if not X:raise ValueError('No development labels for selector')
    return dict(regressor=fit_regressor(X,y,kind,strength),
        expected_fallback_wall={p:float(np.mean([g[p]['total_wall'] for g in groups])) for p in FALLBACKS})


def fit_selectors(records,reader):
    dev=[record for record in records if record['role']=='development' and record['repeat']==1]
    if not dev:raise ValueError('Development-only training data required')
    if any(record['role']!='development' for record in dev):raise AssertionError('Leaked non-development labels')
    groups=[{r['policy']:r for r in record['rows'] if r['engine']==reader} for record in dev]
    ids=sorted({r['physical_id'] for r in dev});ordered=sorted(ids,key=lambda x:hashlib.sha256(('fold/'+x).encode()).digest())
    folds={identity:i%4 for i,identity in enumerate(ordered)};models={};audit=[]
    for mode in ('allviews','cascade'):
        for kind,strengths in (('ridge',(.1,1.,10.)),('stumps',(8,24))):
            method=mode+'_'+kind;best=None
            for strength in strengths:
                utilities=[];qualities=[];costs=[]
                for fold in range(4):
                    train=[g for g,r in zip(groups,dev) if folds[r['physical_id']]!=fold]
                    held=[g for g,r in zip(groups,dev) if folds[r['physical_id']]==fold]
                    m=train_model(train,kind,strength,mode)
                    for group in held:
                        p,cost=choose(group,method,{method:m});q=quality(group[p])
                        if q is not None:utilities.append(q-.002*cost);qualities.append(q);costs.append(cost)
                value=float(np.mean(utilities));audit.append(dict(reader=reader,method=method,strength=strength,
                    grouped_cv_utility=value,grouped_cv_exact=float(np.mean(qualities)),grouped_cv_estimated_wall=float(np.mean(costs))))
                if best is None or value>best[0]:best=(value,strength)
            models[method]=dict(train_model(groups,kind,best[1],mode),cv_utility=best[0],selected_strength=best[1])
    primary=max(('cascade_ridge','cascade_stumps'),key=lambda key:models[key]['cv_utility'])
    return dict(reader=reader,models=models,primary_method=primary,training_ids=ids,folds=folds,
                development_cases=len(dev),cv_candidates=audit,test_labels_used=False,
                primary_selection_rule='Best grouped-development CV utility among two cascades; not best test result')
