"""Build a metadata-only historical exposure index and validate prospective fixtures."""
from collections import Counter, defaultdict
from pathlib import Path, PureWindowsPath
import json
import re
import unicodedata

from ..task55.data import PILOT, ROOT, digest, read, save_new, sha
from .intake import EXECUTION, PRIVATE

HEX = re.compile(r"[a-f0-9]{64}\Z")
AXES = ("physical_id", "uid", "file_sha256", "pixel_sha256", "content_sha256")
PUBLIC = {
    "V1": "vlm_lora_v1/dataset_manifest", "V2": "vlm_lora_v2/dataset_manifest",
    "V2-R2": "vlm_lora_v2_r2/dataset_manifest", "V3": "source_visibility_v3/dataset_manifest",
    "V4": "recovery_v4/dataset_manifest", "hard-pair": "hard_pairs_v1/dataset_manifest",
    "fair-controls": "fair_controls_v1/dataset_manifest", "OCR-labels": "ocr_labels_v1/evaluation_manifest",
}
AUTHOR_FIELDS = {
    "V1": ("vlm_lora_v1/samples", None, "value"),
    "V2": ("vlm_lora_v2/samples", "authored", "value"),
    "V2-R2": ("vlm_lora_v2_r2/samples", "authored", "value"),
    "V3": ("source_visibility_v3/samples", "authored", "value"),
    "V4": ("recovery_v4/synthetic_samples", "authored_specimen", "text"),
    "hard-pair": ("hard_pairs_v1/samples", "authored", "value"),
    "fair-controls": ("fair_controls_v1/evaluation", "authored", "value"),
}


def norm(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def sha_token(value):
    return isinstance(value, str) and bool(HEX.fullmatch(value))


def content_fingerprint(fields):
    """Use full fictional author values, never output OCR or visible-only target."""
    if not isinstance(fields, dict) or any(not isinstance(k, str) or not isinstance(v, str)
                                         for k, v in fields.items()):
        raise ValueError("Expected complete string author fields for fictional content")
    keys = [norm(key) for key in fields if norm(key)]
    if len(keys) != len(set(keys)):
        raise ValueError("Ambiguous normalized semantic keys")
    nonempty = {norm(k): norm(v) for k, v in fields.items() if norm(k) and norm(v)}
    if not nonempty:
        raise ValueError("Empty author content cannot establish identity separation")
    return digest(["full-fictional-author-content/1", sorted(nonempty.items())])


def pixel_hash_index(rows):
    result = {}
    for row in rows:
        file_hash, pixel_hash = row["input_sha256"], row["pixel_sha256"]
        if not sha_token(file_hash) or not sha_token(pixel_hash):
            raise ValueError("Malformed historical image fingerprint")
        if file_hash in result and result[file_hash] != pixel_hash:
            raise ValueError("Historical decoded-pixel records conflict")
        result[file_hash] = pixel_hash
    return result


def audit_history(*, include_master=False):
    index = {axis: defaultdict(set) for axis in AXES}
    receipts = {}
    sources = {}
    known_id_by_hash = {}

    def source(path):
        relative = path.relative_to(ROOT).as_posix()
        receipts[relative] = sha(path)
        return read(path)

    def add(axis, token, dataset):
        if token:
            index[axis][norm(token) if axis in ("physical_id", "uid") else token].add(dataset)

    def add_rows(name, rows, pixel_lookup):
        count = Counter()
        roles = Counter()
        ids = set()
        for row in rows:
            roles[row.get("role", "role_unknown")] += 1
            pid, uid = row.get("physical_id"), row.get("uid")
            file_hash = row.get("input_sha256")
            pixel = row.get("pixel_sha256") or pixel_lookup.get(file_hash)
            for axis, token in (("physical_id", pid), ("uid", uid), ("file_sha256", file_hash), ("pixel_sha256", pixel)):
                if token:
                    add(axis, token, name)
                    count[axis] += 1
            if pid:
                ids.add(norm(pid))
                known_id_by_hash.setdefault(digest(pid), pid)
        sources[name] = dict(records=len(rows), by_role=dict(roles), physical_ids=len(ids),
                             coverage=dict(count))

    pixels = source(ROOT / "research/results/fair_controls_v1/pixel_manifest.json")
    pixel_lookup = pixel_hash_index(pixels)
    for name, path in PUBLIC.items():
        rows = source(ROOT / "research/results" / (path + ".json"))
        add_rows(name, rows, pixel_lookup)
    fc_train = source(ROOT / "research/data/fair_controls_v1/train.json")
    add_rows("fair-controls/train", [row for arm in fc_train.values() for row in arm], pixel_lookup)
    for name in ("e2e_ocr_v1", "e2e_ocr_v2"):
        manifest = source(ROOT / "research/results" / name / "manifest.json")
        rows = [dict(uid=uid, input_sha256=value, role="previously_exposed")
                for uid, value in manifest["input_hashes"].items()]
        add_rows(name, rows, pixel_lookup)
    task5 = source(PILOT / "scoring.json")["packs"]
    pixels_task5 = source(PILOT / "inputs.json")["inputs"]
    by_pixel = {}
    for row in task5:
        for key in ("original_pixel_sha256", "input_pixel_sha256"):
            by_pixel.setdefault(row["pair"][key], row["graph"]["physical_id"])
    add_rows("TASK5", [dict(role=row["role"], physical_id=by_pixel[row["pixel_sha256"]],
                           input_sha256=row["file_sha256"], pixel_sha256=row["pixel_sha256"])
                      for row in pixels_task5], pixel_lookup)

    contents = {}
    for name, (path, authored, value_key) in AUTHOR_FIELDS.items():
        rows = source(ROOT / "research/data" / (path + ".json"))
        if name == "fair-controls":
            rows = rows + [r for arm in fc_train.values() for r in arm]
        known = defaultdict(set)
        for row in rows:
            if authored is not None and row.get("source") != authored:
                continue
            fields = {item["key"]: item[value_key] for item in row["fields"]
                      if item.get("key") and isinstance(item.get(value_key), str)}
            if fields:
                known[norm(row["physical_id"])].add(content_fingerprint(fields))
        contents[name] = known
    specs = source(ROOT / "research/data/ocr_labels_v1/render_specs.json")
    contents["OCR-labels"] = {norm(row["physical_id"]): {content_fingerprint(row["values"])} for row in specs}
    contents["TASK5"] = {}
    for pack in task5:
        graph = pack["graph"]
        fields = {f["key"]: f["reference_value"] for f in graph["fields"]}
        contents["TASK5"].setdefault(norm(graph["physical_id"]), set()).add(content_fingerprint(fields))
    if include_master:
        local = PRIVATE / "stage_pilot"
        by_pixel = {r["pixel_sha256"]: r for r in source(local / "inputs.json")}
        stage_rows, stage_contents = [], {}
        for case in source(local / "analysis.json"):
            # The report carries only hashed IDs. Link to an original full
            # development ID only where the author image is already known.
            physical_id = known_id_by_hash.get(case["physical_id_sha256"])
            if physical_id is None:
                physical_id = "physical-sha256:" + case["physical_id_sha256"]
            stage_contents[norm(physical_id)] = {content_fingerprint(case["references"])}
            for variant in case["variants"].values():
                pixel = variant["pixel"]
                request = by_pixel[pixel]
                stage_rows.append(dict(physical_id=physical_id, role=request["role"],
                                       input_sha256=request["file_sha256"], pixel_sha256=pixel))
        add_rows("master/M2-M3", stage_rows, pixel_lookup)
        contents["master/M2-M3"] = stage_contents
        controlled = source(EXECUTION / "controlled_faults.json")["cases"]
        add_rows("master/M1-M7", [dict(role="fixture", pixel_sha256=pixel)
                                 for pixel in sorted({row[key] for row in controlled for key in
                                     ("before_sha256", "input_sha256", "observed_m2_sha256")})], pixel_lookup)
    for name, known in contents.items():
        for tokens in known.values():
            for token in tokens:
                add("content_sha256", token, name)
        sources[name]["content_annotated_physical_ids"] = len(known)
        sources[name]["content_variant_ids"] = sum(len(tokens) > 1 for tokens in known.values())
    safe_index = {axis: {value: sorted(names) for value, names in values.items()} for axis, values in index.items()}
    suffix = "_final" if include_master else ""
    private_path = PRIVATE / ("exposure_index" + suffix + ".json")
    save_new(private_path, safe_index)
    report = dict(status="HISTORICAL_METADATA_CHECKED", scope="local exposure, no model output or new test input read",
                  sources=sources, manifest_sha256=receipts,
                  unique_by_axis={axis: len(values) for axis, values in safe_index.items()},
                  shared_by_axis={axis: sum(len(v) > 1 for v in values.values()) for axis, values in safe_index.items()},
                  index_sha256=sha(private_path), model_pretraining_exposure="unknown",
                  confirmatory_created=False, model_calls=0,
                  limitations=["Unrecorded decoded pixels and source alias equivalence remain unverified",
                               "Authored content matches are conservative where transformed annotation lists vary",
                               "Public external source content is not fingerprinted from private text"])
    save_new(EXECUTION / ("exposure_audit" + suffix + ".json"), report)
    return report


def validate_manifest(manifest, exposure, *, require_fixture=False):
    """Review a draft manifest. Never publishes, approves or generates a test lock."""
    if manifest.get("schema") != "evidence-specimen-draft/1" or manifest.get("state") != "DRAFT_ONLY":
        raise ValueError("Expected a draft specimen manifest")
    if not isinstance(manifest.get("rows"), list) or not manifest["rows"]:
        raise ValueError("Manifest needs specimens")
    blockers = []
    seen = {}
    contents_by_id = {}
    paths = set()
    for i, row in enumerate(manifest["rows"]):
        if not isinstance(row, dict):
            raise ValueError("Expected a specimen metadata object")
        role = row.get("role")
        if role not in ("development", "prospective_confirmatory") or (require_fixture and role != "development"):
            raise ValueError("Illegal specimen role")
        for key in ("uid", "physical_id", "layout", "lineage", "image_relpath", "rights_basis"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError("Missing specimen metadata: " + key)
        path = Path(row["image_relpath"])
        windows = PureWindowsPath(row["image_relpath"])
        path_key = windows.as_posix().casefold()
        if (path.is_absolute() or windows.drive or windows.root or ".." in windows.parts
                or not windows.parts or path_key in paths):
            raise ValueError("Unexpected or duplicate image path")
        paths.add(path_key)
        if row.get("data_policy") != "fictional":
            raise ValueError("Only fictional specimens are in the draft design")
        for key in ("file_sha256", "pixel_sha256", "content_sha256"):
            if not sha_token(row.get(key)):
                raise ValueError("Missing or malformed fingerprint: " + key)
        physical = norm(row["physical_id"])
        if physical in contents_by_id and contents_by_id[physical] != row["content_sha256"]:
            blockers.append(dict(row=i, axis="physical_id", reason="conflicting_author_content_for_identity"))
        contents_by_id[physical] = row["content_sha256"]
        for axis in AXES:
            token = norm(row[axis]) if axis in ("uid", "physical_id") else row[axis]
            names = exposure.get(axis, {}).get(token, [])
            if axis == "physical_id":
                names = sorted(set(names) | set(exposure.get(axis, {}).get("physical-sha256:" + digest(row[axis]), [])))
            if names:
                blockers.append(dict(row=i, axis=axis, reason="historical_overlap", datasets=names))
            old = seen.get((axis, token))
            if old is not None and (old[0] != role or old[1] != norm(row["physical_id"]) or axis == "uid"):
                blockers.append(dict(row=i, axis=axis, reason="cross_role_or_identity_duplicate"))
            seen[(axis, token)] = role, norm(row["physical_id"])
        if any(not isinstance(row.get(key), bool) for key in ("reference_verified", "provenance_verified")):
            raise ValueError("Verification attestations must be boolean")
        if not row["reference_verified"] or not row["provenance_verified"]:
            blockers.append(dict(row=i, reason="verification_pending"))
    return dict(status="BLOCKED" if blockers else "DRAFT_SCHEMA_PASS", rows=len(manifest["rows"]),
                blockers=blockers, confirmatory_ready=False)


def verify_image_files(manifest, root):
    from PIL import Image, ImageOps
    import numpy as np
    from ..source_graph import pixel_sha256
    root = Path(root).resolve()
    for row in manifest["rows"]:
        path = (root / row["image_relpath"]).resolve()
        if not path.is_relative_to(root) or sha(path) != row["file_sha256"]:
            raise ValueError("Specimen path or byte fingerprint mismatch")
        with Image.open(path) as image:
            array = np.asarray(ImageOps.exif_transpose(image).convert("RGB"))
        if pixel_sha256(array) != row["pixel_sha256"]:
            raise ValueError("Specimen decoded-pixel fingerprint mismatch")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-master", action="store_true")
    report = audit_history(include_master=parser.parse_args().include_master)
    print(json.dumps(dict(status=report["status"], sources=len(report["sources"]),
                          unique=report["unique_by_axis"], model_calls=0)))
