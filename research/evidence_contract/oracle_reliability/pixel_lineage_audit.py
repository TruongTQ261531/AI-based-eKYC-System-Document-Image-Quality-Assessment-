"""Bounded local historical-image audit. dHash components are retrieval candidates."""
import hashlib
import io
import stat
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps

from ..reviewer_tools.strict import digest

FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp', '.gif'}
CONFIG = dict(version='rgb-exif-dhash/3', mode='RGB8', orientation='EXIF transpose',
              frame='primary for comparisons; record hash or decode error for each additional MPO frame', alpha='discard', icc='no color profile conversion',
              dhash='64 horizontal adjacent comparisons, L 9x8 LANCZOS', distance=3,
              max_bytes=64 << 20, max_pixels=32_000_000, max_frames=4)


def safe_path(path, root):
    """Check every existing component, including Windows junction/reparse points."""
    path, root = Path(path).absolute(), Path(root).absolute()
    if '..' in path.parts or not path.is_relative_to(root):
        raise ValueError('outside_root')
    for p in (root, *(root.joinpath(*path.relative_to(root).parts[:i])
                      for i in range(1, len(path.relative_to(root).parts) + 1))):
        st = p.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError('path_alias')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('outside_root')
    return path


def inventory(root):
    stack = [root]
    while stack:
        path = stack.pop()
        try:
            safe_path(path, root)
            if path.is_dir():
                stack.extend(sorted(path.iterdir(), reverse=True))
            elif path.suffix.lower() in FORMATS:
                yield path, None
        except (ValueError, OSError) as exc:
            yield path, str(exc) if isinstance(exc, ValueError) else type(exc).__name__


def frame_fingerprint(src):
    if src.width * src.height > CONFIG['max_pixels']:
        raise ValueError('pixel_or_frame_limit')
    img = ImageOps.exif_transpose(src).convert('RGB')
    h = hashlib.sha256(f"rgb-exif/1|RGB|{img.width}x{img.height}|".encode())
    for y in range(0, img.height, 64):
        h.update(img.crop((0, y, img.width, min(img.height, y+64))).tobytes())
    thumb = img.convert('L').resize((9, 8), Image.Resampling.LANCZOS).tobytes()
    bits = [thumb[i] > thumb[i+1] for i in range(72) if i % 9 != 8]
    return dict(size=img.size,pixel=h.hexdigest(),dhash=sum(int(bit) << i for i,bit in enumerate(bits)))


def inspect(path, root, single_frame_cache=None):
    row = {}
    try:
        safe_path(path, root)
        st = path.stat()
        if not stat.S_ISREG(st.st_mode):
            raise ValueError('not_regular')
        if st.st_size > CONFIG['max_bytes']:
            raise ValueError('file_size_limit')
        with path.open('rb') as stream:
            raw = stream.read(st.st_size + 1)
        if len(raw) != st.st_size:
            raise ValueError('changed_size')
        row['file'] = hashlib.sha256(raw).hexdigest()
        if single_frame_cache is not None and row['file'] in single_frame_cache:
            return dict(row,**single_frame_cache[row['file']],additional_frames=[])
        with Image.open(io.BytesIO(raw)) as src:
            count = getattr(src,'n_frames',1)
            if count>CONFIG['max_frames'] or (count>1 and src.format!='MPO'):
                raise ValueError('pixel_or_frame_limit')
            row.update(frame_fingerprint(src), additional_frames=[])
            for index in range(1, count):
                try:
                    src.seek(index)
                    frame = frame_fingerprint(src)
                except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
                    row.setdefault('additional_frame_errors', []).append(
                        dict(index=index, error=type(exc).__name__))
                else:
                    row['additional_frames'].append(dict(index=index, **frame))
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as exc:
        row['error'] = str(exc) if isinstance(exc, ValueError) and str(exc) in (
            'file_size_limit','pixel_or_frame_limit','outside_root','path_alias','not_regular','changed_size') else type(exc).__name__
    return row


def components(rows):
    """Group unique dHashes by threshold edges. Exclude pixel-exact-only groups."""
    hashes = defaultdict(list)
    for i, row in enumerate(rows):
        if 'dhash' in row:
            hashes[row['dhash']].append(i)
    parent = {}
    def find(x):
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    keys = sorted(hashes)
    # Four disjoint 16-bit bands: a distance <= 3 shares at least one band.
    bands = defaultdict(list)
    for key in keys:
        parent[key] = key
        parts = [(i, (key >> (16*i)) & 65535) for i in range(4)]
        candidates = {old for part in parts for old in bands[part]}
        for old in candidates:
            if (old ^ key).bit_count() <= CONFIG['distance']:
                parent[find(old)] = find(key)
        for part in parts:
            bands[part].append(key)
    groups = defaultdict(list)
    for key, indices in hashes.items():
        groups[find(key)].extend(indices)
    return [sorted(ids) for ids in groups.values() if len({rows[i]['pixel'] for i in ids}) > 1]


def summarize(rows):
    def groups(key):
        result = defaultdict(list)
        for row in rows:
            if key in row:
                result[row[key]].append(row)
        return result
    by_file, by_pixel = groups('file'), groups('pixel')
    ids, families, captures = set(), set(), set()
    by_id = defaultdict(list)
    corpus_counts = Counter()
    exposure_counts = Counter()
    unknown = Counter()
    exclusions = Counter()
    for row in rows:
        meta = row.get('records', [])
        origins = set()
        for record in meta:
            pid = record.get('physical_id') or ''
            if pid.startswith('midv2020/'):
                origins.add('MIDV-2020')
            elif pid.startswith('midvup/'):
                origins.add('MIDV-UP')
            elif str(record.get('source','')).startswith('authored'):
                origins.add('project_authored')
        row['corpus_evidence'] = sorted(origins)
        corpus_counts.update(origins or {'UNKNOWN'})
        row['exposure'] = 'RECORDED_HISTORICAL_STUDY' if meta else 'EXPOSURE_UNKNOWN'
        exposure_counts[row['exposure']] += 1
        for key in ('physical_id','role','layout','capture','original_sha256'):
            if not any(m.get(key) for m in meta):
                unknown[key] += 1
        for m in meta:
            if m.get('physical_id'):
                ids.add(m['physical_id'])
                by_id[m['physical_id']].append(row)
            if m.get('layout'):
                families.add((m['dataset'],m['layout']))
            if m.get('capture') and m.get('physical_id'):
                captures.add((m['physical_id'],m['capture']))
        row['bound_parent_files'] = sorted({m[key] for m in meta for key in ('original_sha256','source_sha256')
            if m.get(key) in by_file and m[key] != row.get('file')})
        if 'error' in row:
            exclusions[row['error']] += 1
    def multi(group, field):
        return len({m[field] for row in group for m in row.get('records', []) if m.get(field)}) > 1
    near = components(rows)
    return dict(entries=len(rows), file_bytes_hashed=sum('file' in r for r in rows),
                decoded=sum('pixel' in r for r in rows),additional_frames_hashed=sum(len(r.get('additional_frames',[])) for r in rows), exclusions=dict(exclusions),
                additional_frame_errors=dict(Counter(error['error'] for row in rows
                    for error in row.get('additional_frame_errors', []))),
                excluded_entries=sum(exclusions.values()),file_duplicate_groups=sum(len(g)>1 for g in by_file.values()),
                pixel_duplicate_groups=sum(len(g)>1 for g in by_pixel.values()), near_candidate_components=len(near),
                exact_pixel_multiple_physical_ids=sum(multi(g,'physical_id') for g in by_pixel.values()),
                exact_pixel_multiple_roles=sum(multi(g,'role') for g in by_pixel.values()),
                image_exposure=dict(exposure_counts), corpus_evidence_counts=dict(corpus_counts),
                exact_pixel_multiple_evidenced_corpora=sum(len({c for r in g for c in r['corpus_evidence']})>1 for g in by_pixel.values()),
                exact_pixel_multiple_study_collections=sum(multi(g,'dataset') for g in by_pixel.values()),
                physical_ids_multiple_roles=sum(multi(g,'role') for g in by_id.values()),
                physical_ids_multiple_study_collections=sum(multi(g,'dataset') for g in by_id.values()),
                physical_ids=len(ids), collection_layout_groups=len(families), physical_id_capture_label_groups=len(captures),
                file_bound_parent_links=sum(len(r['bound_parent_files']) for r in rows),
                unknown_metadata_entries=dict(unknown), input_inventory_digest=digest([
                    [r['path'],r.get('file'),r.get('error')] for r in rows])), near
