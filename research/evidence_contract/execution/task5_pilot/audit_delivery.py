"""TASK5 delivery checks: no OCR/VLM invocation and no historical writes."""
import argparse
import ast
from collections import Counter
from pathlib import Path
import re

from research.evidence_contract.task5.pilot import EC,ROOT,READERS,paths,read,verify_lock,readonly_cached
from research.evidence_contract.runner import InputRequest,Runner,sha_file,write_once
from research.evidence_contract.normalized_output import ReaderSpec
from research.evidence_contract.source_graph import digest

parser=argparse.ArgumentParser();parser.add_argument('--run',default='pilot_01');parser.add_argument('--score',default='evaluation_01')
args=parser.parse_args();local,public=paths(args.run);out=EC/'execution/task5_pilot'
lock=verify_lock(local,public)
tests=read(out/'regression_tests_02.execution.json')
assert tests['exit_code']==tests['failures']==tests['errors']==tests['skipped']==0
assert tests['code_unchanged_during_tests'] and tests['actual_model_invocations']==0
for path,checksum in tests['code_sha256'].items():assert sha_file(ROOT/path)==checksum,path
for path in (EC/'task5').glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
inputs=[InputRequest(**r) for r in read(local/'inputs.json')['inputs']]
assert set(read(local/'inputs.json'))=={'schema','inputs'}
assert len(inputs)==31 and all(r.role in ('fixture','development') and r.data_policy=='fictional' for r in inputs)
for request in inputs:request.load()
prep=read(public/'preparation.json');assert prep['selected_pair_counts']==dict(A=20,B1=20,shared_diagnostic=4)
assert prep['selected_validity']==dict(VALID=40,INVALID_TEST=2,INCONCLUSIVE=2)
assert prep['pool_proposals']==prep['admissible_candidates']==63
for seed in prep['seeds']:
    a=[r for r in prep['selection'] if r['arm']=='A' and r['seed']==seed]
    b=[r for r in prep['selection'] if r['arm']=='B1' and r['seed']==seed]
    assert len(a)==len(b)==7
    for x,y in zip(a,b):
        for key in ('case','family','area_bin','domain_sha256','domain_size'):assert x[key]==y[key]

readers=[];total_new=total_history=0;cache_calls=set()
for reader in READERS:
    fresh,resume,replay=[read(public/(mode+'_'+reader+'.json')) for mode in ('fresh','resume','replay')]
    spec=ReaderSpec(**fresh['reader']);assert fresh['reader']==resume['reader']==replay['reader']
    assert len(fresh['outputs'])==len(resume['outputs'])==len(replay['outputs'])==31
    assert resume['new_inference_calls']==replay['new_inference_calls']==0
    assert resume['new_model_loads']==replay['new_model_loads']==0
    assert fresh['new_model_loads']==1
    assert fresh['historical_log_unchanged'] and resume['historical_log_unchanged'] and replay['historical_log_unchanged']
    for mode in (resume,replay):
        by_pixel={r['input_pixel_sha256']:r for r in mode['outputs']}
        for row in fresh['outputs']:
            other=by_pixel[row['input_pixel_sha256']]
            for key in ('call_id','cache_key','reader_fingerprint','model_sha256','config_sha256','inference_code_sha256',
                        'runtime_sha256','input_file_sha256','input_pixel_sha256','latency_seconds','cpu_seconds'):
                assert row[key]==other[key],(reader,key)
    runner=Runner(spec,local/reader);old=Runner(spec,EC/'local/smoke_02'/reader)
    events=runner.events.read();begins=[e for e in events if e['event']=='inference_begin']
    complete=[e for e in events if e['event']=='inference_completed']
    assert len(begins)==len(complete)==fresh['new_inference_calls']
    assert not any(e['event'] in ('inference_failed','inference_recovered') for e in events)
    assert sha_file(runner.events.path)==resume['event_log_sha256']==replay['event_log_sha256']
    old_anchor=read(EC/'execution/task4_runner/smoke_02/actual_events.json')[reader]
    assert sha_file(old.events.path)==old_anchor['log_sha256']==fresh['historical_event_log_sha256']
    ids=set()
    for request in inputs:
        value=readonly_cached(runner,request) or readonly_cached(old,request)
        assert value is not None and value.output_origin=='actual_model'
        assert value.confidence is None and value.missing_fields is None
        ids.add(value.call_id);cache_calls.add(value.call_id)
    assert len(ids)==31
    history=sum(r['provenance']=='TASK4_read_only_cache' for r in fresh['provenance'])
    total_new+=len(begins);total_history+=history
    readers.append(dict(reader=reader,new_calls=len(begins),history_uses=history,resume_new_calls=0,replay_new_calls=0,
        old_event_log_unchanged=True,new_cache_integrity_verified=True))
assert total_new<=lock['actual_call_cap'] and total_new+total_history==93

evaluation=read(public/(args.score+'.json'));replayed=read(public/('evaluation_replayed.json'))
assert evaluation['semantic_payload_sha256']==replayed['semantic_payload_sha256']
assert read(public/(args.score+'.checks.json'))==read(public/'evaluation_replayed.checks.json')
assert evaluation['new_calls_during_scoring']==replayed['new_calls_during_scoring']==0
assert evaluation['all_inference_logs_unchanged_by_scoring']
assert evaluation['new_actual_model_calls']==total_new and evaluation['historical_cache_uses']==total_history
assert evaluation['synthetic_output_injections_in_real_model_results']==0
assert evaluation['confirmed_real_model_failures']==evaluation['confirmed_software_defects']==0
rows=read(public/(args.score+'.checks.json'))['rows']
assert len(rows)==132 and all(r['output_origin']=='actual_model' for r in rows)
assert Counter(r['arm'] for r in rows)==dict(A=60,B1=60,shared_diagnostic=12)
for arm in ('A','B1'):
    assert evaluation['per_arm_charged_costs'][arm]['logical_requests']==60
    for method in ('A','B0','B2','B3','B3_V3','B3_V3_gate','A_flat','A_no_alternative','A_no_validator','A_no_NI'):
        value=evaluation['primary'][arm][method]
        assert value['scheduled_contract_key_evaluations']==60
        assert value['confirmed_violations']==value['independent_gold_labels']==0
        assert value['false_alarms'] is None and value['false_alarm_rate']['value'] is None
    assert evaluation['comparisons'][arm]['A_alarm_not_B3']==0
    assert evaluation['comparisons'][arm]['A_flat_verdict_agreement']['value']==1.
audit=read(out/'preservation_final.json')
assert not audit['changed_preexisting_paths'] and audit['head_and_refs_unchanged']
assert not audit['tracked_diff'] and not audit['staged_diff']

documents=[]
for name in ('BASELINE_PROTOCOL.md','ABLATION_PLAN.md','DEVELOPMENT_PILOT.md','GO_NO_GO_REVIEW.md'):
    path=EC/name;text=path.read_text(encoding='utf-8');assert '\ufffd' not in text
    broken=[]
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if link.startswith(('https://','http://','#')):continue
        target=(EC/link.split('#')[0]).resolve()
        if not target.is_file() and target!=(out/'final_checks.json').resolve():broken.append(link)
    assert not broken,(name,broken)
    documents.append(dict(name=name,sha256=sha_file(path),broken_links=broken))

result=dict(all_checks_passed=True,head=audit['head'],preserved_files=audit['checked_files'],old_changed_files=0,
    junit_cases_including_subtests=tests['junit_cases_including_subtests'],readers=readers,
    new_actual_model_calls=total_new,historical_cache_uses=total_history,originating_outputs=93,
    scoring_new_calls=0,resume_new_calls=0,replay_new_calls=0,real_model_gold_labels=0,
    independent_verified_failures=0,matched_primary_pairs_per_arm=20,charged_requests_per_arm=60,
    A_exclusive_over_strong_B3=0,flat_oracle_equivalent_on_primary=True,
    semantic_scoring_replay_identical=True,documents=documents,code_sha256=lock['code_sha256'],
    verification_script_sha256=sha_file(__file__),no_training=True,no_checkpoint_or_production_changes=True,
    no_confirmatory_test=True,conclusion='NO-GO for scale/superiority claims; GO for bounded independent oracle/fault validity audit only')
write_once(out/'final_checks.json',result)
print(__import__('json').dumps(dict(all_checks_passed=True,new_actual_calls=total_new,history_uses=total_history,
    preserved_files=audit['checked_files'],matched_logical_requests_per_arm=60,A_exclusive_over_B3=0)))
