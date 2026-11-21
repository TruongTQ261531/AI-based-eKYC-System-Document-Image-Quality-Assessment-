"""Run from repository root. Every invocation creates a fresh private run directory."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import platform
import re
import PIL

from ..task55.data import EC, ROOT, read, save_new, sha
from ..reviewer_tools.strict import digest
from . import pixel_lineage_audit as pixel
from . import c2_evidence_audit as c2
from .corpus_audit import canonical_id

HISTORY = Path('master_01/oracle_reliability_20261116/continuation_20261116_2347/feasibility_02')
NAMES = {'samples','sources','evaluation','train','selection','midv_samples','synthetic_samples'}
KEYS = ('physical_id','role','layout','capture','source','variant','original_sha256','source_sha256',
        'device','camera','document_type','capture_transform')


def metadata(root):
    by_path = defaultdict(list)
    manifests, exclusions = {}, Counter()
    for folder in sorted(root.iterdir()):
        try:
            pixel.safe_path(folder, root)
            if not folder.is_dir():
                continue
            for stem in sorted(NAMES):
                p = folder/(stem+'.json')
                if not p.is_file():
                    continue
                pixel.safe_path(p, root)
                if p.stat().st_size > 120_000_000:
                    exclusions['large_manifest'] += 1
                    continue
                raw = p.read_bytes()
                manifests[p.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    rows = [r for arm in obj.values() if isinstance(arm,list) for r in arm]
                else:
                    rows = obj
                for r in rows:
                    if not isinstance(r,dict):
                        continue
                    rel = r.get('path')
                    h = r.get('input_sha256') or r.get('source_sha256')
                    m = {k:r[k] for k in KEYS if r.get(k) is not None}
                    if folder.name=='midv2020' and stem=='selection':
                        pid = canonical_id('midv2020/'+r['code']+'/'+Path(r['filename']).stem)
                        if not pid:
                            continue
                        rel = 'research/data/midv2020/'+r['code']+'/'+r['filename']
                        h = r['image_sha256']
                        m.update(physical_id=pid,layout=r['code'])
                    if not isinstance(rel,str) or not isinstance(h,str):
                        continue
                    location = ROOT/rel.replace('\\','/')
                    if '..' in location.parts or not location.is_relative_to(root):
                        exclusions['out_of_scope_metadata_paths'] += 1
                        continue
                    m.update(dataset=folder.name, expected=h)
                    entry = by_path[location.relative_to(root).as_posix()]
                    if m not in entry:
                        entry.append(m)
        except (OSError,ValueError) as exc:
            exclusions[type(exc).__name__] += 1
    return by_path, manifests, exclusions


def audit(destination, dry_run, cache=None):
    root = ROOT/'research/data'
    pixel.safe_path(root, ROOT)
    paths = list(pixel.inventory(root))
    if dry_run:
        return dict(inventory_entries=len(paths),path_exclusions=sum(bool(err) for _,err in paths))
    meta, manifests, exclusions = metadata(root)
    rows = []
    for p,err in paths:
        key = p.relative_to(root).as_posix()
        row = dict(error=err) if err else pixel.inspect(p,root,cache)
        records = meta.pop(key, [])
        bound = [r for r in records if r['expected']==row.get('file')]
        exclusions['metadata_hash_unmatched'] += len(records)-len(bound)
        row.update(path=key,records=bound)
        rows.append(row)
    summary, near = pixel.summarize(rows)
    summary.update(metadata_manifest_digest=digest(manifests),metadata_exclusions=dict(exclusions),
                   metadata_referenced_paths_missing=len(meta),config=pixel.CONFIG,
                   historical_role_basis='manifest role, bound by file bytes and path',
                   scope='historical research/data raster files; primary image for grouping')
    save_new(destination/'pixel_private.json',dict(rows=rows, candidate_components=near,
             missing_metadata_paths=sorted(meta), manifests=manifests))
    lineage_file=EC/'local'/HISTORY/'lineage.json'
    receipt=read(EC/'execution'/HISTORY/'receipt.json')
    if sha(lineage_file)!=receipt['private_outputs']['lineage.json']:
        raise ValueError('Historical lineage changed')
    lineage=read(lineage_file)
    c2_result, detail=c2.audit(ROOT,lineage,rows,read(EC/'execution'/HISTORY/'c2_feasibility.json'))
    save_new(destination/'c2_private.json',detail)
    return dict(schema='p2-research-audit/1',pixel=summary,c2=c2_result,
        historical_midv2020_exposure=dict(Counter(r['historical_exposure'] for r in lineage)),
        source_sha256={p.name:sha(p) for p in [Path(__file__),Path(pixel.__file__),Path(c2.__file__),
            *(Path(__file__).with_name(name) for name in ('c2_inventory.py','policy.py','corpus_audit.py',
               'semantic_registry.py','reference_registry.py','production_trust.json','semantic_registry.json'))]},
        config_sha256=digest(pixel.CONFIG),lineage_snapshot_sha256=sha(lineage_file),
        private_manifest_sha256={p.name:sha(p) for p in sorted(destination.glob('*_private.json'))},
        scientific_gate='NO_GO_SUPERIORITY',python=platform.python_version(),pillow=PIL.__version__)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--dry-run', action='store_true')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',args.run):
        parser.error('Use a run name without a path')
    dest=EC/'local/p2_20261120'/args.run
    dest.mkdir(parents=True,exist_ok=False)
    result=audit(dest,args.dry_run)
    save_new(dest/'aggregate.json',result)
    print(json.dumps(result,indent=2))
