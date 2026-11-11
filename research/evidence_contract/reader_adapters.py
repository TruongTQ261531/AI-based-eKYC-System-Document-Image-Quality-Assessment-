"""Read-only adapters to the published labels-study pixel-only predictors.

No setup, download, training, legacy cache lookup or legacy study run is called.
Inference accepts one RGB image, never a graph, key, polygon or answer.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path
import sys
import zipfile

from .normalized_output import FROZEN_READERS, NativeOutput, ReaderSpec, canonical
from .source_graph import digest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "research/results/ocr_labels_v1/models.json"
FROZEN_MANIFEST_SHA = "d8d0cf34bf556d2d2ac36f5f0506560afc23d491f85970c1d9cd8a348998b871"
BASELINE_CODE = ("labels_study.py", "labels_common.py", "labels_schema.py", "labels_metrics.py",
                 "recovery_runtime.py", "recovery_assets.py", "recovery_geometry.py",
                 "v2_cpu.py", "v3_cpu.py", "v3_metrics.py", "v3_sources.py",
                 "v2_inputs.py", "v2_runtime.py", "v2_common.py", "vlm_runtime.py",
                 "vlm_setup.py", "vlm_data.py")


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _check(path, expected):
    if not Path(path).is_file() or file_sha(path) != expected:
        raise ValueError("Missing/changed frozen asset: " + str(path))


def readonly_rapid_package():
    """Verify existing extraction; refuse repair of any old cache member."""
    from research import recovery_assets
    wheel = recovery_assets.CACHE / "rapidocr-1.4.4.whl"
    _check(wheel, recovery_assets.WHEEL_SHA)
    target = (recovery_assets.CACHE / "rapid144").resolve()
    members = {}
    with zipfile.ZipFile(wheel) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            path = (target / item.filename).resolve()
            if not path.is_relative_to(target) or item.file_size > 20_000_000:
                raise ValueError("Unsafe wheel member")
            expected = hashlib.sha256(archive.read(item)).hexdigest()
            _check(path, expected)
            members[item.filename] = expected
    if str(target) not in sys.path:
        sys.path.insert(0, str(target))
    return target, digest(members)


def specification(reader_id):
    """Preflight hashes/packages before loading a reader. No model execution."""
    if reader_id not in FROZEN_READERS:
        raise ValueError("Reader not registered in the frozen baseline")
    _check(MANIFEST, FROZEN_MANIFEST_SHA)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if (manifest["profile"], manifest["seed"], manifest["max_new_tokens"], manifest["host_threads"]) != (
            "rect2", 42, 384, 2):
        raise ValueError("Frozen baseline configuration changed")
    for name, expected in manifest["reused_sources"].items():
        _check(ROOT / "research" / name, expected)
    # The baseline imports RapidOCR from its existing verified wheel extraction.
    # Its dist-info becomes discoverable only after adding that exact path.
    package, package_sha = readonly_rapid_package()
    packages = {p: importlib.metadata.version(p) for p in manifest["packages"]}
    if packages != manifest["packages"]:
        raise ValueError("Use the existing frozen overlay runtime; package versions differ")
    for key, value in dict(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", OMP_NUM_THREADS="2",
                           MKL_NUM_THREADS="2", CUBLAS_WORKSPACE_CONFIG=":4096:8").items():
        if os.environ.get(key) != value:
            raise ValueError("Frozen offline runtime variable differs: " + key)
    weights = {}
    for weight in manifest["onnx_weights"]:
        path = Path(weight["path"])
        _check(path, weight["sha256"])
        weights[path.name] = weight["sha256"]
    assets = dict(active_reader=reader_id, onnx_weights=weights, rapid_package_sha256=package_sha)
    from research.v2_common import PROMPT, CONFIG
    if CONFIG["generation_max_new_tokens"] != 384:
        raise ValueError("Frozen generation limit changed")
    runtime = dict(python=platform.python_version(), platform=platform.platform(),
                   packages=packages, execution="CUDA" if reader_id == "partial_42" else "CPU",
                   omp_threads="2", mkl_threads="2", offline=True)
    if reader_id == "partial_42":
        base_manifest = ROOT / "research/results/vlm_lora_v1/assets.json"
        _check(base_manifest, manifest["base_assets_sha256"])
        base = json.loads(base_manifest.read_text(encoding="utf-8"))
        # The legacy loader would create this file if absent. Never allow that path.
        if not (ROOT / "research/results/vlm_lora_v1/training_environment.json").is_file():
            raise ValueError("Legacy environment record missing; refusing a legacy write")
        adapter = ROOT / manifest["adapter_path"]
        _check(adapter / "adapter_model.safetensors", manifest["adapter_sha256"])
        _check(adapter / "adapter_config.json", manifest["adapter_config_sha256"])
        # The frozen loader verifies its model_files again. Stream here to avoid large allocations.
        model_dir = ROOT / "research/cache/vlm_lora_v1/model"
        for record in base["model"]:
            path = model_dir / record["file"]
            if record.get("sha256"):
                _check(path, record["sha256"])
            else:
                blob = hashlib.sha1()
                blob.update(f"blob {path.stat().st_size}\0".encode())
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        blob.update(block)
                if blob.hexdigest() != record["git_blob"]:
                    raise ValueError("Pinned base model source changed")
        assets.update(base_assets_sha256=manifest["base_assets_sha256"],
                      adapter_sha256=manifest["adapter_sha256"],
                      adapter_config_sha256=manifest["adapter_config_sha256"])
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("partial_42 requires its frozen CUDA runtime")
        runtime.update(gpu=torch.cuda.get_device_name(0), cuda=torch.version.cuda,
                       capability=list(torch.cuda.get_device_capability(0)),
                       dtype="bfloat16" if torch.cuda.is_bf16_supported() else "float16")
    else:
        import onnxruntime as ort
        runtime["available_providers"] = ort.get_available_providers()
        runtime["used_provider"] = "CPUExecutionProvider"
    # Conservative closure also covers imported geometry/schema/prompt helpers.
    code = {p.relative_to(ROOT).as_posix(): file_sha(p) for p in (ROOT / "research").glob("*.py")}
    # Include all helpers of the frozen pipelines, not the oracle/normalizer.
    for path in (ROOT / "ekyc").rglob("*.py"):
        code[path.relative_to(ROOT).as_posix()] = file_sha(path)
    code["reader_adapters.py"] = file_sha(__file__)
    code["runner.py"] = file_sha(Path(__file__).with_name("runner.py"))
    if reader_id == "partial_42":
        for path in model_dir.glob("*.py"):
            code["reviewed_model/" + path.name] = file_sha(path)
    config = dict(baseline_manifest_sha256=file_sha(MANIFEST), profile="rect2", seed=42,
                  host_threads=2, max_new_tokens=384 if reader_id == "partial_42" else None,
                  prompt_sha256=hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()
                      if reader_id == "partial_42" else None,
                  detector_limit_side_len=960 if reader_id != "partial_42" else None,
                  detector_limit_type="max" if reader_id != "partial_42" else None,
                  stateful_context=False, baseline_entry_point="research.labels_study.predictor",
                  version_policy="no model, prompt, parser or preprocessing changes")
    version = "Vintern-1B-v3_5/partial_42/step_0320" if reader_id == "partial_42" else (
        "RapidOCR-ONNX-1.4.4/PP-OCRv4" if reader_id == "rapid_v4" else
        "RapidOCR-ONNX-1.4.4/Latin-PP-OCRv5-rec/shared-v4-det-cls")
    return ReaderSpec(reader_id, version, digest(assets), canonical(config), digest(code), canonical(runtime))


def load_predictor(spec):
    """Return a pixels-only closure. No annotation parameter exists."""
    current = specification(spec.reader_id)
    if current != spec:
        raise ValueError("Runtime/reader changed between preflight and loading")
    # Replace only the optional extraction hook with a read-only verification hook.
    # Same verified package, algorithms and settings; no repair side effects.
    from research import recovery_runtime
    recovery_runtime.prepare = lambda: readonly_rapid_package()[0]
    from research.labels_study import predictor
    predict = predictor(spec.reader_id)

    def pixels_only(rgb):
        from PIL import Image
        import numpy as np
        output = predict(Image.fromarray(np.asarray(rgb, dtype=np.uint8), "RGB"))
        tokens = []
        for row in output.get("_private_boxes", ()):
            tokens.append(dict(text=str(row["text"]), confidence=float(row["confidence"]),
                               box=row["box"]))
        allowed = ("generated_tokens", "visual_features_cached", "predictor_receives",
                   "peak_allocated_bytes", "peak_reserved_bytes", "profile", "fallback",
                   "rectified", "source", "strict_mrz", "mrz_valid")
        metadata = {key: output[key] for key in allowed if key in output}
        metadata.update(predictor_receives="pixels_only", baseline_config_frozen=True)
        result = NativeOutput(output["text"], float(output["wall_seconds"]),
                              float(output["cpu_seconds"]), metadata, tuple(tokens))
        result.validate()
        return result
    return pixels_only
