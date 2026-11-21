"""Replay aggregate arithmetic and evidence bindings from a private P2 run."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import json

from ..task55.data import EC, ROOT, read, sha
from ..reviewer_tools.strict import digest, need
from .p2_audit import HISTORY
from .pixel_lineage_audit import CONFIG, inspect, inventory, safe_path, summarize
from .corpus_audit import objects
from . import c2_evidence_audit
from .verify_d4 import verify as verify_d4


def cross_role_patterns(rows):
    """Count exact primary pixel groups by their collection and declared split."""
    groups = defaultdict(set)
    for row in rows:
        if 'pixel' in row:
            for record in row['records']:
                if record.get('role'):
                    groups[row['pixel']].add((record['dataset'], record['role']))
    patterns = Counter(tuple(sorted(labels)) for labels in groups.values()
                       if len({role for _, role in labels}) > 1)
    return [dict(collection_roles=[dict(collection=c, role=r) for c, r in labels],
                 pixel_groups=count) for labels, count in sorted(patterns.items())]


def verify(run, public):
    aggregate=read(run/'aggregate.json')
    baseline=read(public/'baseline.json')
    for name, expected in baseline['protected_files'].items():
        need(sha(ROOT/name)==expected, 'Protected baseline changed')
    for name, expected in aggregate['source_sha256'].items():
        need(sha(Path(__file__).with_name(name))==expected,'Source digest')
    for name, expected in aggregate['private_manifest_sha256'].items():
        need(sha(run/name)==expected,'Private manifest digest')
    need(verify_d4(EC/'execution/master_01/d4_development_20261117/controls_01')==baseline['d4'],'D4 replay')
    px=read(run/'pixel_private.json')
    rows=px['rows']
    counts=aggregate['pixel']
    need(digest(px['manifests'])==counts['metadata_manifest_digest'],'Metadata binding')
    explicit_pairs=set()
    for name, expected in px['manifests'].items():
        path=safe_path(ROOT/'research/data'/name,ROOT/'research/data')
        need(sha(path)==expected,'Metadata changed')
        for record in objects(read(path)):
            keys=('physical_instance','field','primary_source_id','backup_source_id')
            if all(isinstance(record.get(k),str) for k in keys):
                explicit_pairs.add(tuple(record[k] for k in keys))
    need(digest([[r['path'],r.get('file'),r.get('error')] for r in rows])==counts['input_inventory_digest'],'Image inventory')
    need(len({r['path'] for r in rows})==len(rows)==counts['entries'],'Unique entries')
    root=ROOT/'research/data'
    need([p.relative_to(root).as_posix() for p, _ in inventory(root)] == [r['path'] for r in rows],
         'Historical raster inventory changed')
    for row in rows:
        if 'file' in row:
            need(sha(safe_path(root/row['path'],root))==row['file'],'Source bytes changed')
        if row.get('additional_frame_errors'):
            actual = inspect(root / row['path'], root)
            need(actual.get('pixel') == row['pixel'] and
                 actual.get('additional_frame_errors') == row['additional_frame_errors'],
                 'Auxiliary decode failure replay')
    for field,target in [('file','file_duplicate_groups'),('pixel','pixel_duplicate_groups')]:
        observed=Counter(r[field] for r in rows if field in r)
        need(sum(n>1 for n in observed.values())==counts[target], 'Exact duplicate count')
    need(sum('pixel' in r for r in rows)==counts['decoded'],'Coverage')
    need(sum(len(r.get('additional_frames',[])) for r in rows)==counts['additional_frames_hashed'],'Extra frame coverage')
    need(len(px['candidate_components'])==counts['near_candidate_components'],'Component count')
    rebuilt_pixel, components = summarize(rows)
    need(all(counts[k] == v for k, v in rebuilt_pixel.items()), 'Pixel summary replay')
    need(components == px['candidate_components'], 'Near-duplicate component membership')
    need(counts['config'] == CONFIG and aggregate['config_sha256'] == digest(CONFIG), 'Pixel configuration')
    prior_candidates=EC/'local'/HISTORY/'c2_candidates.json'
    expected=read(EC/'execution'/HISTORY/'receipt.json')['private_outputs']
    need(sha(prior_candidates)==expected['c2_candidates.json'],'Candidate bytes')
    prior=read(prior_candidates)
    detail=read(run/'c2_private.json')
    summary=aggregate['c2']
    lineage=EC/'local'/HISTORY/'lineage.json'
    need(sha(lineage)==aggregate['lineage_snapshot_sha256'],'Historical exposure changed')
    rebuilt_summary,rebuilt_rows=c2_evidence_audit.audit(ROOT,read(lineage),rows,
        read(EC/'execution'/HISTORY/'c2_feasibility.json'))
    need(rebuilt_summary==summary and rebuilt_rows==detail,'C2 evidence replay')
    need(digest(prior)==summary['candidate_inventory_digest'],'Candidate set')
    need([c['candidate_id'] for c in prior]==[d['candidate_id'] for d in detail],'Candidate binding/order')
    matched_pairs=sum((c['physical_instance'],c['field'],c['primary_source_id'],c['backup_source_id'])
                      in explicit_pairs for c in prior)
    need(matched_pairs==0,'New source-pair binding needs evidence review')
    for key, expected_counts in summary['condition_counts'].items():
        actual=Counter(r['conditions'][key] for r in detail)
        need(all(actual[k]==v for k,v in expected_counts.items()) and sum(expected_counts.values())==len(detail),'Condition counts')
    need(all(r['eligible']==all(s=='PASS' for s in r['conditions'].values()) for r in detail),'Eligibility conjunction')
    need(sum(r['eligible'] for r in detail)==summary['eligible'],'Eligible count')
    followup_ids = defaultdict(set)
    for candidate, finding in zip(prior, detail, strict=True):
        followup_ids[finding['followup_group']].add(candidate['physical_instance'])
    need(sum(map(len, followup_ids.values())) == summary['physical_ids'], 'C2 follow-up ID groups')
    role_patterns = cross_role_patterns(rows)
    need(sum(p['pixel_groups'] for p in role_patterns) == counts['exact_pixel_multiple_roles'],
         'Cross-role pixel groups')
    status='PASS_TECHNICAL' if counts['decoded'] and counts['decoded']==len(rows) and not counts['metadata_referenced_paths_missing'] else 'BLOCKED_INPUT'
    if status == 'PASS_TECHNICAL' and counts['additional_frame_errors']:
        status = 'PARTIAL_AUXILIARY_FRAME_COVERAGE'
    return dict(status=status,protected_files=len(baseline['protected_files']),images=counts['decoded'],
                distinct_file_hashes=len({r['file'] for r in rows if 'file' in r}),
                distinct_primary_pixel_hashes=len({r['pixel'] for r in rows if 'pixel' in r}),
                near_candidate_entries=sum(map(len, components)),
                cross_role_exact_pixel_patterns=role_patterns,
                followup_physical_ids={k:len(v) for k,v in followup_ids.items()},
                additional_frames_hashed=counts['additional_frames_hashed'],
                additional_frame_errors=counts['additional_frame_errors'],
                candidate_pairs=len(detail), historical_manifests_checked=len(px['manifests']),
                exact_candidate_source_pair_records_matched=matched_pairs,aggregate_sha256=sha(run/'aggregate.json'),
                verifier_sha256=sha(Path(__file__)),d4_replayed=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.run,EC/'execution/master_01/p2_20261120'),indent=2))
