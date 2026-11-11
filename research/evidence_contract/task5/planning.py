"""Source-conditioned vs strong, validity-filtered uniform random selection.

Both selectors see the SAME candidate pool, annotations, area bins, contracts
and validator. No SUT output, score or reference value enters ranking.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
import itertools
import random

import numpy as np

from ..fixtures import backup_fixture, multiline_fixture, shared_context_fixture, existing_renderer_development
from ..generator import Pair, _mask_regions, generate, plan
from ..source_graph import State, digest
from ..validity import Validity, raster

SEEDS = (42, 31415)
AREA_EDGES = (.01, .04, .12, .35, 1.01)


@dataclass
class Candidate:
    family: str
    case: str
    pair: Pair
    area_fraction: float
    area_bin: int
    source_signature: tuple[str, ...]
    bundle_ni_validity: str | None = None
    bundle_ni_reasons: tuple[str, ...] = ()

    @property
    def eligible(self):
        return self.pair.validation.status == Validity.VALID and self.bundle_ni_validity in (None, "VALID")

    @property
    def uid(self):
        return digest([self.case, self.family, self.pair.graph.sha256, self.pair.mutation.sha256])

    def public(self):
        p = self.pair
        return dict(candidate_id=self.uid, case=self.case, physical_id_sha256=digest(p.graph.physical_id),
                    role=p.graph.role, family=self.family, contract_id=p.mutation.contract_id,
                    target_key=p.mutation.target_key, retained_key=p.mutation.retained_key,
                    area_fraction=self.area_fraction, area_bin=self.area_bin,
                    source_signature=self.source_signature, validity=p.validation.status.value,
                    bundle_ni_validity=self.bundle_ni_validity, bundle_ni_reasons=self.bundle_ni_reasons,
                    selection_admissible=self.eligible,
                    reasons=p.validation.reasons, graph_sha256=p.graph.sha256,
                    mutation_sha256=p.mutation.sha256, original_pixel_sha256=p.validation.before_pixel_sha256,
                    followup_pixel_sha256=p.validation.after_pixel_sha256)


def candidate(case, family, pair):
    graph = pair.graph
    mask = np.zeros((graph.height, graph.width), dtype=bool)
    for q in pair.mutation.mask_geometry:
        mask |= raster(q, graph.width, graph.height)
    fraction = float(mask.mean())
    bin_index = next(i for i, edge in enumerate(AREA_EDGES) if fraction < edge)
    hidden = set(pair.mutation.hidden_source_ids)
    signature = tuple(sorted({s.kind for s in graph.field(pair.mutation.target_key).realizations
                              if (s.source_id not in hidden if family == "backup" else True)}))
    return Candidate(family, case, pair, fraction, bin_index, signature)


def approved_panel():
    """No new natural images, builder calls, train/test reads or model selection."""
    return dict(backup=backup_fixture(), multiline=multiline_fixture(),
                development_0=existing_renderer_development(0))


def pools(panel):
    result = []
    for case, (image, graph, default_a, default_b) in panel.items():
        if graph.role not in ("development", "fixture") or graph.data_policy != "fictional":
            raise ValueError("Pilot panel is restricted to approved fictional fixture/development inputs")
        for field in graph.fields:
            if field.state() != State.SUPPORTED:
                continue
            retained = default_b if field.key != default_b else default_a
            if retained == field.key:
                continue
            for padding in (1, 2, 4):
                mutation = plan(graph, "all_sources_mask", target_key=field.key, seed=42)
                masks = _mask_regions(field.realizations, graph.width, graph.height, padding)
                mutation = replace(mutation, mask_geometry=masks, retained_key=retained, seed=42)
                result.append(candidate(case, "removal_neighbor_bundle", generate(image, graph, mutation)))
                # C2 pool includes every body-containing proper subset, not just
                # an easy primary body mask. Same pool is available to random.
                sources = list(field.realizations)
                if len(sources) > 1 and len(sources) <= 6:
                    for count in range(1, len(sources)):
                        for subset in itertools.combinations(sources, count):
                            if not any(s.kind == "body" for s in subset):
                                continue
                            m = plan(graph, "single_source_mask", target_key=field.key, seed=42)
                            m = replace(m, hidden_source_ids=tuple(s.source_id for s in subset),
                                        mask_geometry=_mask_regions(subset, graph.width, graph.height, padding))
                            result.append(candidate(case, "backup", generate(image, graph, m)))
            for dx, dy in ((5, 7), (12, 16), (20, 11)):
                mutation = plan(graph, "geometry_translate", target_key=field.key, seed=42)
                mutation = replace(mutation, homography=((1., 0., dx), (0., 1., dy), (0., 0., 1.)),
                                   output_size=(graph.width + 2 * dx, graph.height + 2 * dy))
                result.append(candidate(case, "geometry", generate(image, graph, mutation)))
    # A bundle is eligible only when both C1 and its shared-raster C3 witness
    # satisfy the exact same validator. All rejected proposals remain in audit.
    for c in result:
        if c.family == "removal_neighbor_bundle":
            p = c.pair
            ni = generate(p.original, p.graph, replace(p.mutation, kind="pair_a_mask", contract_id="C3"))
            c.bundle_ni_validity = ni.validation.status.value
            c.bundle_ni_reasons = ni.validation.reasons
    return result


def select(candidate_pool, *, arm, seed, seed_index=0, seen=None):
    """Fixed quota: one removal+NI bundle, one geometry per case, one backup.

    Exactly ten paired contracts and ten unique image requests per seed/reader.
    Cache sharing across blocks never buys additional samples/quota.
    """
    if arm not in ("A", "B1"):
        raise ValueError("Unknown selector")
    seen = set() if seen is None else seen
    chosen, ledger = [], []
    groups = sorted({(c.case, c.family) for c in candidate_pool})
    for case, family in groups:
        domain = [c for c in candidate_pool if (c.case, c.family) == (case, family)
                  and c.eligible]
        if not domain:
            continue
        bins = sorted({c.area_bin for c in domain})
        matched_bin = bins[seed_index % len(bins)]
        eligible = sorted([c for c in domain if c.area_bin == matched_bin], key=lambda c: c.uid)
        rng = random.Random(int(digest(["task5-selector/1", seed, case, family])[:16], 16))
        if arm == "B1":
            picked = eligible[rng.randrange(len(eligible))]  # Uniform, no loss-based tuning.
        else:
            def priority(c):
                signature = (c.family, c.source_signature)
                key_coverage = (c.case, c.family, c.pair.mutation.target_key)
                return (signature not in seen, key_coverage not in seen,
                        len(c.source_signature), int(digest([seed, c.uid])[:16], 16))
            picked = max(eligible, key=priority)
        seen.add((family, picked.source_signature))
        seen.add((case, family, picked.pair.mutation.target_key))
        chosen.append(picked)
        ledger.append(dict(arm=arm, seed=seed, case=case, family=family, area_bin=matched_bin,
                           domain_sha256=digest([c.uid for c in eligible]), domain_size=len(eligible),
                           selected_id=picked.uid, selection_uses_model_output=False,
                           selected_area_fraction=picked.area_fraction))
    pairs = []
    for c in chosen:
        pairs.append(c.pair)
        if c.family == "removal_neighbor_bundle":
            p = c.pair
            pairs.append(generate(p.original, p.graph, replace(p.mutation, contract_id="C3", kind="pair_a_mask")))
    pixels = {h for p in pairs for h in (p.validation.before_pixel_sha256, p.validation.after_pixel_sha256)}
    if len(pairs) != 10 or len(pixels) != 10:
        raise ValueError("Matched budget/quota failed; stop before any inference")
    return pairs, ledger


def diagnostics():
    """Predeclared uncertain/invalid attempts; same inputs for every checker."""
    values = []
    for case, data, kind in (
        ("shared_context_loss", shared_context_fixture(), "pair_a_mask"),
        ("limited_source_universe", backup_fixture(limited=True), "all_sources_mask"),
        ("invalid_mrz_backup", backup_fixture(bad_checksum=True), "single_source_mask")):
        image, graph, a, b = data
        m = plan(graph, kind, target_key=a, retained_key=b, seed=42)
        values.append((case, generate(image, graph, m)))
    image, graph, a, b = backup_fixture()
    m = plan(graph, "all_sources_mask", target_key=a, seed=42)
    # Declared all-source mask whose raster misses backup regions: catches a
    # validator error path. It is not labelled a model defect.
    m = replace(m, mask_geometry=m.mask_geometry[:1])
    values.append(("incomplete_target_erasure", generate(image, graph, m)))
    return values
