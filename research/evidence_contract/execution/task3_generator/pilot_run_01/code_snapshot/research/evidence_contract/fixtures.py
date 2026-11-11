"""Fictional development fixtures; reuse existing render helpers in memory only."""
from dataclasses import replace
import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .source_graph import (Component, Condition, EvidenceGraph, Field, Realization,
                           from_label_record, pixel_sha256, polygon)


def _quad(box):
    a, b, c, d = box
    return polygon(((a, b), (c, b), (c, d), (a, d)))


def _font(size):
    path = Path("C:/Windows/Fonts/consola.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)


def draw_component(image, text, x, y, cid, *, role="value", size=24):
    from research.labels_synth import ink_patch
    font = _font(size)
    mask, glyphs = ink_patch(text, font)
    px, py = x - 8, y - 8
    image.paste((12, 22, 28), (px, py), mask)
    a, b, c, d = mask.getbbox()
    support = tuple(_quad((px+g["box"][0], py+g["box"][1], px+g["box"][2], py+g["box"][3])) for g in glyphs)
    return Component(cid, _quad((px+a, py+b, px+c, py+d)), role=role,
                     availability="available", evidence_basis="construction_exact",
                     provenance="labels_synth.ink_patch; explicit fictional renderer source inventory",
                     glyphs=support)


def _source(sid, key, value, components, *, kind="body", conditions=None, value_kind="text",
            checksum_required=None):
    return Realization(sid, kind, key, value, tuple(components),
                       tuple(conditions or (Condition("semantic_link", True, "explicit fixture schema/labels"),)),
                       "fictional fixture renderer", value_kind, checksum_required)


def _field(key, value, sources, *, coverage="complete", value_kind="text"):
    return Field(key, value, tuple(sources), coverage,
                 "Complete fictional renderer inventory including labels and MRZ" if coverage == "complete" else
                 "Deliberate incomplete annotation: backup exists outside declared graph", value_kind=value_kind)


def _graph(name, image, fields):
    pixels = np.asarray(image).copy()
    graph = EvidenceGraph(name, name, name + "/render", "fixture", pixels.shape[1], pixels.shape[0],
                          pixel_sha256(pixels), tuple(fields), "fictional")
    return pixels, graph


def backup_fixture(*, limited=False, bad_checksum=False):
    from research.v3_sources import check_digit, parse_td3, span_quad
    image = Image.new("RGB", (1000, 560), (245, 247, 239))
    draw = ImageDraw.Draw(image)
    draw.text((25, 20), "FICTIONAL CONTRACT FIXTURE - NOT AN ID DOCUMENT", font=_font(21), fill=(20, 50, 75))
    key, value, neighbor, kept = "id_number", "DEMO12345", "school", "RESEARCH SCHOOL"
    label_a = draw_component(image, "DOCUMENT NUMBER", 45, 90, "body/a/label", role="semantic_context", size=18)
    body = draw_component(image, value, 45, 120, "body/a/value")
    label_b = draw_component(image, "SCHOOL", 45, 180, "body/b/label", role="semantic_context", size=18)
    school = draw_component(image, kept, 45, 210, "body/b/value")
    duplicate = draw_component(image, value, 630, 120, "duplicate/a/value")
    first = ("P<UTO" + "DEMO<<UNIT<SAMPLE").ljust(44, "<")
    dob, expiry, optional = "990101", "350101", "LOCAL01".ljust(14, "<")
    second = value + check_digit(value) + "UTO" + dob + check_digit(dob) + "F" + expiry + check_digit(expiry)
    second += optional + check_digit(optional)
    second += check_digit(second[:10] + second[13:20] + second[21:43])
    if bad_checksum:
        second = second[:9] + str((int(second[9]) + 1) % 10) + second[10:]
    parsed = parse_td3(first, second)
    draw_component(image, first, 45, 390, "mrz/line0", size=18)
    full_line = draw_component(image, second, 45, 426, "mrz/line1", size=18)
    # Use strict V3 TD3 parsing and its projective character-span helper. The
    # independent glyph inventory determines the actual enclosing strip bounds.
    cell = float(_font(18).getlength("A"))
    ys = [p[1] for glyph in full_line.glyphs for p in glyph]
    strip = ((45, min(ys)-1), (45+44*cell, min(ys)-1), (45+44*cell, max(ys)+1), (45, max(ys)+1))
    mrz_region = polygon(span_quad(strip, 0, 9))
    mrz_component = replace(full_line, component_id="mrz/a/value", geometry=mrz_region,
                            glyphs=full_line.glyphs[:9], provenance="strict TD3 span + actual rendered glyph polygons")
    conditions = (Condition("semantic_link", True, "fixture field id_number explicitly linked to TD3 document number"),
                  Condition("format_valid", parsed is not None, "v3_sources.parse_td3"),
                  Condition("composite_checksum", parsed["checks"]["composite"], "TD3 composite check digit"),
                  Condition("field_checksum", parsed["checks"]["id_number"], "TD3 field check digit"))
    sources = [_source("body/a", key, value, (body, label_a)),
               _source("duplicate/a", key, value, (duplicate,), kind="duplicated_body"),
               _source("mrz/a", key, value, (mrz_component,), kind="mrz", conditions=conditions, checksum_required=True)]
    if bad_checksum:
        q = np.asarray(duplicate.geometry)
        x0, y0 = np.floor(q.min(axis=0)).astype(int) - 2
        x1, y1 = np.ceil(q.max(axis=0)).astype(int) + 2
        ImageDraw.Draw(image).rectangle((int(x0), int(y0), int(x1), int(y1)), fill=(245, 247, 239))
        sources = [sources[0], sources[2]]
    if limited:
        sources = sources[:1]
    fields = [_field(key, value, sources, coverage="limited" if limited else "complete"),
              _field(neighbor, kept, [_source("body/b", neighbor, kept, (school, label_b))])]
    name = "fixture/backup-limited" if limited else "fixture/backup-bad-checksum" if bad_checksum else "fixture/backup"
    pixels, graph = _graph(name, image, fields)
    if limited:
        graph = replace(graph, physical_id="fixture/backup", source_id="fixture/backup/render")
    return pixels, graph, key, neighbor


def multiline_fixture():
    image = Image.new("RGB", (1000, 560), (245, 247, 239))
    label = draw_component(image, "ADDRESS", 40, 80, "address/label", role="semantic_context", size=18)
    first = draw_component(image, "FICTIONAL ROAD", 40, 120, "address/line1")
    second = draw_component(image, "DEMO CITY", 40, 165, "address/line2")
    other_label = draw_component(image, "SCHOOL", 40, 240, "school/label", role="semantic_context", size=18)
    other = draw_component(image, "RESEARCH SCHOOL", 40, 280, "school/value")
    fields = [_field("address", "FICTIONAL ROAD DEMO CITY", [_source("address", "address", "FICTIONAL ROAD DEMO CITY", (first, second, label))]),
              _field("school", "RESEARCH SCHOOL", [_source("school", "school", "RESEARCH SCHOOL", (other, other_label))])]
    pixels, graph = _graph("fixture/multiline", image, fields)
    return pixels, graph, "address", "school"


def shared_context_fixture():
    image = Image.new("RGB", (1000, 560), (245, 247, 239))
    a = draw_component(image, "CATEGORY ONE", 50, 100, "category/value")
    b = draw_component(image, "DEMO CODE", 50, 160, "code/value")
    # A's value is genuinely needed to interpret B's key, even if B pixels stay.
    context = replace(a, component_id="code/context", role="semantic_context")
    fields = [_field("category", "CATEGORY ONE", [_source("category", "category", "CATEGORY ONE", (a,))]),
              _field("category_code", "DEMO CODE", [_source("code", "category_code", "DEMO CODE", (b, context))])]
    pixels, graph = _graph("fixture/shared-semantic-context", image, fields)
    return pixels, graph, "category", "category_code"


def existing_renderer_development(index):
    """Never call labels_synth.build(), save(), or progress()."""
    if not 0 <= index < 8:
        raise ValueError("Only pre-existing development specifications may be rendered")
    from research.labels_synth import CONDITIONS, render, specification
    spec = specification(index)
    if spec["role"] != "development":
        raise ValueError("Development role expected")
    image, fields, metadata = render(spec, CONDITIONS[index % 2], "full")
    pixels = np.asarray(image).copy()
    record = dict(uid=spec["physical_id"] + "/evidence-task3/" + CONDITIONS[index % 2],
                  physical_id=spec["physical_id"], role="development", source="labels_synth_existing_renderer",
                  fields=fields)
    graph = from_label_record(record, pixels, construction_scope="labels_synth.render full; existing development spec; in-memory only")
    a = "id_number" if "id_number" in spec["keys"] else "student_id"
    b = "full_name"
    return pixels, graph, a, b


def development_fixtures():
    return (backup_fixture(), backup_fixture(limited=True), backup_fixture(bad_checksum=True),
            multiline_fixture(), shared_context_fixture(),
            *(existing_renderer_development(i) for i in range(3)))
