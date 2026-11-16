"""Model-independent, GT-free inference records and strict/tolerant validity."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import re

from .source_graph import digest

SCHEMA = "normalized-document-output/1"
FROZEN_READERS = ("rapid_v4", "rapid_latin_v5", "partial_42")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def require_sha(value):
    if not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value):
        raise ValueError("Expected SHA256")


@dataclass(frozen=True)
class ReaderSpec:
    reader_id: str
    model_version: str
    model_sha256: str
    config_json: str
    inference_code_sha256: str
    runtime_json: str
    output_origin: str = "actual_model"

    def __post_init__(self):
        require_sha(self.model_sha256)
        require_sha(self.inference_code_sha256)
        if self.output_origin not in ("actual_model", "oracle_unit_injected"):
            raise ValueError("Unknown output origin")
        if self.output_origin == "actual_model" and self.reader_id not in FROZEN_READERS:
            raise ValueError("Unregistered actual reader: freeze and document another baseline first")
        if not self.reader_id or not self.model_version:
            raise ValueError("Reader ID/version required")
        for value in (self.config_json, self.runtime_json):
            if canonical(json.loads(value)) != value:
                raise ValueError("Config/runtime must be canonical, finite JSON")

    @property
    def config_sha256(self):
        return digest(json.loads(self.config_json))

    @property
    def runtime_sha256(self):
        return digest(json.loads(self.runtime_json))

    @property
    def fingerprint(self):
        return digest(asdict(self))

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class NativeOutput:
    text: str
    wall_seconds: float
    cpu_seconds: float
    runtime: dict
    native_tokens: tuple[dict, ...] = ()
    confidence: float | None = None
    confidence_scope: str | None = None

    def validate(self):
        if not isinstance(self.text, str):
            raise ValueError("Raw text must be a string")
        for value in (self.wall_seconds, self.cpu_seconds):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("Invalid measured time")
        if self.confidence is not None:
            if (isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float))
                    or not self.confidence_scope or not math.isfinite(self.confidence) or not 0 <= self.confidence <= 1):
                raise ValueError("Confidence must be a native, scoped probability-like score")
        blocked = {"embedding", "embeddings", "features", "tensor", "reference_text", "expected_values", "ground_truth"}
        def inspect(value):
            if isinstance(value, dict):
                if any(str(k).casefold() in blocked for k in value):
                    raise ValueError("Reference/embedding data forbidden in inference records")
                for item in value.values(): inspect(item)
            elif isinstance(value, (list, tuple)):
                for item in value: inspect(item)
        inspect(self.runtime)
        for token in self.native_tokens:
            if set(token) != {"text", "confidence", "box"} or not isinstance(token["text"], str):
                raise ValueError("Unexpected native token fields")
            score = token.get("confidence")
            if score is not None and (isinstance(score, bool) or not isinstance(score, (float, int)) or not math.isfinite(score) or not 0 <= score <= 1):
                raise ValueError("Invalid native token confidence")
            if (not isinstance(token['box'], (list, tuple)) or len(token['box']) < 3
                    or any(not isinstance(point, (list, tuple)) or len(point) != 2
                           or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                  or not math.isfinite(v) for v in point) for point in token['box'])):
                raise ValueError("Native OCR box must be a finite polygon")
        canonical(self.to_dict())  # Refuse arrays/tensors and nonfinite values.

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, value):
        data = dict(value)
        data["native_tokens"] = tuple(data.get("native_tokens", ()))
        output = cls(**data)
        output.validate()
        return output


def parse_fields(text):
    """Frozen tolerant-parser behavior, plus explicit RFC nonfinite rejection.

    No semantic aliases, values, or expected keys come from annotation. The
    predictor already used its frozen body-label/MRZ parser when applicable.
    """
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result: raise ValueError("Duplicate key")
            result[key] = value
        return result
    def nonfinite(_):
        raise ValueError("Nonfinite JSON constant")
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Nonfinite parsed JSON number")
        return number
    def load(value):
        parsed = json.loads(value, object_pairs_hook=unique, parse_constant=nonfinite, parse_float=finite_float)
        if not isinstance(parsed, dict): raise ValueError("Not an object")
        return parsed
    try:
        strict = load(text)
        strict_valid = True
        strict_shape = all(isinstance(k, str) and (v is None or isinstance(v, str)) for k, v in strict.items())
    except (ValueError, TypeError):
        strict_valid = strict_shape = False
    fenced = re.fullmatch(r"\s*```(?:json)?\s*\n?(.*?)\n?```\s*", text, re.S | re.I)
    try:
        parsed = load(fenced[1] if fenced else text)
    except (ValueError, TypeError):
        return {}, dict(strict_json_valid=strict_valid, strict_field_shape_valid=strict_shape,
                        tolerant_json_valid=False, fenced=bool(fenced), bad_type_keys=[], null_or_empty_keys=[],
                        usable_for_contracts=False)
    fields, bad, empty = {}, [], []
    for key, value in parsed.items():
        if value is None or isinstance(value, str) and not value.strip():
            empty.append(key)
        elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
            fields[key] = str(value)
        else:
            bad.append(key)
    return fields, dict(strict_json_valid=strict_valid, strict_field_shape_valid=strict_shape,
                       tolerant_json_valid=True, fenced=bool(fenced), bad_type_keys=sorted(bad),
                       null_or_empty_keys=sorted(empty), usable_for_contracts=not bad)


@dataclass(frozen=True)
class NormalizedOutput:
    schema_version: str
    reader_id: str
    model_version: str
    model_sha256: str
    reader_fingerprint: str
    config_sha256: str
    inference_code_sha256: str
    runtime_sha256: str
    input_file_sha256: str
    input_pixel_sha256: str
    cache_key: str
    call_id: str
    output_origin: str
    raw_text: str
    raw_validity: str
    json_validity: dict
    predicted_fields: tuple[dict, ...]
    missing_fields: None
    missing_fields_basis: str
    confidence: float | None
    confidence_scope: str | None
    native_tokens: tuple[dict, ...]
    latency_seconds: float
    cpu_seconds: float
    runtime_metadata: dict
    access_mode: str
    normalization_code_sha256: str

    @property
    def fields(self):
        return {f["semantic_key"]: f["value"] for f in self.predicted_fields}

    def to_dict(self):
        return asdict(self)

    def public(self):
        # Never include text, field values, native OCR boxes, IDs or embeddings.
        names = ("schema_version", "reader_id", "model_version", "model_sha256", "reader_fingerprint",
                 "config_sha256", "inference_code_sha256", "runtime_sha256", "input_file_sha256",
                 "input_pixel_sha256", "cache_key", "call_id", "output_origin", "raw_validity",
                 "latency_seconds", "cpu_seconds", "access_mode", "normalization_code_sha256")
        result = {name: getattr(self, name) for name in names}
        result.update(predicted_field_count=len(self.predicted_fields),
                      strict_json_valid=self.json_validity["strict_json_valid"],
                      tolerant_json_valid=self.json_validity["tolerant_json_valid"],
                      usable_for_contracts=self.json_validity["usable_for_contracts"],
                      native_confidence_available=any(t.get("confidence") is not None for t in self.native_tokens)
                          or self.confidence is not None)
        return result


def normalize(spec, native, *, input_file_sha256, input_pixel_sha256, cache_key, call_id,
              access_mode="fresh"):
    import hashlib
    from pathlib import Path
    native.validate()
    for value in (input_file_sha256, input_pixel_sha256, cache_key): require_sha(value)
    fields, validity = parse_fields(native.text)
    return NormalizedOutput(SCHEMA, spec.reader_id, spec.model_version, spec.model_sha256, spec.fingerprint,
                            spec.config_sha256, spec.inference_code_sha256, spec.runtime_sha256,
                            input_file_sha256, input_pixel_sha256, cache_key, call_id, spec.output_origin,
                            native.text, "completed", validity,
                            tuple(dict(semantic_key=k, value=v, confidence=None, confidence_scope=None)
                                  for k, v in sorted(fields.items())), None, "reference_join_only_after_inference",
                            native.confidence, native.confidence_scope, native.native_tokens,
                            native.wall_seconds, native.cpu_seconds, native.runtime, access_mode,
                            hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
