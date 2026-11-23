"""Prepare the fixed rights-limited subset of the verified master queue."""
import argparse
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from ..oracle_reliability.reference_registry import production_trust
from ..reviewer_tools.strict import digest, need
from ..task55.data import EC, ROOT, read, save_new, sha
from .prepare import SOURCE_Q, cluster_metrics, private_run, write_packages
from .verify import verify as verify_master

MASTER = 'human_20261122144027Z'
BASELINE = '10177b1dc72dde35d98a943c92022c5416851744'
ACQUISITION = ROOT/'research/results/vlm_lora_v2/acquisition.json'
TYPE_CODES = {'aze_passport': '05', 'grc_passport': '25', 'lva_passport': '32', 'srb_passport': '41'}


def partition(queue, sources):
    """Join by exact provider physical ID AND original byte hash, then filter by type."""
    by_key = {(s['physical_id'], s['source_sha256']): s['code'] for s in sources}
    need(len(by_key) == len(sources), 'Duplicate acquisition key')
    groups = {True: [], False: []}
    for item in queue:
        key = item['physical_id'], item['full']['before']['file']
        code = by_key.get(key)
        need(code in TYPE_CODES, 'Unbound or unexpected document type')
        groups[TYPE_CODES[code] != '25'].append(item)
    keep, hold = groups[True], groups[False]
    kept = {i['physical_id'] for i in keep}
    held = {i['physical_id'] for i in hold}
    need((len(keep), len(hold), len(kept), len(held)) == (37, 8, 18, 6) and kept.isdisjoint(held),
         'Unexpected partition of the master cohort')
    need(len({i['candidate_id'] for i in queue}) == 45, 'Duplicate master candidate')
    return keep, dict(included_physical_ids=sorted(kept), excluded_physical_ids=sorted(held),
                      excluded_candidates=sorted(i['candidate_id'] for i in hold))


def prepare(dest):
    master = private_run(MASTER)
    need(not dest.exists(), 'Run already exists')
    public = EC/'human_gate/receipts'/MASTER
    receipt = verify_master(master)
    need(receipt == read(public/'verification.json') and
         sha(master/'aggregate.json') == sha(public/'aggregate.json'), 'Master differs from public receipt')
    need(production_trust()['expected_journal_head_sha256'] is None and
         not any(master.parent.glob('*/signed_round1.json')), 'Signed closure or checkpoint requires reconciliation')
    original = read(master/'aggregate.json')
    queue = read(master/'queue.json')
    keep, selection = partition(queue, read(ACQUISITION)['sources'])
    upstream = original['checks']['upstream_rights']
    for name, h in upstream.items():
        need(sha(ROOT/'research/cache/upstream'/('midv2020_'+name)) == h, 'Provider notice mismatch')
    wanted = {h for i in keep for h in i['allowed_evidence_sha256']}
    assets = {h: master/'R02'/rel for rel,h in read(master/'R02_manifest.json').items() if h in wanted}
    need(set(assets) == wanted, 'Missing retained image')
    ids = {i['candidate_id'] for i in keep}
    rows = [r for r in read(SOURCE_Q/'evidence.json')['candidates'] if r['candidate_id'] in ids]
    need(len(rows) == len(keep), 'Incomplete ledger binding')

    # Build off to the side. A failed run never occupies the requested immutable name.
    with TemporaryDirectory(dir=dest.parent) as tmp:
        stage = Path(tmp)/'run'
        save_new(stage/'selection.json', selection)
        save_new(stage/'queue.json', keep)
        packages, rights = write_packages(stage, keep, assets, upstream, scope='C2_37_PROPOSED')
        summary = dict(scope='C2_37_PROPOSED', baseline=BASELINE,
                       master_aggregate_sha256=sha(public/'aggregate.json'), acquisition_sha256=sha(ACQUISITION),
                       selection_sha256=sha(stage/'selection.json'), queue_sha256=sha(stage/'queue.json'),
                       type_mapping_sha256=digest(TYPE_CODES), package_sha256=packages,
                       rights_file_sha256=sha(stage/'artifact_rights.json'),
                       rights=[{k:v for k,v in r.items() if k!='members'} | dict(unique_members=len(r['members']))
                               for r in rights],
                       selected=cluster_metrics(rows, ids), held=dict(candidates=8, physical_ids=6),
                       images_per_workspace=len(wanted), forms_per_workspace=len(keep),
                       source_precision=dict(Counter(i['source_precision']['body'] for i in keep)),
                       assessor_sharing='REVIEW_ACCESS_PENDING', owner_approval=None,
                       scientific_gate='GO_PREPARATORY_ONLY')
        save_new(stage/'aggregate.json', summary)
        stage.rename(dest)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run')
    args = parser.parse_args()
    print(prepare(private_run(args.run))['scope'])
