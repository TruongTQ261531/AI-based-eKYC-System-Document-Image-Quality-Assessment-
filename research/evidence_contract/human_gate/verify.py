"""Independent reconciliation of the fixed human gate snapshot and its private packages."""
import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import subprocess

from ..oracle_reliability.reference_registry import approved_ids, production_trust
from ..reviewer_tools.strict import digest, need
from ..task55.data import EC, ROOT, read, save_new, sha
from .closure import BASE, PUBLIC, SOURCE, frozen
from .prepare import private_run
from .review import QUESTIONS

FOLDER=Path(__file__).parent
CODES=('R02','R03')


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms={}
        self.form=None
        self.assets=set()
        self.current_select=None

    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form':
            cid=a['data-candidate']
            need(cid not in self.forms and self.form is None and 'action' not in a,'Duplicate form or external action')
            self.form=dict(assessor=a['data-assessor'],item=a['data-item'],fields=[],cites={'before':[],'after':[]})
            self.forms[cid]=self.form
        if tag in ('img','a'):
            url=a['src' if tag=='img' else 'href']
            need(url.startswith('assets/') and Path(url).parent==Path('assets'),'Nonlocal image link')
            self.assets.add(url)
        if tag=='select':
            need(self.form is not None and 'required' in a,'Missing required answer')
            self.form['fields'].append(a['name'])
            self.current_select=0
        if tag=='option':
            need('selected' not in a and (self.current_select!=0 or a.get('value')==''),'Prefilled opinion')
            self.current_select+=1
        if tag=='input':
            need(a.get('type')=='checkbox' and 'checked' not in a,'Prefilled citation')
            self.form['cites'][a['data-side']].append(a['value'])
        if tag=='textarea':
            need('required' in a,'Missing rationale')
            self.form['fields'].append(a['name'])

    def handle_endtag(self,tag):
        if tag=='form':
            self.form=None
        if tag=='select':
            self.current_select=None


def check_group(g,rows,selected):
    def count(part):
        return dict(candidates=len(part),physical_ids=len({r['physical_instance'] for r in part}))
    none=count([])
    issued=[r for r in rows if r['candidate_id'] in selected]
    need(g['scope']==g['missing_d10']==g['semantic_approval_missing']==g['without_any_proposals']==count(rows),'Missing evidence denominators')
    need(g['prepared']==g['waiting_both_prepared']==count(issued),'Review denominator')
    for key in ('adjudicated','approved','shareable','two_proposals','waiting_one','observations_received','eligible'):
        need(g[key]==none,'Unauthorized promotion')
    for col in rows[0]['conditions']:
        need(g['conditions'][col]=={s:count([r for r in rows if r['conditions'][col]==s])
                                    for s in ('PASS','FAIL','UNKNOWN')},'Eight-condition arithmetic')


def verify(dest):
    draft,_=frozen()
    a=read(dest/'aggregate.json')
    baseline=read(PUBLIC/'aggregate.json')['c2']
    ledger=SOURCE/'qualification/evidence.json'
    need(sha(ledger)==baseline['candidate_evidence_sha256']==a['checks']['source_ledger'],'Frozen evidence ledger')
    e=read(ledger)
    eligible=[r for r in e['candidates'] if any(
        all(v==(1 if k==r['primary'] else 0) for k,v in option['impact'].items()) for option in r['paired'])]
    selected={r['candidate_id'] for r in eligible}
    queue=read(dest/'queue.json')
    by_id={i['candidate_id']:i for i in queue}
    need(len(queue)==len(selected)==45 and set(by_id)==selected and
         len({r['physical_instance'] for r in eligible})==24,'Exact eligible geometry membership')
    need(sha(dest/'queue.json')==a['queue_sha256'],'Private queue binding')
    incoming=read(SOURCE/'organizer_queue.json')
    need(sha(SOURCE/'organizer_queue.json')==a['checks']['organizer_queue_sha256'] and
         [len(incoming['phase1']),len(incoming['phase2']),sum(len(i['coherence_flags']) for i in incoming['coherence'])]==
         [a['checks']['phase1_queue'],a['checks']['phase2_queue'],a['checks']['coherence_flags']],'Queue preservation')
    need(not production_trust()['authorities'] and not approved_ids() and not (dest/'signed_round1.json').exists()
         and digest(draft)==a['closure']['pending_digest'] and a['closure']['signed_records']==0,'Unsigned production baseline')
    families={k:set() for k in ('provider_annotations','original_frames','derived_frames','region_crops','review_workspaces')}
    for r in eligible:
        item=by_id[r['candidate_id']]
        edge=e['physical_instances'][r['physical_instance']]['edges'][r['best']['edge']]
        need(item['physical_id']==r['physical_instance'] and item['field']==r['field'] and
             item['primary_source']==r['primary'] and item['backup_source']==r['backup'] and
             item['impact']==r['best']['impact'] and item['transform']==edge['transform'],'Wrong candidate or mutation')
        need(not item['proposed_mapping']['human_approved'] and len(item['regions'])==6,'Semantic status or missing region')
        for side,k,asset in [('before','source_sha256','original_frames'),('after','input_sha256','derived_frames')]:
            need(item['full'][side]==dict(file=edge[k],pixel=edge[side+'_pixel']),'Source image mismatch')
            families[asset].add(edge[k])
        for issued,old in zip(item['regions'],r['inspection']):
            need(all(issued[k]==v for k,v in old.items() if k!='crop'),'Source polygon, crop or absence mismatch')
            if 'sha256' in old:
                families['region_crops'].add(old['sha256'])
        families['provider_annotations'].add(item['template_sha256'])
    expected_answers=set(QUESTIONS)|{'semantic_judgment','precision_judgment','exposure','rationale'}
    for code in CODES:
        root=dest/code
        manifest=read(dest/(code+'_manifest.json'))
        need(set(manifest)=={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()},'Missing or extra files')
        for rel,h in manifest.items():
            need(sha(root/rel)==h,'Package bytes')
            if rel!='index.html':
                need(Path(rel).stem==h,'Content-addressed assets')
        page=Page()
        html=(root/'index.html').read_text(encoding='utf8')
        page.feed(html)
        need(page.forms.keys()==selected and page.assets==set(manifest)-{'index.html'},'Incomplete package')
        for cid,form in page.forms.items():
            item=by_id[cid]
            need(form['assessor']==code and form['item']==digest(item) and set(form['fields'])==expected_answers
                 and len(form['fields'])==len(expected_answers) and form['cites']==item['evidence_by_side'],'Assessor form binding')
        need(CODES[1-CODES.index(code)] not in html and 'https://' not in html,'Assessor isolation or network reference')
        need(digest(manifest)==a['package_sha256'][code],'Package receipt')
        families['review_workspaces'].add(digest(manifest))
    rights=read(dest/'artifact_rights.json')
    need(sha(dest/'artifact_rights.json')==a['rights_file_sha256'] and {r['artifact'] for r in rights}==set(families),'Rights manifest')
    for r,entry in zip(rights,a['rights'],strict=True):
        family=families[r['artifact']]
        need(set(r['members'])==family and digest(sorted(family))==r['version_digest']
             and entry=={k:v for k,v in r.items() if k!='members'}|dict(unique_members=len(family)),'Versioned rights set')
        need(r['authority_of_record'] is None and r['decisions']['assessor_sharing']=='REVIEW_ACCESS_PENDING','Rights disposition')
    check_group(a['selected'],eligible,selected)
    check_group(a['all_priority'],e['candidates'],selected)
    rest=[r for r in e['candidates'] if r['candidate_id'] not in selected]
    affected=sum(any(o['impact'][r['primary']]>0 for o in r['paired']) for r in rest)
    need(a['deferred']==dict(candidates=len(rest),physical_ids=len({r['physical_instance'] for r in rest}),
                             primary_touched=affected,primary_untouched=len(rest)-affected),'Deferred group')
    need(a['source_precision']==dict(Counter(i['source_precision']['body'] for i in queue)),'Precision count')
    tests={}
    for suite in ('targeted','full'):
        receipt=read(dest/(suite+'_tests.json'))
        need(receipt['exit_code']==0 and sha(dest/(suite+'.log'))==receipt['log_sha256'],'Regression receipt')
        tests[suite]=sha(dest/(suite+'_tests.json'))
    protected=read(EC/'execution/master_01/p2_20261120/baseline.json')['protected_files']
    for path,h in protected.items():
        need(sha(ROOT/path)==h,'Protected P2 bytes')
    historical=subprocess.check_output(['git','diff','--name-only','--diff-filter=DMRT',BASE,'--',
        'research/evidence_contract/execution','research/evidence_contract/oracle_reliability',
        'research/evidence_contract/adjudication'],cwd=ROOT)
    need(not historical.strip(),'Frozen code or receipt changed')
    return dict(status='VERIFIED_TECHNICAL',aggregate_sha256=sha(dest/'aggregate.json'),test_receipts=tests,
        original_submissions=6,view_hashes=3,protected_p2_files=len(protected),verified_participant_forms=2*len(queue),
        private_return_files_in_issued_packages=0,production_reference_approvals=0,
        private_package_manifests_checked=2,rights_versions_checked=len(rights),prior_inputs=a['checks'])


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('run')
    args=p.parse_args()
    dest=private_run(args.run)
    result=verify(dest)
    path=dest/'verification.json'
    if path.exists():
        need(result==read(path),'Receipt mismatch')
    else:
        save_new(path,result)
    print(result['status'])
