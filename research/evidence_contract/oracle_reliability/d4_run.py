"""Execute the declared D4 development controls; no reader/model is called."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
from time import perf_counter_ns,process_time_ns

from . import policy,reporting,reporting_v2
from .d4_controls import cases,inputs
from .mrz_ablation_v1 import compare_pair,adapter_proof,verify_frozen_source
from ..task55.data import EC,save_new,sha,digest


def run(output):
    output=Path(output).resolve()
    if not output.is_relative_to((EC/'execution').resolve()) or output.exists():raise ValueError('Fresh execution path required')
    verify_frozen_source();spec=cases();save_new(output/'expected_controls.json',spec)
    records=[];rows=[];divergences=[];started=perf_counter_ns();cpu=process_time_ns()
    for case in spec:
        start=perf_counter_ns();args=inputs(case);normalization_ns=perf_counter_ns()-start
        ref,ctx,before,after=args
        payload=dict(reference=ref,context=asdict(ctx),before=asdict(before),after=asdict(after))
        panels={}
        for tier in (1,2):
            start=perf_counter_ns();result=compare_pair(*args,minimum_grade=tier);pair_ns=perf_counter_ns()-start
            result['cost'].update(pair_total_ns=pair_ns,input_normalization_ns_shared=normalization_ns)
            expected=case['expected_by_tier'][str(tier)]
            for arm,value in result['arms'].items():
                if [value[e]['state'] for e in policy.ENDPOINTS]!=expected[arm]:raise ValueError('Expected/actual mismatch: '+case['name'])
            if result['arms']['checked_v2']!=policy.evaluate(*args,minimum_grade=tier):raise ValueError('Frozen checked regression')
            differing=[e for e in policy.ENDPOINTS if result['arms']['checked_v2'][e]!=result['arms']['mrz_metadata_asserted'][e]]
            if differing:
                if case['family']!='literal_mrz_intervention':raise ValueError('Divergence outside MRZ treatment')
                divergences.append(dict(name=case['name'],tier=tier,endpoints=differing,
                    checked_reasons={e:result['arms']['checked_v2'][e]['reason'] for e in differing},
                    asserted_reasons={e:result['arms']['mrz_metadata_asserted'][e]['reason'] for e in differing},
                    treatment='Literal TD3 verification omitted; same typed profile, declared tier and shared guards',
                    shared_input_sha256=result['shared_input_sha256']))
            panels[str(tier)]=result
            rows.append(dict(dataset='constructed_D4_tier'+str(tier),partition=case['family'],
                contract=ctx.contract,cluster='symbolic_not_physical',truth=dict(zip(policy.ENDPOINTS,case['truth'])),
                methods={arm:{e:value[e] for e in policy.ENDPOINTS} for arm,value in result['arms'].items()}))
        records.append(dict(name=case['name'],family=case['family'],shared_input=payload,panels=panels,
                            truth=case['truth'],expected=case['expected_by_tier'],physical_ids=0))
    cells=reporting.cells_from_rows(rows);save_new(output/'control_results.json',records)
    save_new(output/'aggregate_cells.json',cells)
    groups=reporting_v2.report(cells)
    save_new(output/'accounting.json',dict(schema='oracle-accounting-supplement/2',input_sha256=sha(output/'aggregate_cells.json'),
        source_cells=len(cells),metric_groups=len(groups),groups=groups,confirmatory=False,new_observations=0,
        model_calls=0,training_runs=0,labels_changed=0,scope='Authored symbolic controls; not an empirical cohort'))
    save_new(output/'divergences.json',divergences)
    matrix=[dict(guard=g,checked='shared frozen admission/resolver',asserted='shared frozen admission/resolver') for g in
        ('authority','image_field_mutation_binding','output_origin','parser_usability','typed_value_and_precision_profile',
         'semantic_key','source_flags','conflicting_values','missing_support','C1_inventory','C2_transition','transformation_validity','tier')]
    matrix.append(dict(guard='literal_TD3_format_dates_checksums_value_consistency',checked='recomputed',asserted='not recomputed'))
    save_new(output/'guard_matrix.json',dict(adapter_proof=adapter_proof(),guards=matrix,
        note='Same field/precision support profiles; no century inference. Legacy reason strings retained, actual literal-call counts disambiguate arm behavior.'))
    valid_names={'TD3_id_number','TD3_dob','TD3_expiry_date','valid_MRZ_correct_output'}
    costs={arm:{key:sum(p['cost']['arms'][arm][key] for r in records for p in r['panels'].values())
                 for key in ('literal_td3_calls','declared_mrz_resolutions','mrz_work_ns','evaluation_ns')}
           for arm in ('checked_v2','mrz_metadata_asserted')}
    summary=dict(schema='D4-development-results/1',status='PASS_CONSTRUCTED_DEVELOPMENT',controls=len(records),tiers=[1,2],
        paired_evaluations=2*len(records),arm_evaluations=4*len(records),endpoints=3,
        valid_MRZ_parity_cases=sorted(valid_names),valid_MRZ_parity_tier_pairs=2*len(valid_names),
        divergence_tier_pairs=len(divergences),divergence_unique_controls=len({d['name'] for d in divergences}),
        non_treatment_divergences=0,frozen_checked_exact_regressions=2*len(records),
        symbolic_physical_ids=0,actual_new_observations=0,model_calls=0,training_runs=0,human_annotations_created=0,
        human_active_minutes=None,annotation_budget_shared=True,reference_approvals_created=0,
        prospective_started=False,scientific_gate='NO_GO_SUPERIORITY',costs=costs,
        runtime_ns=perf_counter_ns()-started,process_cpu_ns=process_time_ns()-cpu,
        cost_scope='One warm-process execution per arm/tier/control; validation/predicate timers are local software observations, no end-to-end eKYC or human cost claim',
        counterexamples=['shared_wrong_reference','corroborated_shared_wrong_reference','correlated_wrong_body_and_valid_MRZ'],
        withheld_truth='Truth is evaluation-only authored control data; never passed to compare_pair')
    save_new(output/'summary.json',summary)
    lines=['# D4 expected versus actual — constructed controls','','No independent IDs or model calls. C/P/R columns are pointwise/relation/structure.','',
           '| Case | Tier | Checked expected = actual | Asserted expected = actual |','|---|---:|---|---|']
    for r in records:
        for tier,p in r['panels'].items():
            lines.append('| '+r['name']+' | '+tier+' | '+' / '.join(r['expected'][tier]['checked_v2'])+' | '+' / '.join(r['expected'][tier]['mrz_metadata_asserted'])+' |')
    (output/'expected_vs_actual.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    source_names=['policy.py','controls.py','d4_controls.py','mrz_ablation_v1.py','d4_run.py','reporting.py','reporting_v2.py','reference_registry.py','production_trust.json']
    save_new(output/'manifest.json',dict(files={p.name:sha(p) for p in output.iterdir() if p.is_file()},
        sources={name:sha(Path(__file__).parent/name) for name in source_names},source_spec_sha256=digest(spec)))
    verify_frozen_source()
    return {k:summary[k] for k in ('status','controls','paired_evaluations','divergence_unique_controls','divergence_tier_pairs','non_treatment_divergences','model_calls')}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    print(json.dumps(run(p.parse_args().output),indent=2))
