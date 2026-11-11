"""Typed, conservative adapters for declared visual evidence; no model calls."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from enum import Enum
import hashlib
import json
import re
import unicodedata

import numpy as np

SCHEMA_VERSION = "evidence-graph/1"


class State(str, Enum):
    SUPPORTED = "SUPPORTED"
    REMOVED = "REMOVED"
    UNKNOWN = "UNKNOWN"


def digest(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pixel_sha256(image: np.ndarray) -> str:
    image = np.asarray(image)
    if image.dtype != np.uint8 or image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected an RGB uint8 image")
    header = json.dumps(list(image.shape), separators=(",", ":")).encode()
    return hashlib.sha256(header + b"\0RGB/uint8\0" + image.tobytes()).hexdigest()


def polygon(points) -> tuple[tuple[float, float], ...]:
    from research.labels_schema import polygon as validate_polygon
    return tuple(tuple(float(v) for v in p) for p in validate_polygon(points))


def normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


def date_parts(value: str, kind: str):
    """No century guessing. Return (year, month, day, year precision)."""
    if kind == "date_yymmdd":
        match = re.fullmatch(r"(\d{2})(\d{2})(\d{2})", value)
        if not match:
            match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{2})", value)
            if not match:
                return None
            d, m, y = map(int, match.groups())
        else:
            y, m, d = map(int, match.groups())
        precision = 2
    elif kind == "date_full":
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", value)
        if match:
            y, m, d = map(int, match.groups())
        else:
            match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", value)
            if not match:
                return None
            d, m, y = map(int, match.groups())
        precision = 4
    else:
        return None
    # Validate the calendar without treating a two-digit year as a real century.
    from datetime import date
    try:
        date(y if precision == 4 else 2000 + y, m, d)
    except ValueError:
        return None
    return y, m, d, precision


def compatible(a: str, a_kind: str, b: str, b_kind: str) -> bool:
    if a_kind.startswith("date_") or b_kind.startswith("date_"):
        left, right = date_parts(a, a_kind), date_parts(b, b_kind)
        if left is None or right is None:
            return False
        return (left[0] % 100, *left[1:3]) == (right[0] % 100, *right[1:3]) and (
            min(left[3], right[3]) == 2 or left[0] == right[0])
    return normalized(a) == normalized(b)


@dataclass(frozen=True)
class Condition:
    name: str
    satisfied: bool | None
    provenance: str


@dataclass(frozen=True)
class Component:
    component_id: str
    geometry: tuple[tuple[float, float], ...]
    role: str = "value"
    required: bool = True
    availability: str = "unknown"
    readability: str = "unassessed"
    evidence_basis: str = "geometry_only"
    provenance: str = ""
    reviewer_ids: tuple[str, ...] = ()
    glyphs: tuple[tuple[tuple[float, float], ...], ...] = ()

    def __post_init__(self):
        object.__setattr__(self, "geometry", polygon(self.geometry))
        if self.role not in ("value", "semantic_context"):
            raise ValueError("Unknown component role")
        if self.availability not in ("available", "removed", "unknown"):
            raise ValueError("Unknown availability")
        if self.readability not in ("readable", "unreadable", "partial", "unassessed", "uncertain"):
            raise ValueError("Unknown readability")
        if not self.component_id or not self.provenance:
            raise ValueError("Component ID and provenance required")
        for glyph in self.glyphs:
            polygon(glyph)

    def state(self) -> State:
        if self.availability == "removed":
            return State.REMOVED
        if self.availability != "available":
            return State.UNKNOWN
        if self.evidence_basis == "construction_exact" and self.glyphs:
            # A construction-support claim, explicitly NOT human readability.
            return State.SUPPORTED
        if (self.evidence_basis == "human_verified" and self.readability == "readable"
                and len(set(self.reviewer_ids)) >= 2):
            return State.SUPPORTED
        return State.UNKNOWN


@dataclass(frozen=True)
class Realization:
    source_id: str
    kind: str
    semantic_key: str
    reference_value: str
    components: tuple[Component, ...]
    conditions: tuple[Condition, ...]
    provenance: str
    value_kind: str = "text"
    checksum_required: bool | None = None

    def __post_init__(self):
        if not self.source_id or not self.semantic_key or not self.provenance or not self.components:
            raise ValueError("Explicit semantic key, source ID, components and provenance required")
        if len({c.component_id for c in self.components}) != len(self.components):
            raise ValueError("Duplicate component IDs")
        if len({c.name for c in self.conditions}) != len(self.conditions):
            raise ValueError("Duplicate conditions")
        if self.value_kind not in ("text", "date_full", "date_yymmdd"):
            raise ValueError("Unsupported typed value")

    def valid_conditions(self) -> bool:
        values = {c.name: c.satisfied for c in self.conditions if c.provenance}
        required = ["semantic_link"]
        if self.kind == "mrz":
            required += ["format_valid", "composite_checksum"]
            if self.checksum_required is None:
                return False
            if self.checksum_required:
                required.append("field_checksum")
        return all(values.get(k) is True for k in required) and all(
            c.satisfied is True and bool(c.provenance) for c in self.conditions)

    def state(self) -> State:
        needed = [c for c in self.components if c.required]
        if not needed:
            return State.UNKNOWN
        # Physical deletion is known even if original readability is unassessed.
        if any(c.state() == State.REMOVED for c in needed):
            return State.REMOVED
        if not self.valid_conditions():
            return State.UNKNOWN
        return State.SUPPORTED if all(c.state() == State.SUPPORTED for c in needed) else State.UNKNOWN


@dataclass(frozen=True)
class Field:
    key: str
    reference_value: str
    realizations: tuple[Realization, ...]
    coverage: str = "unknown"
    coverage_provenance: str = ""
    optional: bool = True
    value_kind: str = "text"

    def __post_init__(self):
        if not self.key or not isinstance(self.reference_value, str):
            raise ValueError("Explicit semantic key and reference string required")
        if any(s.semantic_key != self.key for s in self.realizations):
            raise ValueError("Source semantic key differs from field")
        if self.coverage not in ("complete", "limited", "unknown"):
            raise ValueError("Unknown source coverage")
        if self.coverage == "complete" and not self.coverage_provenance:
            raise ValueError("Complete coverage requires provenance")

    def supported_sources(self) -> tuple[Realization, ...]:
        return tuple(s for s in self.realizations if s.state() == State.SUPPORTED)

    def state(self) -> State:
        supported = self.supported_sources()
        if supported:
            if any(not compatible(s.reference_value, s.value_kind,
                                  self.reference_value, self.value_kind) for s in supported):
                return State.UNKNOWN
            return State.SUPPORTED
        if (self.coverage == "complete" and self.realizations
                and all(s.state() == State.REMOVED for s in self.realizations)):
            return State.REMOVED
        return State.UNKNOWN


@dataclass(frozen=True)
class EvidenceGraph:
    document_id: str
    physical_id: str
    source_id: str
    role: str
    width: int
    height: int
    input_pixel_sha256: str
    fields: tuple[Field, ...]
    data_policy: str = "unknown"
    input_file_sha256: str | None = None
    unmapped_fields: tuple[str, ...] = ()
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self):
        if not self.document_id or not self.physical_id or not self.source_id:
            raise ValueError("Document, physical and source IDs required")
        if self.width <= 0 or self.height <= 0 or not re.fullmatch("[a-f0-9]{64}", self.input_pixel_sha256):
            raise ValueError("Image dimensions and SHA256 required")
        if len({f.key for f in self.fields}) != len(self.fields):
            raise ValueError("Duplicate semantic fields; put alternatives in realizations")
        sources = [s.source_id for f in self.fields for s in f.realizations]
        components = [c.component_id for f in self.fields for s in f.realizations for c in s.components]
        if len(sources) != len(set(sources)) or len(components) != len(set(components)):
            raise ValueError("Source/component IDs must be graph-unique")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("Unknown graph schema")

    def field(self, key: str) -> Field:
        for item in self.fields:
            if item.key == key:
                return item
        raise KeyError(key)

    def source(self, source_id: str) -> Realization:
        for field in self.fields:
            for source in field.realizations:
                if source.source_id == source_id:
                    return source
        raise KeyError(source_id)

    def to_dict(self):
        return asdict(self)

    @property
    def sha256(self):
        return digest(self.to_dict())

    @classmethod
    def from_dict(cls, value):
        data = dict(value)
        fields = []
        for raw in data.pop("fields"):
            field = dict(raw)
            sources = []
            for entry in field.pop("realizations"):
                source = dict(entry)
                components = []
                for raw_component in source.pop("components"):
                    component = dict(raw_component)
                    component["reviewer_ids"] = tuple(component.get("reviewer_ids", ()))
                    component["glyphs"] = tuple(polygon(g) for g in component.get("glyphs", ()))
                    components.append(Component(**component))
                source["components"] = tuple(components)
                source["conditions"] = tuple(Condition(**c) for c in source["conditions"])
                sources.append(Realization(**source))
            fields.append(Field(**field, realizations=tuple(sources)))
        data["unmapped_fields"] = tuple(data.get("unmapped_fields", ()))
        return cls(**data, fields=tuple(fields))


def from_legacy_nodes(*, document_id, physical_id, source_id, role, image, nodes,
                      mrz_checks=None, data_policy="unknown") -> EvidenceGraph:
    """Read-only V3/HP adapter. Geometry alone is NEVER promoted to legibility."""
    grouped = {}
    for i, node in enumerate(nodes):
        key = node.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("Legacy node has no declared semantic key")
        provenance = str(node.get("author_source", ""))
        sid = f"{source_id}/source/{i}"
        mrz = provenance.startswith("mrz_line")
        kind = "mrz" if mrz else "duplicated_body" if node.get("kind") == "body_duplicate" else "body"
        conditions = [Condition("semantic_link", True, "legacy explicit key mapping")]
        required = None
        if mrz:
            checks = mrz_checks or {}
            required = key in ("id_number", "dob", "expiry_date", "personal_number")
            conditions += [Condition("format_valid", checks.get("format_valid"), "strict TD3 parser"),
                           Condition("composite_checksum", checks.get("composite"), "TD3 check digit")]
            if required:
                conditions.append(Condition("field_checksum", node.get("checksum_valid"), "TD3 field check digit"))
        components = tuple(Component(f"{sid}/component/{j}", polygon(q),
                                     provenance=provenance or "legacy node: source unknown")
                           for j, q in enumerate(node["components"]))
        value_kind = "date_yymmdd" if node.get("kind") == "date_yymmdd" else "text"
        if key in ("dob", "expiry_date", "issue_date") and date_parts(node["value"], "date_full"):
            value_kind = "date_full"
        source = Realization(sid, kind, key, node["value"], components, tuple(conditions),
                             provenance or "legacy mapping", value_kind, required)
        grouped.setdefault(key, []).append(source)
    fields = []
    for key, sources in grouped.items():
        ref = next((s for s in sources if s.value_kind != "date_yymmdd"), sources[0])
        fields.append(Field(key, ref.reference_value, tuple(sources), "limited",
                            "Legacy annotations do not certify exhaustive sources", value_kind=ref.value_kind))
    return EvidenceGraph(document_id, physical_id, source_id, role, image.shape[1], image.shape[0],
                         pixel_sha256(image), tuple(fields), data_policy)


def from_v3_source(source, image, *, role=None, data_policy=None):
    from research.v3_sources import source_graph
    if role is not None and source.get("role") is not None and role != source["role"]:
        raise ValueError("Adapter cannot relabel a source data role")
    resolved_role = source.get("role") or role or "unassigned"
    resolved_policy = source.get("data_policy", "unknown") if data_policy is None else data_policy
    if source.get("data_policy") is not None and source["data_policy"] != resolved_policy:
        raise ValueError("Adapter cannot relabel a source data policy")
    nodes, metadata = source_graph(source)
    checks = dict(metadata.get("checks", {}), format_valid=bool(metadata.get("mrz_parsed")))
    return from_legacy_nodes(document_id=source["physical_id"], physical_id=source["physical_id"],
                             source_id=source["physical_id"], role=resolved_role, image=image, nodes=nodes,
                             mrz_checks=checks, data_policy=resolved_policy)


def from_hp_full(full, image):
    from research.hp_data import nodes_for
    graph = from_legacy_nodes(document_id=full["uid"], physical_id=full["physical_id"],
                              source_id=full["physical_id"], role=full["role"], image=image,
                              nodes=nodes_for(full), data_policy=full.get("data_policy", "unknown"))
    # HP ANDs the value with its label. Preserve the label as semantic context.
    fields = []
    for field in graph.fields:
        sources = tuple(replace(s, components=tuple(replace(c, role="semantic_context" if j else "value")
                                                    for j, c in enumerate(s.components))) for s in field.realizations)
        fields.append(replace(field, realizations=sources))
    return replace(graph, fields=tuple(fields))


def from_label_record(record, image, *, construction_scope=None):
    """OCR-label adapter; unknown semantic keys stay unknown, never positional."""
    if construction_scope and record.get("data_policy") != "fictional":
        raise ValueError("Construction scope requires an explicitly fictional source record")
    fields, unmapped = [], []
    for i, field in enumerate(record["fields"]):
        key = field.get("semantic_key")
        if not key:
            unmapped.append(str(field.get("raw_key", i)))
            continue
        sid = f"{record['uid']}/source/{i}"
        constructed = bool(construction_scope and field.get("geometry_origin") == "renderer_ink"
                           and field.get("glyphs") and field.get("construction_visibility", {}).get("status") == "ink_visible")
        glyphs = tuple(polygon(g["polygon"]) for g in field.get("glyphs", ()))
        component = Component(f"{sid}/value", polygon(field["polygon"]), availability="available" if constructed else "unknown",
                              evidence_basis="construction_exact" if constructed else "geometry_only",
                              provenance=construction_scope or "author geometry, not human review", glyphs=glyphs)
        components = [component]
        if field.get("label_box") is not None:
            from research.hp_data import rect_quad
            q = polygon(rect_quad(field["label_box"]))
            components.append(Component(f"{sid}/label", q, role="semantic_context",
                                        availability="available" if constructed else "unknown",
                                        evidence_basis="construction_exact" if constructed else "geometry_only",
                                        provenance=construction_scope or "author label geometry", glyphs=(q,) if constructed else ()))
        kind = "date_full" if date_parts(field["reference_text"], "date_full") else "text"
        realization = Realization(sid, "body", key, field["reference_text"], tuple(components),
                                  (Condition("semantic_link", True, "explicit renderer/author semantic key"),),
                                  construction_scope or "OCR labels annotation", kind)
        fields.append(Field(key, field["reference_text"], (realization,),
                            "complete" if constructed else "limited", construction_scope or "annotation scope incomplete",
                            value_kind=kind))
    if unmapped:
        fields = [replace(f, coverage="limited", coverage_provenance="Unmapped native fields may contain other sources") for f in fields]
    return EvidenceGraph(record["uid"], record["physical_id"], record.get("provider_record", record["uid"]),
                         record["role"], image.shape[1], image.shape[0], pixel_sha256(image), tuple(fields),
                         "fictional" if construction_scope else record.get("data_policy", "unknown"),
                         record.get("input_sha256"), tuple(unmapped))
