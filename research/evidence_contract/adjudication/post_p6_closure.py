"""Rebuild the owner's fixed Round 1 roster from sealed evidence, without signing."""
from collections import Counter
from itertools import combinations

from .workflow import normalized_view
from ..execution.master_01.reviewer_intake_20261117_r02_phase2.workflow import sealed_view
from ..oracle_reliability.reference_registry import production_trust
from ..reviewer_tools.intake import package
from ..reviewer_tools.phase2_comparison import compare
from ..reviewer_tools.strict import canonical, digest, need
from ..task55 import agreement, ifv
from ..task55.data import EC, read, save_new, sha

PUBLIC = EC / 'execution/master_01'
LOCAL = EC / 'local'
ROSTER = {
    'AUTHOR': ('00ff0a49d4df5a84c2d78511bcf2d9ed36e19945747a93c08d6788e3b9a9da79',
               '812605bbab3940be838ac9da07ed903c0098717ace789f703f080869dde3267d'),
    'R02': ('b25d59d918c7cd0ba01702bc0c16b3c19acd973245ab2c7ebe83352dcbeb074b',
            '4813ecabf57899329f11dae31c47063154cfd35e51bbbd7982b10cd31827d3d1'),
    'R03': ('d57613872163de808ce8c5ac9a5e9657f142b2d51264db1e10bc095eecd9e0b8',
            '79cbb88301989080b2bc26931bc2bef4e3a76a1ab09c2134ba3b721ea07e081d'),
}


def originals(code, first, second):
    if code == 'AUTHOR':
        rows = [('continuation_20261114/original_review_export.json', 'ifv_20261114/intake.json'),
                ('continuation_20261115/original_phase2_export.json', 'ifv_20261115/intake.json')]
        return [(LOCAL/'master_01'/p, read(PUBLIC/r)['source_file_sha256']) for p, r in rows]
    rows = []
    for sid in (first, second):
        if code == 'R02' and sid == first:
            receipt = read(PUBLIC/'reviewer_intake_20261116_r02/intake.json')
            rows.append((LOCAL/'master_01/reviewer_intake_20261116_r02/original_review_R02.json',
                         receipt['source_file_sha256']))
        else:
            folder = LOCAL/'reviewer_intake_v2'/sid
            rows.append((folder/'raw.json', read(folder/'receipt.json')['raw_sha256']))
    return rows


def unsigned_payload(views, authority_id, timestamp):
    """With real designation and signing time this is the exact workflow payload."""
    return dict(schema='review-round-closure/1', mode='PRODUCTION', authority_id=authority_id,
                authority_role='round_owner', timestamp=timestamp, round_id='IFV-Round-1',
                view_sha256=sorted(digest(v) for v in views),
                cutoff_basis='Owner cutoff 2026-11-21. Frozen AUTHOR, R02, R03, both phases complete.')


def prepare(dest):
    need(not production_trust()['authorities'], 'Reassess authority before preparing a pending closure')
    phases, views, comp, summary = {}, {}, {}, {}
    for code, (first, second) in ROSTER.items():
        (p1, h1), (p2, h2) = originals(code, first, second)
        need(sha(p1) == h1 and sha(p2) == h2, 'Original review byte hash')
        phase1 = read(p1)
        need(digest(phase1) == first and digest(read(p2)) == second, 'Sealed submission digest')
        _, validation, _ = ifv.sealed_phase1(first)
        need(validation['complete_observations'] == 86, 'Incomplete phase 1')
        paths = list(ifv.STAGE2.glob('*/submissions/'+second+'/output_observations.json'))
        need(len(paths) == 1 and read(paths[0]) == read(p2), 'Unique sealed phase 2')
        folder = paths[0].parents[2]
        compared, _, links, _ = sealed_view(paths[0], code)
        comp[code] = compared
        identities = {cid: row['identity_sha256'] for cid, row in links.items()}
        packet = read(folder/'packet.json')
        # AUTHOR used the organizer's original IFV publication, predating portable jobs.
        # Its real manifest hash identifies the legacy issuance in this adapter.
        if code == 'AUTHOR':
            issuance = sha(folder/'publication.json')
            bundle = dict(packet=packet, archive_sha256=issuance, job=dict(job_id=issuance,
                          phase='phase2', reviewer_id=code, phase1_snapshot=first))
        else:
            receipt = read(LOCAL/'reviewer_intake_v2'/second/'receipt.json')
            archives = list((LOCAL/'reviewer_exports').rglob('reviewer_'+code+'_phase2.zip'))
            need(len(archives) == 1, 'Expected one issued archive')
            bundle = package(archives[0], receipt['package_sha256'], code)
        view = normalized_view(p2.read_bytes(), bundle, identities, phase1_seal=dict(
            snapshot_id=first, reviewer_id=code, complete=True))
        need(view['complete'] and len(view['items']) == 46, 'Incomplete phase 2')
        views[code], phases[code] = view, phase1
        summary[code] = dict(snapshots=[first, second], raw_sha256=[h1, h2], complete=[86, 46],
                             view_sha256=digest(view), join_sha256=sha(ifv.JOINS/(folder.name+'.json')),
                             exposure=dict(Counter(i['prior_exposure'] for i in phase1['items'])))
    pairs = {}
    for a, b in combinations(ROSTER, 2):
        metrics, _ = compare(comp[a], comp[b])
        historical = {'AUTHOR_R02':'reviewer_intake_20261117_r02_phase2/phase2_agreement.json',
                      'AUTHOR_R03':'reviewer_intake_20261120_r03_phase2/author_r03_agreement.json',
                      'R02_R03':'reviewer_intake_20261120_r03_phase2/r02_r03_agreement.json'}[a+'_'+b]
        need(metrics['views'] == read(PUBLIC/historical)['views'], 'Historical pairwise results differ')
        one = agreement.compare([phases[a], phases[b]], read(agreement.PACKET_ROOT/'packet_manifest.json'))
        all_rows = metrics['views']['all']
        pairs[a+'_'+b] = dict(phase1=one['categorical'], transcript=one['readable_transcript_exact_agreement'],
                              phase2_raw_exact=all_rows['all_raw_dimensions_matched'],
                              endpoints={k:v['matched'] for k,v in all_rows['derived'].items()})
    queues = {}
    for key in comp['AUTHOR']['rows']:
        rows = [c['rows'][key] for c in comp.values()]
        reasons = []
        for group in ('raw','derived'):
            if len({digest(row[group]) for row in rows}) > 1:
                reasons.append(group+'_disagreement')
        if any('uncertain' in row['raw'].values() or 'not_established' in row['raw'].values()
               or set(row['derived'].values()) & {'INCONCLUSIVE','INVALID_TEST'} for row in rows):
            reasons.append('uncertain_or_guard_unresolved')
        if reasons:
            queues[key] = reasons
    # Phase-1 slots are distinct from the 46 phase-2 cases and retain their own joins.
    slots = [{i['slot_id']:i for i in phase['items']} for phase in phases.values()]
    phase1_queue = []
    for key in slots[0]:
        fields = ('availability','readability','semantic_key_confirmed','observed_transcript','sources')
        observations = [tuple(digest(s[key][f]) for f in fields) for s in slots]
        if len(set(observations)) > 1 or any('uncertain' in (s[key][f] for f in fields[:3]) for s in slots):
            phase1_queue.append(key)
    # Include the independently flagged contradiction even if other reviewers agree.
    flags = read(LOCAL/'master_01/reviewer_intake_20261120_r03_phase2/r03_coherence_details.json')
    save_new(dest/'review_views.json', views)
    save_new(dest/'organizer_queue.json', dict(phase1=phase1_queue, phase2=queues, coherence=flags))
    payload = unsigned_payload(views.values(), None, None)
    with (dest/'closure_payload.canonical.json').open('xb') as stream:
        stream.write(canonical(payload))
    return dict(cutoff='2026-11-21', intake='CLOSED_BY_OWNER_DECISION', agreement='COMPLETE',
                signature='SIGNATURE_PENDING', adjudication='PENDING', approved_references=0,
                members=summary, pairs=pairs, phase1_queue=len(phase1_queue), phase2_queue=len(queues),
                pending_payload_sha256=digest(payload))


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('run')
    args = parser.parse_args()
    need(Path(args.run).name == args.run and args.run not in ('.','..'), 'Expected run name')
    dest = LOCAL/'post_p6'/args.run
    dest.mkdir(parents=True, exist_ok=False)
    save_new(dest/'round.json', prepare(dest))
