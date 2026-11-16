"""Fresh-directory controls and historical replay; no predictor invocation."""
from copy import deepcopy
from pathlib import Path
import argparse
import json

from ..task55.data import EC,ROOT,FrozenPilot,digest,read,save_new,sha
from ..task55 import ifv
from ..task55.ifv_sampling import SAMPLE
from ..master.ifv_analysis import from_sealed
from ..master import reference_policy as v1
from . import policy as p
from .controls import make_controls,inputs
from .reporting import cells_from_rows,report

OUT=EC/'execution/master_01/oracle_reliability_20261116'
PRIVATE=EC/'local/master_01/oracle_reliability_20261116'
LABELS={'CONFIRMED_FAULT':True,'NO_FAULT':False}


def v1_projection(case):
    """Explicitly diagnostic projection: legacy MRZ flags are asserted, not recomputed."""
    ref,ctx,before,after=inputs(case);payload=deepcopy(case['reference_payload'])
    payload.pop('main_source_id');payload.update(schema=v1.SCHEMA,policy=v1.POLICY)
    for side in ('before','after'):
        for source in payload[side]['sources']:
            source.pop('mrz');source['conditions'].pop('context_present')
            if source['kind']=='mrz':source['conditions'].update(format_valid=True,field_checksum=True,composite_checksum=True)
    result=v1.evaluate(v1.seal_reference(payload),ctx,before,after)
    mapping={'PASS':'NO_FAULT','CANDIDATE_VIOLATION':'FAULT','INCONCLUSIVE':'UNKNOWN','INVALID_TEST':'INVALID_TEST'}
    return {endpoint:mapping[result[endpoint]['verdict']] for endpoint in ('pointwise','relation')}


def control_rows():
    records=[];rows=[];seen=set()
    for case in make_controls():
        args=inputs(case);methods={}
        for tier in (1,2):
            for flat in (False,True):
                name=('flat' if flat else 'B')+'_tier'+str(tier)
                result=p.evaluate(*args,minimum_grade=tier,flat=flat)
                methods[name]={e:result[e] for e in p.ENDPOINTS}
        expected=case['expected'];observed=[methods['B_tier1'][e]['state'] for e in p.ENDPOINTS]
        if observed!=expected:raise ValueError('Control expectation failed: '+case['name'])
        identity=digest({k:v for k,v in case.items() if k not in {'name','expected','truth'}})
        if identity in seen:raise ValueError('Duplicate symbolic control; declare aliases before evaluation')
        seen.add(identity)
        rows.append(dict(dataset='symbolic_controls',partition='development',contract=case['context']['contract'],cluster='symbolic_not_physical',
                         truth=dict(zip(p.ENDPOINTS,case['truth'])),methods=methods,comparison_id=identity))
        record=dict(case,comparison_id=identity,methods=methods,expected_matches_observed=True,origin='oracle_unit_injected',physical_ids=0)
        if case['name'] in {'C2_main_not_removed','TD3_bad_checksum','source_unresolved','invalid_or_ambiguous_date_000229'}:
            record['legacy_v1_projection']=v1_projection(case)
        records.append(record)
    return records,rows


def pilot_rows():
    pilot=FrozenPilot();sample=read(SAMPLE);ifv.bound_manifest(sample,'sample_id')
    snapshot='812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d'
    folder=ifv.STAGE2/'d7598ae874d735869d2505c30ac9f7348691c2450af2a70d45666f8b3293c223'
    submission=folder/'submissions'/snapshot/'output_observations.json'
    _,details=from_sealed(submission)
    labels=read(submission.parent/'labels.json');links=read(ifv.JOINS/(folder.name+'.json'))
    packet=read(folder/'packet.json');packet_cases={c['case_id']:c for c in packet['cases']}
    flagged={c['case_id'] for c in details if c['coherence_flags']}
    all_ids=sorted({v['row']['physical_id_sha256'] for v in links.values()});clusters={key:'cluster_'+str(i+1) for i,key in enumerate(all_ids)}
    state_map={'PASS':'NO_FAULT','CANDIDATE_VIOLATION':'FAULT','INCONCLUSIVE':'UNKNOWN','INVALID_TEST':'INVALID_TEST'}
    rows=[]
    for case_id,link in sorted(links.items()):
        row=link['row'];after=pilot.outputs[row['reader'],row['followup_pixel_sha256']]
        before=pilot.outputs[row['reader'],row['original_pixel_sha256']]
        case=packet_cases[case_id]
        ctx=p.PairContext(row['contract_id'],row['field_key'],row['original_pixel_sha256'],row['followup_pixel_sha256'],
                          digest(['historical_gate_probe',link['identity_sha256']]),row['validity'],'unassessed')
        # No conversion of reviewer observations into an approved reference.
        gated=p.evaluate(None,ctx,before,after)
        methods={}
        for name in ('A','A_flat','B3','B0','B2'):
            original=row['checks'][name];state=state_map[original['verdict']]
            methods[name]={e:p.decision(state,'frozen_'+original['verdict']) for e in ('pointwise','relation')}
        methods['shared_structure_checker']={'structure':dict(gated['structure'])}
        methods['B_reference_gate']={e:gated[e] for e in p.ENDPOINTS}
        structure_truth=not case['after_output']['structured_output_usable']
        for sensitivity in ('original','withhold_literal_flags'):
            truth={e:LABELS.get(labels[case_id][e]) if sensitivity=='original' or case_id not in flagged else None for e in ('pointwise','relation')}
            truth['structure']=structure_truth
            rows.append(dict(dataset='historical_actual_model_'+sensitivity,partition='primary' if row['stratum']=='primary' else 'diagnostic',
                             contract=row['contract_id'],cluster=clusters[row['physical_id_sha256']],truth=truth,methods=deepcopy(methods),
                             comparison_id=link['identity_sha256'],reader=row['reader']))
    pilot.assert_read_only()
    return rows,dict(review_comparisons=len(links),primary_comparisons=sum(v['row']['stratum']=='primary' for v in links.values()),
                     primary_physical_ids=len({v['row']['physical_id_sha256'] for v in links.values() if v['row']['stratum']=='primary'}),
                     actual_cached_outputs=len(pilot.outputs),source_human_phase2_sha256=sha(submission),
                     source_sample_sha256=sha(SAMPLE),label_status='One-author unadjudicated; structure is normalized-parser status, not a human label')


def run(destination):
    destination=Path(destination).resolve()
    if not destination.is_relative_to(OUT.resolve()) or destination.exists():raise ValueError('Use a fresh run under the B checkpoint')
    records,controls=control_rows();historical,history=pilot_rows()
    rows=controls+historical;cells=cells_from_rows(rows);result=report(cells)
    for case in records:
        for tier in (1,2):
            if any(case['methods']['B_tier'+str(tier)][e]['state']!=case['methods']['flat_tier'+str(tier)][e]['state'] for e in p.ENDPOINTS):
                raise ValueError('Matched-information parity failed')
    source_files=['oracle_reliability/policy.py','oracle_reliability/controls.py','oracle_reliability/reporting.py','oracle_reliability/run.py',
                  'master/reference_policy.py','master/ifv_analysis.py','normalized_output.py']
    save_new(PRIVATE/(destination.name+'_historical_rows.json'),historical)
    save_new(destination/'control_cases.json',records);save_new(destination/'aggregate_cells.json',cells)
    save_new(destination/'results.json',dict(schema='oracle-reliability-results/1',scope='DEVELOPMENT_ONLY',
        control_cases=len(controls),symbolic_physical_ids=0,symbolic_pixel_hash_pairs=1,history=history,model_calls=0,training_runs=0,
        human_annotations_created=0,independent_reference_approved=False,confirmatory=False,scientific_gate='NO_GO_SUPERIORITY',
        risk_coverage_meaning='Two declared evidence-tier operating points, not a calibrated confidence curve; zero decisions implies risk NA',
        bound_flat_state_parity=True,results=result))
    save_new(destination/'manifest.json',dict(files={name:sha(destination/name) for name in ('control_cases.json','aggregate_cells.json','results.json')},
        sources={name:sha(EC/name) for name in source_files},plan_sha256=sha(OUT/'development_plan.json')))
    return dict(status='DEVELOPMENT_COMPLETE',controls=len(controls),history=history,model_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(run(args.destination),indent=2))
