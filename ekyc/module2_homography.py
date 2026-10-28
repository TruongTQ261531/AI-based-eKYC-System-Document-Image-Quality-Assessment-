"""Localize a document quadrilateral and rectify original pixels.

Contrast enhancement is used only for localization. Geometry alone cannot infer
reading direction, true aspect ratio, or recover missing image content.
"""
import cv2
import numpy as np
from .io import StageError


def order_corners(points):
    """Cyclic image-coordinate order, starting near top-left (not text upright)."""
    try:
        points = np.asarray(points, dtype=np.float32).reshape(4, 2)
    except (ValueError, TypeError, OverflowError) as error:
        raise StageError('Four finite document corners required') from error
    if not np.isfinite(points).all() or len(np.unique(points, axis=0)) != 4:
        raise StageError('Four distinct finite corners required')
    center = points.mean(axis=0)
    ordered = points[np.argsort(np.arctan2(points[:, 1]-center[1], points[:, 0]-center[0]))]
    first = np.lexsort((ordered[:, 0], ordered[:, 1], ordered.sum(axis=1)))[0]
    ordered = np.ascontiguousarray(np.roll(ordered, -first, axis=0))
    edges = np.roll(ordered, -1, axis=0)-ordered
    lengths = np.linalg.norm(edges, axis=1)
    cross = edges[:, 0]*np.roll(edges, -1, axis=0)[:, 1]-edges[:, 1]*np.roll(edges, -1, axis=0)[:, 0]
    if (not cv2.isContourConvex(ordered) or abs(cv2.contourArea(ordered)) < 100
            or lengths.min() < 2 or np.min(np.abs(cross)/(lengths*np.roll(lengths, -1))) < .03):
        raise StageError('Invalid or degenerate document quadrilateral')
    return ordered


def _edge_evidence(points, nearby, gray):
    """Check each side independently and measure contrast across its boundary."""
    supports, contrasts = [], []
    height, width = gray.shape
    for a, b in zip(points, np.roll(points, -1, axis=0)):
        delta = b-a
        length = float(np.linalg.norm(delta))
        xy = a + np.linspace(.04, .96, min(256, max(24, int(length))))[:, None]*delta
        pixels = np.rint(xy).astype(int)
        supports.append(float(np.mean(nearby[pixels[:, 1], pixels[:, 0]] > 0)))
        normal = np.array([-delta[1], delta[0]]) / max(length, 1)
        inner, outer = np.rint(xy+4*normal).astype(int), np.rint(xy-4*normal).astype(int)
        valid = ((inner[:, 0] >= 0) & (inner[:, 0] < width) & (inner[:, 1] >= 0) & (inner[:, 1] < height)
                 & (outer[:, 0] >= 0) & (outer[:, 0] < width) & (outer[:, 1] >= 0) & (outer[:, 1] < height))
        if valid.any():
            ip, op = inner[valid], outer[valid]
            diff = np.abs(gray[ip[:, 1], ip[:, 0]].astype(float)-gray[op[:, 1], op[:, 0]])
            contrasts.append(float(np.median(diff)))
        else:
            contrasts.append(0.)
    return supports, contrasts


def _refine_sides(points, edges):
    """Fit nearby observed edge pixels, then intersect adjacent fitted lines.

    Polygon approximation can cut across rounded corners. Search only a narrow
    band around each proposed side; a missing side must not be invented.
    """
    h, w = edges.shape
    radius = max(4, min(14, int(max(h, w)*.012)))
    offsets = np.arange(-radius, radius+1, dtype=np.float32)
    lines = []
    for a, b in zip(points, np.roll(points, -1, axis=0)):
        delta = b-a
        length = float(np.linalg.norm(delta))
        normal = np.array([-delta[1], delta[0]], np.float32)/length
        xy = a + np.linspace(.08, .92, 96, dtype=np.float32)[:, None]*delta
        band = np.rint(xy[None, :, :]+offsets[:, None, None]*normal).astype(int)
        valid = ((band[:, :, 0] >= 0) & (band[:, :, 0] < w)
                 & (band[:, :, 1] >= 0) & (band[:, :, 1] < h))
        hits = np.zeros(valid.shape, dtype=bool)
        hits[valid] = edges[band[:, :, 1][valid], band[:, :, 0][valid]] > 0
        # Three adjacent offsets tolerate rasterization, not a missing boundary.
        coverage = hits.copy()
        coverage[1:] |= hits[:-1]
        coverage[:-1] |= hits[1:]
        scores = coverage.mean(axis=1)-.08*np.abs(offsets)/radius
        best = int(np.argmax(scores))
        if coverage[best].mean() < .45:
            return None
        selected = band[max(0, best-1):best+2][hits[max(0, best-1):best+2]]
        if len(selected) < 12:
            return None
        vx, vy, x, y = cv2.fitLine(selected.astype(np.float32), cv2.DIST_HUBER, 0, .01, .01).ravel()
        lines.append((np.array([x, y]), np.array([vx, vy])))
    refined = []
    for i in range(4):
        p, u = lines[i-1]
        q, v = lines[i]
        system = np.column_stack((u, -v))
        if abs(np.linalg.det(system)) < .03:
            return None
        refined.append(p+np.linalg.solve(system, q-p)[0]*u)
    refined = np.asarray(refined, dtype=np.float32)
    if np.max(np.linalg.norm(refined-points, axis=1)) > 2.5*radius:
        return None
    if (refined < [2, 2]).any() or (refined >= [w-2, h-2]).any():
        return None
    try:
        return order_corners(refined)
    except StageError:
        return None


def _localize(image, region_hints=None):
    height, width = image.shape[:2]
    scale = min(1.0, 1200/max(height, width))
    small = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    to_source = np.array([width/sw, height/sh], dtype=np.float32)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.createCLAHE(2.0, (8, 8)).apply(gray)
    maps = []
    edge_union = np.zeros_like(gray)
    for name, variant in (('gray', gray), ('clahe', enhanced)):
        blurred = cv2.GaussianBlur(variant, (3, 3), 0)
        for low, high in ((12, 40), (25, 75), (50, 150), (75, 190)):
            edges = cv2.Canny(blurred, low, high)
            edge_union = cv2.bitwise_or(edge_union, edges)
            maps.append((name+'_edges', cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))))
        # Region contours complement interrupted edge contours in low contrast.
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        maps.append((name+'_region', binary))
    nearby = cv2.dilate(edge_union, np.ones((5, 5), np.uint8))
    hints=[]
    for hint in region_hints or []:
        box=np.asarray(hint.get('box'),dtype=float)
        if box.shape!=(4,) or not np.isfinite(box).all() or hint.get('confidence',0)<.65: continue
        x1,y1,x2,y2=box*scale
        if min(x2-x1,y2-y1)<60 or x1<0 or y1<0 or x2>=sw or y2>=sh: continue
        hints.append((np.float32([[x1,y1],[x2,y1],[x2,y2],[x1,y2]]),hint))
    candidates = {}
    for source, mask in maps:
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:45]:
            area = cv2.contourArea(contour)/(sh*sw)
            if not .06 <= area <= .995:
                continue
            for base in (contour, cv2.convexHull(contour)):
                # Rounded plastic corners often produce inset/sloping polygon
                # chords on all four sides. Their enclosing rectangle follows
                # the observed straight edges; the same four-side evidence
                # checks below still reject open/missing boundaries.
                rect=cv2.minAreaRect(base)
                rw,rh=rect[1]
                if rw*rh>0 and cv2.contourArea(base)/(rw*rh)>=.85:
                    points=cv2.boxPoints(rect)
                    key=tuple(np.rint(points[np.lexsort((points[:,1],points[:,0]))].ravel()/4).astype(int))
                    if key not in candidates: candidates[key]=(points,source+'_rounded_rectangle')
                for epsilon in (.012, .02, .03, .045, .06):
                    polygon = cv2.approxPolyDP(base, epsilon*cv2.arcLength(base, True), True)
                    if len(polygon) != 4 or not cv2.isContourConvex(polygon):
                        continue
                    points = polygon.reshape(4, 2)
                    # Deduplicate before costly geometry validation and scoring.
                    key = tuple(np.rint(points[np.lexsort((points[:, 1], points[:, 0]))].ravel()/4).astype(int))
                    if key not in candidates:
                        candidates[key] = (points, source)
    ranked = []
    for points, source in candidates.values():
        try:
            points = order_corners(points)
        except StageError:
            continue
        area = abs(cv2.contourArea(points))/(sh*sw)
        if not .06 <= area <= .995:
            continue
        # A frame edge is not evidence of a complete document boundary.
        border = ((points[:, 0] <= 1) | (points[:, 0] >= sw-2)
                  | (points[:, 1] <= 1) | (points[:, 1] >= sh-2))
        if border.any():
            continue
        supports, contrasts = _edge_evidence(points, nearby, gray)
        if min(supports) < .45 or np.mean(supports) < .65:
            if sum(s >= .5 for s in supports) < 3:
                continue
            refined = _refine_sides(points, edge_union)
            if refined is None:
                continue
            supports, contrasts = _edge_evidence(refined, nearby, gray)
            if min(supports) < .45 or np.mean(supports) < .65:
                continue
            points, source = refined, source+'_refined'
            area = abs(cv2.contourArea(points))/(sh*sw)
            if not .06 <= area <= .995:
                continue
        contrast = min(float(np.mean(contrasts))/40, 1.)
        score = .40*float(np.mean(supports)) + .20*min(supports) + .25*area + .15*contrast
        ranked.append((score, points, source, supports, contrasts, area))
    # A semantic full-card hint prevents strong text/portrait borders from
    # replacing the complete card. Accept a geometric candidate only when it
    # covers the hinted card, rather than a small rectangle inside it.
    if hints:
        hint_points,hint=max(hints,key=lambda value:value[1]['confidence'])
        hx,hy,hw,hh=cv2.boundingRect(hint_points)
        matches=[]
        for item in ranked:
            _,points,*_=item
            x,y,bw,bh=cv2.boundingRect(points)
            intersection,_=cv2.intersectConvexConvex(hint_points,points)
            coverage=intersection/max(cv2.contourArea(hint_points),1)
            if (coverage>=.78 and bw>=.92*hw and bh>=.94*hh and bw<=1.20*hw and bh<=1.20*hh
                    and x<=hx+.04*hw and y<=hy+.04*hh
                    and x+bw>=hx+.96*hw and y+bh>=hy+.96*hh):
                matches.append(item)
        if matches:
            best=max(matches,key=lambda item:item[0])
            return best[1]*to_source,dict(policy='semantic_boundary_v4',source=best[2],
                candidate_count=len(candidates),accepted_candidates=len(matches),score=round(best[0],4),
                score_is_probability=False,edge_supports=[round(v,4) for v in best[3]],
                boundary_contrasts=[round(v,2) for v in best[4]],area_fraction=round(best[5],4),
                ambiguous=False,localization='perspective',document_label=hint['label'])
        # When four edges cannot be corroborated, keep a padded detector crop.
        # This preserves readable content; it does not claim recovered corners.
        x1,y1=hint_points[0];x2,y2=hint_points[2]
        px,py=(x2-x1)*.035,(y2-y1)*.035
        x1,y1=max(0.,x1-px),max(0.,y1-py)
        x2,y2=min(sw-1.,x2+px),min(sh-1.,y2+py)
        points=np.float32([[x1,y1],[x2,y1],[x2,y2],[x1,y2]])
        return points*to_source,dict(policy='semantic_boundary_v4',source='scanocr_card_region',
            candidate_count=len(candidates),accepted_candidates=0,score=round(hint['confidence'],4),
            score_is_probability=False,edge_supports=[],boundary_contrasts=[],
            area_fraction=float(cv2.contourArea(points)/(sw*sh)),ambiguous=False,
            localization='detected_region_crop',document_label=hint['label'])
    if not ranked:
        raise StageError('No reliable document quadrilateral; retake or supply four corners')
    # A strong portrait/text-box boundary inside a plausible full document is
    # usually the wrong crop. Prefer its supported enclosing boundary, without
    # imposing one document aspect ratio or assuming that every rectangle is ID.
    adjusted = []
    for item in ranked:
        score, points, source, supports, contrasts, area = item
        nested = False
        for other in ranked:
            if other[5] < 1.8*area or other[0] < score-.15:
                continue
            intersection, _ = cv2.intersectConvexConvex(points, other[1])
            if intersection/max(abs(cv2.contourArea(points)), 1) >= .95:
                nested = True
                break
        adjusted.append((score-(.15 if nested else 0), points, source, supports, contrasts, area))
    ranked = adjusted
    ranked.sort(key=lambda item: item[0], reverse=True)
    best = ranked[0]
    competing = None
    for other in ranked[1:]:
        intersection, _ = cv2.intersectConvexConvex(best[1], other[1])
        union = abs(cv2.contourArea(best[1]))+abs(cv2.contourArea(other[1]))-intersection
        if intersection/max(union, 1) < .8:
            competing = other[0]
            break
    return best[1]*to_source, dict(
        policy='boundary_evidence_v3', source=best[2], candidate_count=len(candidates),
        accepted_candidates=len(ranked), score=round(best[0], 4),
        score_is_probability=False, edge_supports=[round(v, 4) for v in best[3]],
        boundary_contrasts=[round(v, 2) for v in best[4]], area_fraction=round(best[5], 4),
        ambiguous=bool(competing is not None and best[0]-competing < .05))


def _rectified_metrics(card):
    gray = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
    scale = min(1., 960/max(gray.shape))
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return dict(brightness_mean=round(float(small.mean()), 2),
                brightness_p90=round(float(np.percentile(small, 90)), 2),
                contrast_std=round(float(small.std()), 2),
                sharpness=round(float(cv2.Laplacian(small, cv2.CV_64F).var()), 2),
                bright_pixel_fraction=round(float(np.mean(small >= 250)), 4),
                note='Diagnostic only: bright paper is not proof of glare; OCR must assess readability.')


class Homography:
    def run(self, image, corners=None, *, aspect_ratio=None, region_hints=None):
        if (not isinstance(image, np.ndarray) or image.ndim != 3 or image.shape[2] != 3
                or image.dtype != np.uint8 or min(image.shape[:2]) < 2):
            raise StageError('Expected a non-empty uint8 BGR image')
        if aspect_ratio is not None:
            try:
                aspect_ratio = float(aspect_ratio)
            except (TypeError, ValueError, OverflowError) as error:
                raise StageError('Invalid document aspect ratio') from error
            if not np.isfinite(aspect_ratio) or not .1 <= aspect_ratio <= 10:
                raise StageError('Document aspect ratio must be between 0.1 and 10')
        height, width = image.shape[:2]
        automatic = corners is None
        detection = None
        if automatic:
            corners, detection = _localize(image,region_hints)
        points = order_corners(corners)
        if (points[:, 0] < 0).any() or (points[:, 0] >= width).any() or (points[:, 1] < 0).any() or (points[:, 1] >= height).any():
            raise StageError('Document corners extend outside the source image')
        top, right, bottom, left = np.linalg.norm(np.roll(points, -1, axis=0)-points, axis=1)
        out_width, out_height = float(max(top, bottom)), float(max(left, right))
        if min(out_width, out_height) < 80:
            raise StageError('Document is too small to read')
        if aspect_ratio is not None:
            out_width = min(out_width, out_height*aspect_ratio)
            out_height = out_width/aspect_ratio
        factor = min(1., 1600/max(out_width, out_height))
        out_width, out_height = int(out_width*factor), int(out_height*factor)
        if min(out_width, out_height) < 80:
            raise StageError('Rectified document is too small to read')
        destination = np.float32([[0, 0], [out_width-1, 0], [out_width-1, out_height-1], [0, out_height-1]])
        matrix = cv2.getPerspectiveTransform(points, destination)
        if not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-12:
            raise StageError('Unstable document perspective transform')
        rectified = cv2.warpPerspective(image, matrix, (out_width, out_height), flags=cv2.INTER_LINEAR)
        warnings = ['reading_direction_unverified']
        if aspect_ratio is None:
            warnings.append('aspect_ratio_estimated_from_edges')
        if detection and detection['ambiguous']:
            warnings.append('competing_document_regions')
        region_crop=bool(detection and detection.get('localization')=='detected_region_crop')
        if region_crop: warnings.append('perspective_not_verified_region_preserved')
        if max(top, bottom)/min(top, bottom) > 2.5 or max(left, right)/min(left, right) > 2.5:
            warnings.append('strong_foreshortening')
        return rectified, dict(corners=points.tolist(), matrix=matrix.tolist(),
            method='detected_region_crop' if region_crop else 'contour_detection' if automatic else 'provided_corners',
            width=out_width, height=out_height, requires_review=automatic,
            orientation='geometric_only', aspect_ratio_source='provided' if aspect_ratio is not None else 'edge_estimate',
            warnings=warnings, detection=detection, rectified_metrics=_rectified_metrics(rectified))
