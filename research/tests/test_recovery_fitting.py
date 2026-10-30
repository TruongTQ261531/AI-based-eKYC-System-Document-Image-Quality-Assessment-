from research.recovery_runtime import POLICIES
from research.recovery_selection import fit_selectors,cascade_decision


def test_grouped_fitting_never_opens_test_outputs_and_learns_a_fallback():
    records=[]
    for i in range(8):
        rows=[]
        for policy in POLICIES:
            correct=4 if policy=='raw' else 1
            rows.append(dict(policy=policy,engine='rapid_latin_v5',routed=True,raster_sha256=policy,
                features=[1.,i/10]+[.5]*14+[float(policy==p) for p in POLICIES],
                score={'fields':[{'exact':j<correct} for j in range(5)]},total_wall=.2,
                ocr_wall=.1,transform_wall=.02,semantic_map_wall=.01,localize_wall=.03,probe_wall=0.))
        records.append(dict(role='development',repeat=1,physical_id='DEV'+str(i),rows=rows))
    # A canary with no rows: any attempt to use test outputs raises KeyError.
    records.append(dict(role='test',repeat=1,physical_id='SEALED_TEST'))
    fitted=fit_selectors(records,'rapid_latin_v5')
    assert fitted['training_ids']==['DEV'+str(i) for i in range(8)]
    assert not fitted['test_labels_used']
    method=fitted['primary_method'];base=next(r for r in records[0]['rows'] if r['policy']=='completion')
    assert cascade_decision(fitted['models'][method],base['features'])=='raw'
