"""Final release audit: source/protected hashes, evidence counts and document links.

This is artifact verification, not another efficacy experiment or human review.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

from research.evidence_contract.reviewer_tools.strict import loads, need
from research.evidence_contract.task55.data import EC, ROOT, save_new
from research.evidence_contract.oracle_reliability import reference_registry
from research.evidence_contract.oracle_reliability.verify_reporting_v2 import verify

HERE=Path(__file__).resolve().parent
PRIVATE=EC/'local/master_01/oracle_reliability_20261116/continuation_20261116_2347'
BASE='0f40f5e014b1065d86c10ad453ed23e2db17ac34'
TOOLING='ace4628cc3c8b909b7a327a0eda48ff0410b4db8'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)


def run():
    protected=loads((PRIVATE/'protected_before.json').read_bytes(),max_bytes=5000000)
    need(all((EC/p).is_file() and sha((EC/p).read_bytes())==expected for p,expected in protected.items()),'Frozen evidence changed')
    logs=0
    for path in HERE.glob('*.json'):
        value=loads(path.read_bytes(),max_bytes=10000000)
        if isinstance(value,dict) and 'stdout_stderr_sha256' in value:
            need(sha((HERE/value['log']).read_bytes())==value['stdout_stderr_sha256'],'Log changed: '+path.name);logs+=1
    tests=loads((HERE/'full_tests_01.json').read_bytes())
    need(tests['exit_code']==0 and tests['counts']==dict(passed=411,failed=0,skipped=0,deselected=0) and tests['subtests_passed']==6,'Final test counts')
    config=reference_registry.production_trust()
    need(not config['authorities'] and config['owner_protocol_approval_sha256'] is None and config['expected_journal_head_sha256'] is None,'Unauthorized production setup')
    need(not reference_registry.approved_ids(),'Unexpected approval')
    exposure=loads((HERE/'feasibility_02/exposure_audit.json').read_bytes())
    need(exposure['files_scanned']==22861 and exposure['exposure_states']==dict(EXPOSED_CONFIRMED=192,EXPOSURE_UNKNOWN=808),'Exposure totals')
    c2=loads((HERE/'feasibility_02/c2_feasibility.json').read_bytes())
    need((c2['candidate_pairs'],c2['candidate_instances'],c2['eligible_pairs'])==(1100,400,0),'C2 totals')
    need(loads((HERE/'feasibility_01/c2_feasibility.json').read_bytes())==c2,'C2 audit changed unexpectedly')
    sizing=loads((HERE/'sizing_01/sizing.json').read_bytes(),max_bytes=5000000)
    need(sizing['scenario_count']==len(sizing['scenarios'])==384 and sizing['scientific_go'] is False,'Sizing scope')
    need(all(v is None or v is False for v in sizing['owner_decisions'].values()),'Owner decisions invented')
    metrics=verify(EC/'execution/master_01/oracle_reliability_20261116/run_02/aggregate_cells.json',HERE/'metrics_01/report.json')
    ledger=loads((EC/'paper/B_CLAIM_TO_EVIDENCE_20261117.json').read_bytes())
    required={'claim_id','wording','status','evidence_artifacts','sample_domain','independence','assumptions',
              'known_counterexample','allowed_section','forbidden_stronger_wording','upgrade_evidence'}
    need(len(ledger['claims'])==12 and ledger['independent_efficacy_claims']==0,'Claim totals')
    for claim in ledger['claims']:
        need(set(claim)==required and claim['status']!='SUPPORTED_INDEPENDENT','Claim fields/scope')
        for name in claim['evidence_artifacts']:need((EC/name).is_file(),'Missing claim artifact: '+name)
    changed=set(git('diff','--name-only',BASE).decode().splitlines())
    changed.update(git('ls-files','--others','--exclude-standard').decode().splitlines())
    need(not any('/local/' in p or p.endswith(('.zip','.png','.jpg','.safetensors','.bin')) for p in changed),'Private/binary artifact in delivery')
    source_count=0
    tooling_files=git('diff','--name-only',BASE,TOOLING).decode().splitlines()
    for name in tooling_files:
        if name.endswith(('.py','.json','.txt')) and ('/execution/' not in name):
            need(git('show',TOOLING+':'+name)==(ROOT/name).read_bytes(),'Code/config changed after tested tooling commit')
            source_count+=1
    links=0
    for name in changed:
        if not name.endswith('.md'):continue
        path=ROOT/name
        for target in re.findall(r'(?<!!)\[[^\]\n]+\]\(([^)\n]+)\)',path.read_text(encoding='utf-8')):
            target=target.strip().strip('<>')
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:',target) or target.startswith('#'):continue
            target=unquote(target.split('#',1)[0])
            if target:
                need((path.parent/target).exists(),'Missing local link in '+name+': '+target);links+=1
    result=dict(status='PASS_RELEASE_AUDIT',protected_files_unchanged=len(protected),
        command_logs_hash_verified=logs,tested_code_config_files_unchanged=source_count,
        full_tests_passed=411,subtests_passed=6,claim_records_checked=12,local_links_checked=links,
        metrics=metrics,exposure=exposure['exposure_states'],c2_candidates=1100,c2_eligible=0,
        sizing_scenarios=384,production_authorities=0,production_approvals=0,
        scientific_state='GO_PREPARATORY_ONLY',confirmatory=False,new_model_calls=0,training_runs=0,
        artifacts={name:sha((ROOT/name).read_bytes()) for name in sorted(changed)},
        tooling_head=TOOLING,base_head=BASE,
        scope='File/count/link and arithmetic verification; no independent scientific truth or final Git push asserted')
    save_new(HERE/'final_release_check.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='artifacts'},indent=2))


if __name__=='__main__':run()
