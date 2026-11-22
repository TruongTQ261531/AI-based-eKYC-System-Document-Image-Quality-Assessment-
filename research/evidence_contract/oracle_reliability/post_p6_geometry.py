"""Verify archived MIDV source regions and replay local pixel transformations."""
from collections import defaultdict
import random

import cv2
import numpy as np

from .semantic_registry import field_for_alias


def rectangle(shape):
    if shape.get('name') != 'rect' or min(shape['width'], shape['height']) <= 0:
        return None
    x, y, w, h = [shape[k] for k in ('x','y','width','height')]
    return np.float32([[x,y],[x+w,y],[x+w,y+h],[x,y+h]])


def mapped_sources(template, source):
    """Check native alias, literal when recorded, and all projected corners jointly."""
    polygons, stored = [], []
    by_key = defaultdict(list)
    for f in source['fields']:
        by_key[f.get('author_key') or f['key']].append(f)
    unique = {}
    for i, reg in enumerate(template['regions']):
        attrs, shape = reg['region_attributes'], reg['shape_attributes']
        key = attrs['field_name']
        if len(by_key[key]) != 1 or not attrs.get('value'):
            continue
        f = by_key[key][0]
        if f.get('value', f.get('text', attrs['value'])) != attrs['value']:
            continue
        rect = rectangle(shape)
        if rect is None:
            continue
        projected = np.float32(f['quad'])
        if projected.shape != (4,2) or not np.isfinite(projected).all():
            continue
        polygons.append(rect)
        stored.append(projected)
        unique[i] = projected.tolist()
    if len(polygons) < 3:
        return {}
    if 'template_dimensions' in source:
        w,h = source['template_dimensions']
        corners = np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])
        H = cv2.getPerspectiveTransform(corners,np.float32(source['gt']))
    else:
        # The acquisition stored the original projected quads for each native alias.
        # Check one common transform and residual over all fields, including both MRZ lines.
        H, _ = cv2.findHomography(np.concatenate(polygons),np.concatenate(stored),0)
    if H is None:
        return {}
    rebuilt = cv2.perspectiveTransform(np.array(polygons).reshape(-1,1,2),H).reshape(-1,4,2)
    if not np.isfinite(rebuilt).all() or np.max(np.abs(rebuilt-np.array(stored))) > .2:
        return {}
    return unique


def regions(candidate, template, quads):
    if candidate['backup_source_id'] != 'mrz_line0+mrz_line1':
        return None
    regs = template['regions']
    primary = candidate['primary_source_id']
    if not primary.startswith('region_') or not primary[7:].isdigit():
        return None
    index = int(primary[7:])
    if index not in quads or field_for_alias(regs[index]['region_attributes']['field_name']) != candidate['field']:
        return None
    keys = [r['region_attributes']['field_name'] for r in regs]
    lines = ['mrz_line0','mrz_line1']
    if any(keys.count(k) != 1 or keys.index(k) not in quads for k in lines):
        return None
    indices = [index]+[keys.index(k) for k in lines]
    if len(set(indices)) != 3:
        return None
    return {f'region_{i}':quads[i] for i in indices}


def same_lineage(before, after):
    return bool(before and after and before['physical_id'] == after['physical_id']
                and before['file'] == (after.get('original_sha256') or after.get('source_sha256'))
                and before['file'] != after.get('input_sha256'))


def replay_mutation(parent, child, row, full_fields):
    """Return crop origin / literal rasterized masks only on exact RGB reproduction."""
    kind = row['capture']
    h,w = child.shape[:2]
    x = y = 0
    masks = []
    if 'crop_origin' in row.get('capture_transform', {}):
        tr = row['capture_transform']
        if tr.get('blur_glare') or kind not in ('field_clip','corner_clip'):
            return None
        x,y = tr['crop_origin']
        if min(x,y) < 0 or x+w != parent.shape[1] or y+h != parent.shape[0] or not (x or y):
            return None
        expected = parent[y:,x:]
    elif kind in ('value_mask','pair_a','pair_b','pair_mask') and row.get('mask_regions'):
        masks = row['mask_regions']
        expected = parent.copy()
        for q in masks:
            pts = np.asarray(q)
            if pts.ndim != 2 or pts.shape[1] != 2 or len(pts)<3 or not np.isfinite(pts).all():
                return None
            cv2.fillConvexPoly(expected, np.rint(pts).astype(np.int32), (35,38,42))
    elif kind in ('field_clip','value_mask') and full_fields:
        from research.v2_data import augment
        expected, fields = augment(parent,full_fields,row['physical_id'],kind)
        if len(fields) != len(row['fields']) or any(
                f['key'] != s['key'] or not np.allclose(f['quad'],s['quad'],rtol=0,atol=.001)
                for f,s in zip(fields,row['fields'])):
            return None
        if kind == 'field_clip':
            y = round(full_fields[0]['quad'][0][1]-fields[0]['quad'][0][1])
        else:
            from research.v2_common import seed
            generator = random.Random(seed(row['physical_id']+'/'+kind))
            chosen = generator.sample(range(len(full_fields)),generator.randrange(1,len(full_fields)+1))
            painted = parent.copy()
            for index in chosen:
                q = np.asarray(full_fields[index]['quad'],np.float32)
                q = (q-q.mean(axis=0))*1.04+q.mean(axis=0)
                cv2.fillConvexPoly(painted,np.rint(q).astype(np.int32),(35,38,42))
                masks.append(q.tolist())
            if not np.array_equal(painted,expected):
                return None

    else:
        return None
    if not np.array_equal(expected,child) or np.array_equal(parent,child):
        return None
    return dict(origin=[x,y], masks=masks, size=[w,h])


def region_impact(quad, transform):
    """Fraction of polygon pixels removed by cropping or covering masks in this child."""
    q = np.rint(np.array(quad)-transform['origin']).astype(np.int32)
    x,y,w,h = cv2.boundingRect(q)
    footprint = np.zeros((h,w),np.uint8)
    cv2.fillConvexPoly(footprint,q-np.int32([x,y]),1)
    total = int(footprint.sum())
    child_w,child_h = transform['size']
    # Restrict the computation to a region-sized canvas even for large photographs.
    for mask in transform['masks']:
        points = np.rint(mask).astype(np.int32)
        mx,my,mw,mh = cv2.boundingRect(points)
        x0,y0,x1,y1 = max(x,mx),max(y,my),min(x+w,mx+mw),min(y+h,my+mh)
        if x1>x0 and y1>y0:
            stamp = np.zeros((mh,mw),np.uint8)
            cv2.fillConvexPoly(stamp,points-np.int32([mx,my]),1)
            region = footprint[y0-y:y1-y,x0-x:x1-x]
            region[stamp[y0-my:y1-my,x0-mx:x1-mx].astype(bool)] = 0
    left,top = max(0,-x),max(0,-y)
    right,bottom = min(w,child_w-x),min(h,child_h-y)
    remaining = int(footprint[top:bottom,left:right].sum()) if right>left and bottom>top else 0
    return 1-remaining/total if total else None
