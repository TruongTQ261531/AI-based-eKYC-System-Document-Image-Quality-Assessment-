"""Deterministic, development/fixture-only counterfactual pairs.

No completed dataset builder is called, no original is overwritten, and no
model output enters selection. Pixel transforms are independent of the oracle.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import io
import json
from pathlib import Path
import random

import cv2
import numpy as np
from PIL import Image

from .source_graph import EvidenceGraph, State, digest, pixel_sha256, polygon
from .validity import IDENTITY, Mutation, ValidationReport, validate_pair

RESEARCH_ROOT = Path(__file__).resolve().parent
GENERATOR_VERSION = "evidence-pairs/1"


def png_bytes(image):
    stream = io.BytesIO()
    Image.fromarray(image).save(stream, format="PNG", compress_level=6)
    return stream.getvalue()


def _mask_regions(sources, width, height, padding):
    # Reuse HP's declared-source mask geometry, not its absence/legibility oracle.
    # Import is lazy; build/write_capture/preserve/training entry points are never called.
    from research.hp_data import regions_for
    nodes = [dict(key=s.semantic_key, components=[c.geometry for c in s.components if c.role == "value"])
             for s in sources]
    if not nodes:
        return ()
    masks = regions_for(nodes, nodes[0]["key"])
    regions = []
    for q in masks:
        points = np.asarray(q)
        x0, y0 = np.floor(points.min(axis=0)).astype(int) - padding
        x1, y1 = np.ceil(points.max(axis=0)).astype(int) + padding
        # Only mask bounds are clamped; validation still checks original source frame.
        regions.append(polygon(((max(0, x0), max(0, y0)), (min(width-1, x1), max(0, y0)),
                                (min(width-1, x1), min(height-1, y1)), (max(0, x0), min(height-1, y1)))))
    return tuple(regions)


def plan(graph: EvidenceGraph, kind: str, *, target_key: str, retained_key: str | None = None,
         seed: int = 42) -> Mutation:
    if graph.role not in ("fixture", "development"):
        raise ValueError("TASK 3 permits fixture/development roles only")
    target = graph.field(target_key)
    if retained_key:
        graph.field(retained_key)
    rng = random.Random(int(digest([GENERATOR_VERSION, graph.physical_id, kind, seed])[:16], 16))
    width, height = graph.width, graph.height
    if kind == "full":
        return Mutation(kind, "C4", seed, target_key, output_size=(width, height), operator="identity",
                        expected_source_state=((target_key, "SUPPORTED"),))
    if kind in ("single_source_mask", "all_sources_mask", "pair_a_mask", "pair_b_mask"):
        if kind == "single_source_mask":
            sources = [s for s in target.realizations if s.kind == "body"][:1]
            contract, state = "C2", "SUPPORTED"
        else:
            sources = list(target.realizations)
            contract = "C1" if kind == "all_sources_mask" else "C3"
            state = "REMOVED" if target.coverage == "complete" else "UNKNOWN"
        expected = [(target_key, state)]
        if retained_key:
            expected.append((retained_key, "SUPPORTED"))
        masks = _mask_regions(sources, width, height, rng.randrange(1, 3))
        return Mutation(kind, contract, seed, target_key, retained_key,
                        tuple(s.source_id for s in sources), masks, output_size=(width, height),
                        expected_source_state=tuple(expected))
    if kind == "geometry_translate":
        dx, dy = rng.randrange(5, 18), rng.randrange(5, 18)
        return Mutation(kind, "C4", seed, target_key, homography=((1., 0., dx), (0., 1., dy), (0., 0., 1.)),
                        output_size=(width + 2*dx, height + 2*dy), operator="translate_pad",
                        expected_source_state=((target_key, "SUPPORTED"),))
    if kind == "geometry_rotate90":
        return Mutation(kind, "C4", seed, target_key,
                        homography=((0., -1., height-1.), (1., 0., 0.), (0., 0., 1.)),
                        output_size=(height, width), operator="rotate90",
                        expected_source_state=((target_key, "SUPPORTED"),))
    raise ValueError("Unknown generation family: " + kind)


@dataclass(frozen=True)
class Pair:
    case_id: str
    original: np.ndarray
    followup: np.ndarray
    graph: EvidenceGraph
    mutation: Mutation
    validation: ValidationReport

    def metadata(self):
        before, after = png_bytes(self.original), png_bytes(self.followup)
        return dict(schema_version=GENERATOR_VERSION, case_id=self.case_id,
                    document_id=self.graph.document_id, physical_id=self.graph.physical_id,
                    source_id=self.graph.source_id, role=self.graph.role, data_policy=self.graph.data_policy,
                    seed=self.mutation.seed, contract_id=self.mutation.contract_id,
                    original_input_sha256=hashlib.sha256(before).hexdigest(),
                    input_sha256=hashlib.sha256(after).hexdigest(),
                    parent_file_sha256=self.graph.input_file_sha256,
                    original_pixel_sha256=pixel_sha256(self.original),
                    input_pixel_sha256=pixel_sha256(self.followup), graph_sha256=self.graph.sha256,
                    expected_source_state=dict(self.mutation.expected_source_state),
                    observed_source_state={} if not self.validation.after_graph else {
                        f.key: f.state().value for f in self.validation.after_graph.fields},
                    mask_geometry=asdict(self.mutation)["mask_geometry"],
                    transformation=self.mutation.to_dict(), validation=self.validation.to_dict(),
                    expectations_are_not_validity_proofs=True,
                    human_readability_inferred_from_geometry=False)


def generate(image: np.ndarray, graph: EvidenceGraph, mutation: Mutation) -> Pair:
    if graph.role not in ("fixture", "development"):
        raise ValueError("Confirmatory/train/calibration roles are blocked in TASK 3")
    if pixel_sha256(image) != graph.input_pixel_sha256:
        raise ValueError("Input pixels differ from graph")
    original = image.copy()
    if mutation.operator == "mask":
        result = image.copy()
        for q in mutation.mask_geometry:
            cv2.fillConvexPoly(result, np.rint(q).astype(np.int32), mutation.fill)
    elif mutation.operator == "identity":
        result = image.copy()
    elif mutation.operator == "translate_pad":
        result = cv2.warpAffine(image, np.asarray(mutation.homography, dtype=float)[:2], mutation.output_size,
                                flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=mutation.fill)
    elif mutation.operator == "rotate90":
        result = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    else:
        raise ValueError("Unsupported generator operation; validator accepts external reviewed pairs separately")
    report = validate_pair(original, result, graph, mutation)
    original.setflags(write=False)
    result.setflags(write=False)
    case_id = digest([graph.sha256, mutation.to_dict(), pixel_sha256(result)])
    return Pair(case_id, original, result, graph, mutation, report)


def suite(image, graph, a, b, *, seed=42, include_rotation=False):
    """Every planned pair is returned, including invalid/inconclusive attempts."""
    entries = [("full", a, None), ("single_source_mask", a, None), ("all_sources_mask", a, None),
               ("pair_a_mask", a, b), ("pair_b_mask", b, a), ("geometry_translate", b, None)]
    if include_rotation:
        entries.append(("geometry_rotate90", b, None))
    return tuple(generate(image, graph, plan(graph, kind, target_key=target, retained_key=kept, seed=seed))
                 for kind, target, kept in entries)


def write_new_run(destination, pairs, *, run_metadata=None):
    """Exclusive output creation; refuses old namespaces, symlink escapes and PII."""
    destination = Path(destination).resolve()
    if not destination.is_relative_to(RESEARCH_ROOT.resolve()) or destination == RESEARCH_ROOT.resolve():
        raise ValueError("Output must be a new child of research/evidence_contract")
    pairs = tuple(pairs)
    if any(p.graph.role not in ("fixture", "development") for p in pairs):
        raise ValueError("Forbidden data role")
    if any(p.graph.data_policy not in ("fictional", "public_specimen") for p in pairs):
        raise ValueError("Explicit fictional/public-specimen data policy required")
    if len({p.case_id for p in pairs}) != len(pairs):
        raise ValueError("Duplicate case IDs; do not count repeated raster as new cases")
    destination.mkdir(parents=True, exist_ok=False)
    cases = []
    for pair in pairs:
        folder = destination / pair.case_id
        folder.mkdir()
        before, after = png_bytes(pair.original), png_bytes(pair.followup)
        (folder / "original.png").write_bytes(before)
        (folder / "followup.png").write_bytes(after)
        metadata = pair.metadata()
        metadata["original_path"] = f"{pair.case_id}/original.png"
        metadata["followup_path"] = f"{pair.case_id}/followup.png"
        (folder / "case.json").write_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2,
                                                     allow_nan=False) + "\n", encoding="utf-8")
        cases.append(metadata)
    result = dict(generator=GENERATOR_VERSION, cases=cases, metadata=run_metadata or {},
                  model_calls=0, training_steps=0, confirmatory_inputs_opened=0)
    (destination / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2,
                                                        allow_nan=False) + "\n", encoding="utf-8")
    return result
