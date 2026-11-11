"""Validate actual raster mutations, independently of generator expectations.

Pillow rasterizes annotation regions; NumPy checks deletion/preservation. A
geometry certificate is not a human readability label. No SUT output is read.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import math

import numpy as np
from PIL import Image, ImageDraw

from .source_graph import Component, EvidenceGraph, State, digest, pixel_sha256, polygon

IDENTITY = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))


class Validity(str, Enum):
    VALID = "VALID"
    INVALID_TEST = "INVALID_TEST"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class Mutation:
    kind: str
    contract_id: str
    seed: int
    target_key: str
    retained_key: str | None = None
    hidden_source_ids: tuple[str, ...] = ()
    mask_geometry: tuple[tuple[tuple[float, float], ...], ...] = ()
    homography: tuple[tuple[float, float, float], ...] = IDENTITY
    output_size: tuple[int, int] = (0, 0)
    fill: tuple[int, int, int] = (35, 38, 42)
    operator: str = "mask"
    expected_source_state: tuple[tuple[str, str], ...] = ()

    def to_dict(self):
        def audit(value):
            if isinstance(value, dict):
                return {k: audit(v) for k, v in value.items()}
            if isinstance(value, (tuple, list)):
                return [audit(v) for v in value]
            if isinstance(value, float) and not math.isfinite(value):
                return "NONFINITE:" + str(value)
            return value
        return audit(asdict(self))

    @property
    def sha256(self):
        return digest(self.to_dict())


@dataclass(frozen=True)
class ReviewEvidence:
    before_pixel_sha256: str
    after_pixel_sha256: str
    reviewer_ids: tuple[str, ...]
    independent_verified: bool
    # Entries are (source ID, observed original text, observed follow-up text).
    observations: tuple[tuple[str, str, str], ...]
    provenance: str
    decision: str = "preserved"

    def bound_to(self, before, after):
        return (self.before_pixel_sha256 == before and self.after_pixel_sha256 == after
                and self.independent_verified and len(set(self.reviewer_ids)) >= 2
                and bool(self.provenance))


@dataclass(frozen=True)
class ValidationReport:
    status: Validity
    reasons: tuple[str, ...]
    graph_sha256: str
    mutation_sha256: str
    before_pixel_sha256: str
    after_pixel_sha256: str
    mutation: Mutation
    after_graph: EvidenceGraph | None
    measurements: dict
    review_required: tuple[str, ...] = ()
    reference_before_graph: EvidenceGraph | None = None

    def to_dict(self):
        value = asdict(self)
        value["status"] = self.status.value
        value["mutation"] = self.mutation.to_dict()
        return value


def raster(points, width, height) -> np.ndarray:
    """Reference polygon rasterization uses a different library from masks."""
    points = polygon(points)
    canvas = Image.new("1", (width, height))
    ImageDraw.Draw(canvas).polygon(list(points), fill=1)
    return np.asarray(canvas, dtype=bool)


def project(points, matrix):
    q = np.c_[np.asarray(points, dtype=float), np.ones(len(points))] @ matrix.T
    if np.any(np.abs(q[:, 2]) < 1e-10):
        raise ValueError("Projection at infinity")
    return polygon(q[:, :2] / q[:, 2:3])


def _in_frame(points, width, height):
    q = np.asarray(points)
    return bool((q[:, 0] >= 0).all() and (q[:, 0] <= width - 1).all()
                and (q[:, 1] >= 0).all() and (q[:, 1] <= height - 1).all())


def _mapped_geometry(source, matrix):
    return replace(source, components=tuple(replace(c, geometry=project(c.geometry, matrix),
                        glyphs=tuple(project(g, matrix) for g in c.glyphs)) for c in source.components))


def _apply_review(source, review, before_hash, after_hash):
    if not review or not review.bound_to(before_hash, after_hash) or review.decision not in ("preserved", "verified"):
        return source
    entries = [entry for entry in review.observations if entry[0] == source.source_id]
    if len(entries) != 1 or entries[0][1:] != (source.reference_value, source.reference_value):
        return source
    components = tuple(replace(c, availability="available", readability="readable",
                               evidence_basis="human_verified", reviewer_ids=review.reviewer_ids,
                               provenance=review.provenance) if c.availability != "removed" else c
                       for c in source.components)
    return replace(source, components=components)


def validate_pair(original: np.ndarray, followup: np.ndarray, graph: EvidenceGraph,
                  mutation: Mutation, review: ReviewEvidence | None = None) -> ValidationReport:
    """Return invalid/uncertain attempts instead of dropping failed preconditions."""
    reasons, measurements, pending = [], {}, []
    extent_unverified = []
    before_hash = after_hash = ""

    def result(status, after=None):
        reviewed_before = None
        if review and before_hash and after_hash and review.bound_to(before_hash, after_hash):
            reviewed_before = replace(graph, fields=tuple(replace(f, realizations=tuple(
                _apply_review(s, review, before_hash, after_hash) for s in f.realizations)) for f in graph.fields))
        return ValidationReport(status, tuple(dict.fromkeys(reasons)), graph.sha256, mutation.sha256,
                                before_hash, after_hash, mutation, after, measurements,
                                tuple(sorted(set(pending))), reviewed_before)

    try:
        before_hash, after_hash = pixel_sha256(original), pixel_sha256(followup)
        height, width = original.shape[:2]
        out_height, out_width = followup.shape[:2]
        if (before_hash != graph.input_pixel_sha256 or (width, height) != (graph.width, graph.height)):
            reasons.append("original_image_or_graph_hash_mismatch")
            return result(Validity.INVALID_TEST)
        if mutation.output_size != (out_width, out_height):
            reasons.append("output_dimensions_mismatch")
            return result(Validity.INVALID_TEST)
        if mutation.contract_id not in ("C1", "C2", "C3", "C4"):
            reasons.append("unknown_contract")
            return result(Validity.INVALID_TEST)
        if len(mutation.fill) != 3 or any(type(v) is not int or not 0 <= v <= 255 for v in mutation.fill):
            reasons.append("invalid_fill")
            return result(Validity.INVALID_TEST)
        target = graph.field(mutation.target_key)
        if not target.realizations:
            reasons.append("source_annotations_missing")
            pending.append("coverage:" + target.key)
            return result(Validity.INCONCLUSIVE)
        if mutation.retained_key is not None:
            graph.field(mutation.retained_key)
        hidden = set(mutation.hidden_source_ids)
        if len(hidden) != len(mutation.hidden_source_ids):
            reasons.append("duplicate_hidden_source")
            return result(Validity.INVALID_TEST)
        if any(graph.source(sid).semantic_key != target.key for sid in hidden):
            reasons.append("hidden_source_belongs_to_other_field")
            return result(Validity.INVALID_TEST)
        matrix = np.asarray(mutation.homography, dtype=float)
        if matrix.shape != (3, 3) or not np.isfinite(matrix).all() or abs(np.linalg.det(matrix)) < 1e-10:
            reasons.append("invalid_homography")
            return result(Validity.INVALID_TEST)
        if review and not review.bound_to(before_hash, after_hash):
            reasons.append("review_not_bound_or_not_independent")
        if review and review.bound_to(before_hash, after_hash) and review.decision == "invalid":
            reasons.append("independent_review_rejects_precondition")
            return result(Validity.INVALID_TEST)

        fields = []
        if mutation.operator == "mask":
            if (width, height) != (out_width, out_height) or not np.array_equal(matrix, IDENTITY):
                reasons.append("mask_changes_coordinate_frame")
                return result(Validity.INVALID_TEST)
            union = np.zeros((height, width), dtype=bool)
            for q in mutation.mask_geometry:
                if not _in_frame(q, width, height):
                    reasons.append("mask_out_of_frame")
                    return result(Validity.INVALID_TEST)
                union |= raster(q, width, height)
            if not hidden or not union.any():
                reasons.append("empty_mask_intent")
                return result(Validity.INVALID_TEST)
            changed = np.any(original != followup, axis=2)
            measurements.update(mask_pixels=int(union.sum()), changed_pixels=int(changed.sum()),
                                changes_outside_mask=int((changed & ~union).sum()), components={})
            if np.any(changed & ~union):
                reasons.append("pixels_changed_outside_declared_mask")
            if not np.all(followup[union] == np.asarray(mutation.fill, dtype=np.uint8)):
                reasons.append("declared_mask_not_opaque_in_actual_pixels")
            for field in graph.fields:
                sources = []
                for source in field.realizations:
                    components = []
                    for component in source.components:
                        if not _in_frame(component.geometry, width, height):
                            reasons.append("source_annotation_out_of_frame:" + component.component_id)
                            components.append(replace(component, availability="unknown"))
                            continue
                        region = raster(component.geometry, width, height)
                        n = int(region.sum())
                        covered = int((region & union).sum())
                        actual_changes = int((region & changed).sum())
                        glyph_region = np.zeros_like(region)
                        for glyph in component.glyphs:
                            if not _in_frame(glyph, width, height):
                                reasons.append("glyph_support_out_of_frame:" + component.component_id)
                            glyph_region |= raster(glyph, width, height)
                        if np.any(glyph_region & ~region):
                            reasons.append("annotation_excludes_declared_glyph_ink:" + component.component_id)
                        measurements["components"][component.component_id] = dict(
                            pixels=n, mask_covered_pixels=covered, actual_changed_pixels=actual_changes)
                        erased = bool(n and covered == n and np.all(
                            followup[region] == np.asarray(mutation.fill, dtype=np.uint8)))
                        erase_intent = source.source_id in hidden and component.role == "value"
                        removal_reviewed = bool(review and review.bound_to(before_hash, after_hash)
                                                and review.decision in ("removed", "verified")
                                                and (source.source_id, source.reference_value, "") in review.observations)
                        if erase_intent and not component.glyphs and not removal_reviewed:
                            extent_unverified.append(source.source_id)
                        if erase_intent and not erased:
                            reasons.append("target_characters_not_fully_removed:" + component.component_id)
                        if not erase_intent and (covered or actual_changes):
                            reasons.append("collateral_source_or_context_change:" + component.component_id)
                        availability = "removed" if erased and erase_intent else "unknown" if actual_changes else component.availability
                        components.append(replace(component, availability=availability))
                    updated = replace(source, components=tuple(components))
                    updated = _apply_review(updated, review, before_hash, after_hash)
                    sources.append(updated)
                fields.append(replace(field, realizations=tuple(sources)))
            if reasons and any(not r.startswith("review_not_bound") for r in reasons):
                return result(Validity.INVALID_TEST)
            after = replace(graph, fields=tuple(fields), input_pixel_sha256=after_hash)
            if extent_unverified:
                reasons.append("target_ink_extent_requires_independent_review")
                pending.extend(extent_unverified)
                return result(Validity.INCONCLUSIVE, after)
            if mutation.contract_id in ("C1", "C3"):
                if hidden != {s.source_id for s in target.realizations}:
                    reasons.append("all_source_mask_does_not_name_every_declared_source")
                    return result(Validity.INVALID_TEST, after)
            if mutation.contract_id == "C1":
                if after.field(target.key).state() != State.REMOVED:
                    reasons.append("exhaustive_removal_not_proven_by_annotation_scope")
                    pending.append("coverage:" + target.key)
                    return result(Validity.INCONCLUSIVE, after)
            elif mutation.contract_id == "C2":
                if not any(s.kind == "body" and s.source_id in hidden for s in target.realizations):
                    reasons.append("body_source_not_targeted")
                    return result(Validity.INVALID_TEST, after)
                backups = [s for s in after.field(target.key).realizations if s.source_id not in hidden]
                if not any(s.state() == State.SUPPORTED for s in backups) or after.field(target.key).state() != State.SUPPORTED:
                    pending.extend(s.source_id for s in backups if s.state() == State.UNKNOWN)
                    reasons.append("valid_readable_backup_not_verified" if backups else "no_declared_backup_contract_inapplicable")
                    return result(Validity.INCONCLUSIVE, after)
            elif mutation.contract_id == "C3":
                if not mutation.retained_key or mutation.retained_key == target.key:
                    reasons.append("distinct_retained_field_required")
                    return result(Validity.INVALID_TEST, after)
                retained = after.field(mutation.retained_key)
                if retained.state() != State.SUPPORTED:
                    pending.extend(s.source_id for s in retained.realizations)
                    reasons.append("retained_semantics_or_readability_unverified")
                    return result(Validity.INCONCLUSIVE, after)
            else:
                reasons.append("mask_is_not_geometry_contract")
                return result(Validity.INVALID_TEST, after)
        else:
            if mutation.contract_id != "C4" or hidden or mutation.mask_geometry:
                reasons.append("geometry_contract_has_mask_intent")
                return result(Validity.INVALID_TEST)
            exact = False
            if mutation.operator == "identity":
                exact = np.array_equal(matrix, IDENTITY) and np.array_equal(original, followup)
                if not exact:
                    reasons.append("identity_pixels_or_matrix_changed")
                    return result(Validity.INVALID_TEST)
            elif mutation.operator == "translate_pad":
                dx, dy = matrix[0, 2], matrix[1, 2]
                expected_matrix = np.array([[1., 0., dx], [0., 1., dy], [0., 0., 1.]])
                if (not np.array_equal(matrix, expected_matrix) or dx != int(dx) or dy != int(dy)
                        or dx < 0 or dy < 0 or int(dx) + width > out_width or int(dy) + height > out_height):
                    reasons.append("translation_crops_or_resamples_source")
                    return result(Validity.INVALID_TEST)
                expected = np.empty_like(followup)
                expected[:] = mutation.fill
                expected[int(dy):int(dy)+height, int(dx):int(dx)+width] = original
                exact = np.array_equal(expected, followup)
                if not exact:
                    reasons.append("translation_pixels_not_preserved")
                    return result(Validity.INVALID_TEST)
            elif mutation.operator == "rotate90":
                required_matrix = np.array([[0., -1., height - 1.], [1., 0., 0.], [0., 0., 1.]])
                exact = ((out_width, out_height) == (height, width)
                         and np.array_equal(matrix, required_matrix)
                         and np.array_equal(followup, np.transpose(original, (1, 0, 2))[:, ::-1]))
                if not exact:
                    reasons.append("rotation_pixels_or_matrix_not_preserved")
                    return result(Validity.INVALID_TEST)
            measurements["exact_pixel_correspondence"] = exact
            for field in graph.fields:
                sources = []
                for source in field.realizations:
                    updated = _mapped_geometry(source, matrix)
                    if any(not _in_frame(c.geometry, out_width, out_height) for c in updated.components if c.required):
                        reasons.append("geometry_loses_source_region:" + source.source_id)
                    if not exact:
                        updated = replace(updated, components=tuple(replace(c, availability="unknown") for c in updated.components))
                    updated = _apply_review(updated, review, before_hash, after_hash)
                    sources.append(updated)
                fields.append(replace(field, realizations=tuple(sources)))
            after = replace(graph, fields=tuple(fields), width=out_width, height=out_height,
                            input_pixel_sha256=after_hash)
            if any(r.startswith("geometry_loses") for r in reasons):
                return result(Validity.INVALID_TEST, after)
            if after.field(target.key).state() != State.SUPPORTED:
                reasons.append("geometry_text_preservation_unverified")
                pending.extend(s.source_id for s in target.realizations)
                return result(Validity.INCONCLUSIVE, after)
        original_required = graph.field(mutation.retained_key) if mutation.contract_id == "C3" else target
        if original_required.state() == State.UNKNOWN and mutation.contract_id != "C1":
            # A paired human review can establish the original as well as follow-up.
            reviewed = replace(original_required, realizations=tuple(_apply_review(s, review, before_hash, after_hash)
                                                                     for s in original_required.realizations))
            if reviewed.state() != State.SUPPORTED:
                reasons.append("original_reference_support_unverified")
                pending.extend(s.source_id for s in original_required.realizations)
                return result(Validity.INCONCLUSIVE, after)
        if reasons:
            return result(Validity.INCONCLUSIVE, after)
        return result(Validity.VALID, after)
    except (ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        reasons.append("invalid_input:" + type(exc).__name__ + ":" + str(exc))
        return result(Validity.INVALID_TEST)
