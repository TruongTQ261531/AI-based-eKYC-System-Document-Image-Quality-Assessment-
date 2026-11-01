"""Re-label exact R2 pixels using explicit source-realization graphs."""
import collections
import numpy as np
from research.v3_common import *
from research.v3_sources import source_graph,capture_geometry,visible_realizations
from research.v3_metrics import reference_precision

def mock_references(row):
    return {k:[dict(value=v,kind='body',source='authored_label_value',priority=0) for v in values] for k,values in row['accepted_values'].items()}

def derive():
    """Pure reference derivation, also replayed by the final audit."""
    rows=read(R2DATA/'samples.json');sources={r['physical_id']:r for r in read(R2DATA/'sources.json')}
    shapes={r['physical_id']:(r['height'],r['width']) for r in rows if r['capture']=='full'}
    graphs={};stats=collections.Counter()
    for pid,source in sources.items():
        graphs[pid],meta=source_graph(source);stats['mrz_present']+=meta['mrz_present'];stats['mrz_parsed']+=meta['mrz_parsed']
        if meta.get('mrz_parsed'):
            for key,value in meta['checks'].items():stats['valid_check/'+key]+=bool(value)
    result=[];changes=collections.Counter();manifest=[]
    for r in rows:
        if r['source']=='authored':refs=mock_references(r);evidence=[];masked={f['key'] for f in r['fields'] if f.get('occluded')}
        else:
            H,masks=capture_geometry(sources[r['physical_id']],r,shapes[r['physical_id']])
            refs,evidence,masked=visible_realizations(graphs[r['physical_id']],H,masks,r['width'],r['height'])
        # Preserve the maximum explicit date precision when available, then
        # prefer body/native references. No date century is inferred.
        target={}
        for key,values in refs.items():
            ordered=sorted(values,key=lambda ref:(-reference_precision(ref) if key in ('dob','expiry_date','issue_date') else 0,ref['priority']))
            target[key]=ordered[0]['value']
        sample=dict(r,body_target=r['target'],target=target,source_refs=refs,source_evidence=evidence,masked_keys=sorted(masked))
        result.append(sample)
        changed=target!=r['target'];new_keys=len(set(target)-set(r['target']));lost_keys=len(set(r['target'])-set(target))
        changes[r['role']+'/changed_targets']+=changed;changes[r['role']+'/new_supported_keys']+=new_keys;changes[r['role']+'/lost_body_keys']+=lost_keys
        manifest.append({k:v for k,v in sample.items() if k not in ('fields','path','target','body_target','accepted_values','source_refs','source_evidence','masked_keys')})
    if any(a['input_sha256']!=b['input_sha256'] or a['uid']!=b['uid'] for a,b in zip(rows,result)):raise ValueError('R3 changed image inputs')
    return result,manifest,dict(stats),dict(changes)

def build():
    preserve_v1()
    result,manifest,stats,changes=derive()
    save(DATA/'samples.json',result);save(OUT/'dataset_manifest.json',manifest)
    save(OUT/'dataset_card.json',dict(samples_sha256=sha(DATA/'samples.json'),r2_samples_sha256=sha(R2DATA/'samples.json'),
        exact_same_pixels=True,reference_policy_only_intervention=True,rows=len(result),train_images=640,
        source_stats=stats,target_changes=changes,test_images=144,test_identities=48,
        date_policy='Maximum explicitly observed precision as training target; accept observed source realizations; separately score max precision and century overreach',
        visibility='OR over body/duplicate/TD3 realizations, AND over actual component regions; synthetic-mask geometry only',
        parsed_mrz_does_not_imply_authenticity=True,independent_human_legibility_labels=False,
        source_contract='Explicit author-labelled fields and format-recognized ICAO TD3 spans; not every inferable or encoded fact'))
    print('V3_REFERENCE_DATA_READY',len(result),dict(changes),flush=True)

if __name__=='__main__':build()
