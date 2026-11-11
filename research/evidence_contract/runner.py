"""Content-addressed, resumable pixels-only reader execution and raw replay.

Only image-reader invocations have inference_begin events. Loading, cache hits,
normalization and scoring never masquerade as fresh neural inference.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

import numpy as np
from PIL import Image, ImageOps

from .normalized_output import NativeOutput, ReaderSpec, canonical, normalize, require_sha
from .source_graph import digest, pixel_sha256

EC_ROOT = Path(__file__).resolve().parent


def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@dataclass(frozen=True)
class InputRequest:
    path: str
    file_sha256: str
    pixel_sha256: str
    role: str
    data_policy: str

    def load(self):
        # Policy is checked BEFORE opening an image, not inferred from its filename.
        if self.role not in ("fixture", "development"):
            raise ValueError("Only fixture/development inputs are permitted in TASK 4")
        if self.data_policy not in ("fictional", "public_specimen"):
            raise ValueError("Unknown/personal data policy is blocked")
        require_sha(self.file_sha256)
        require_sha(self.pixel_sha256)
        path = Path(self.path)
        if sha_file(path) != self.file_sha256:
            raise ValueError("Input file hash mismatch")
        with Image.open(path) as image:
            rgb = np.array(ImageOps.exif_transpose(image).convert("RGB"), dtype=np.uint8)
        if pixel_sha256(rgb) != self.pixel_sha256:
            raise ValueError("Decoded input pixel hash mismatch")
        return rgb


@contextmanager
def exclusive_lock(path, timeout=30.):
    """Persistent OS lock file; OS releases the lock on a crashed process."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError("Reader/cache lock is busy")
                time.sleep(.05)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def write_once(path, value):
    """Atomic create without overwriting any previous cache/report."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("xb") as stream:
            stream.write((canonical(value) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        if os.name == "nt":
            # Windows rename is atomic and refuses an existing destination.
            # Hard-link creation is unavailable under some managed Windows accounts.
            os.rename(temp, path)
        else:
            os.link(temp, path)  # POSIX rename would overwrite; link refuses to.
    finally:
        if temp.exists():
            temp.unlink()  # Only this invocation's private temporary file.


class EventLog:
    """Append-only JSONL with a hash chain. No model text or GT is logged."""
    def __init__(self, store):
        self.store = Path(store)
        self.path = self.store / "events.jsonl"

    def read(self):
        if not self.path.exists():
            return []
        values, previous = [], "0" * 64
        data = self.path.read_bytes()
        if data and not data.endswith(b"\n"):
            raise ValueError("Truncated event log; preserve it and audit before retry")
        for line in data.splitlines():
            row = json.loads(line)
            check = dict(row)
            actual = check.pop("event_sha256")
            if check["previous_sha256"] != previous or digest(check) != actual:
                raise ValueError("Event log hash chain mismatch")
            values.append(row)
            previous = actual
        return values

    def append(self, event, **metadata):
        allowed = {"cache_key", "call_id", "reader_id", "reader_fingerprint", "output_origin",
                   "input_file_sha256", "input_pixel_sha256", "elapsed_seconds", "error_type",
                   "run_id", "payload_sha256"}
        if set(metadata) - allowed:
            raise ValueError("Unexpected event metadata; text and annotations are forbidden")
        self.store.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(self.store / "locks/events.lock"):
            rows = self.read()
            row = dict(event=event, timestamp_utc=datetime.now(timezone.utc).isoformat(),
                       sequence=len(rows) + 1, previous_sha256=rows[-1]["event_sha256"] if rows else "0" * 64,
                       **metadata)
            row["event_sha256"] = digest(row)
            with self.path.open("ab") as stream:
                stream.write((canonical(row) + "\n").encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
        return row


class Runner:
    def __init__(self, spec: ReaderSpec, store, loader=None):
        self.spec = spec
        self.store = Path(store).resolve()
        if spec.output_origin == "actual_model" and not self.store.is_relative_to((EC_ROOT / "local").resolve()):
            raise ValueError("Actual raw outputs must stay in the ignored evidence_contract/local area")
        self.store.mkdir(parents=True, exist_ok=True)
        self.events = EventLog(self.store)
        self.loader = loader
        self.predictor = None
        self.run_id = uuid.uuid4().hex

    def key(self, request):
        return digest(dict(schema="raw-reader-cache/1", reader=self.spec.fingerprint,
                           input_file_sha256=request.file_sha256, input_pixel_sha256=request.pixel_sha256))

    def _cached(self, path, key, request):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            payload = raw["payload"]
            if (raw["payload_sha256"] != digest(payload) or payload["schema"] != "raw-reader-cache/1"
                    or payload["reader_spec"] != self.spec.to_dict() or payload["cache_key"] != key
                    or payload["input_file_sha256"] != request.file_sha256
                    or payload["input_pixel_sha256"] != request.pixel_sha256):
                raise ValueError("Raw cache binding/integrity mismatch")
            native = NativeOutput.from_dict(payload["native"])
            call_id = payload["call_id"]
            begins = [e for e in self.events.read() if e["event"] == "inference_begin" and e.get("call_id") == call_id]
            if len(begins) != 1 or begins[0].get("cache_key") != key:
                raise ValueError("Raw output lacks its originating inference event")
            return native, call_id, raw["payload_sha256"]
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Corrupt cache; no automatic re-inference") from exc

    def infer(self, request: InputRequest, *, replay=False, retry_failed=False):
        rgb = request.load()
        key = self.key(request)
        path = self.store / "raw" / (key + ".json")
        base = dict(cache_key=key, reader_id=self.spec.reader_id, reader_fingerprint=self.spec.fingerprint,
                    output_origin=self.spec.output_origin, input_file_sha256=request.file_sha256,
                    input_pixel_sha256=request.pixel_sha256, run_id=self.run_id)
        with exclusive_lock(self.store / "locks" / (key + ".lock")):
            if path.exists():
                native, call_id, payload_sha = self._cached(path, key, request)
                if not replay:
                    rows = self.events.read()
                    if not any(e["event"] in ("inference_completed", "inference_recovered") and
                               e.get("call_id") == call_id for e in rows):
                        self.events.append("inference_recovered", **base, call_id=call_id, payload_sha256=payload_sha)
                    self.events.append("cache_hit", **base, call_id=call_id)
                return normalize(self.spec, native, input_file_sha256=request.file_sha256,
                                 input_pixel_sha256=request.pixel_sha256, cache_key=key, call_id=call_id,
                                 access_mode="replay" if replay else "cache_hit")
            if replay:
                raise FileNotFoundError("Replay requires an existing raw output; model loading is forbidden")
            history = [e for e in self.events.read() if e.get("cache_key") == key]
            starts = [e for e in history if e["event"] == "inference_begin"]
            if starts and not retry_failed:
                raise RuntimeError("Previous failed/ambiguous inference; explicit retry and audit required")
            if self.predictor is None:
                if self.loader is None:
                    raise RuntimeError("No reader loader supplied")
                start = time.perf_counter()
                self.events.append("model_load_begin", reader_id=self.spec.reader_id,
                                   reader_fingerprint=self.spec.fingerprint, run_id=self.run_id,
                                   output_origin=self.spec.output_origin)
                try:
                    self.predictor = self.loader(self.spec)
                except Exception as exc:
                    self.events.append("model_load_failed", reader_id=self.spec.reader_id,
                                       reader_fingerprint=self.spec.fingerprint, run_id=self.run_id,
                                       output_origin=self.spec.output_origin, error_type=type(exc).__name__,
                                       elapsed_seconds=time.perf_counter() - start)
                    raise
                self.events.append("model_load_completed", reader_id=self.spec.reader_id,
                                   reader_fingerprint=self.spec.fingerprint, run_id=self.run_id,
                                   output_origin=self.spec.output_origin, elapsed_seconds=time.perf_counter() - start)
            call_id = uuid.uuid4().hex
            start = time.perf_counter()
            self.events.append("inference_begin", **base, call_id=call_id)
            try:
                native = self.predictor(rgb)  # Sole boundary: pixels, no request/GT/expected key.
                if not isinstance(native, NativeOutput):
                    raise TypeError("Reader must return NativeOutput")
                native.validate()
                payload = dict(schema="raw-reader-cache/1", reader_spec=self.spec.to_dict(), cache_key=key,
                               input_file_sha256=request.file_sha256, input_pixel_sha256=request.pixel_sha256,
                               call_id=call_id, native=native.to_dict())
                payload_sha = digest(payload)
                write_once(path, dict(payload=payload, payload_sha256=payload_sha))
            except Exception as exc:
                self.events.append("inference_failed", **base, call_id=call_id,
                                   elapsed_seconds=time.perf_counter() - start, error_type=type(exc).__name__)
                raise
            self.events.append("inference_completed", **base, call_id=call_id, payload_sha256=payload_sha,
                               elapsed_seconds=time.perf_counter() - start)
            return normalize(self.spec, native, input_file_sha256=request.file_sha256,
                             input_pixel_sha256=request.pixel_sha256, cache_key=key, call_id=call_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader", required=True, choices=("rapid_v4", "rapid_latin_v5", "partial_42"))
    parser.add_argument("--inputs", type=Path, required=True, help="Pixels-only InputRequest manifest")
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True, help="New public counts/hash summary")
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    if not args.store.resolve().is_relative_to((EC_ROOT / "local").resolve()):
        raise ValueError("CLI inference store must be in evidence_contract/local")
    if not args.summary.resolve().is_relative_to((EC_ROOT / "execution/task4_runner").resolve()):
        raise ValueError("CLI public summaries must be in the new TASK4 execution area")
    manifest = json.loads(args.inputs.read_text(encoding="utf-8"))
    # Explicit key whitelist refuses a GT-bearing input manifest before inference.
    if set(manifest) != {"schema", "inputs"} or manifest["schema"] != "pixels-only-inputs/1":
        raise ValueError("Not a pixels-only input manifest")
    requests = [InputRequest(**row) for row in manifest["inputs"]]
    spec_path = args.store / (args.reader + ".spec.json")
    if args.replay:
        spec = ReaderSpec(**json.loads(spec_path.read_text(encoding="utf-8")))
        loader = None
    else:
        from .reader_adapters import specification, load_predictor
        spec = specification(args.reader)
        if spec_path.exists():
            if json.loads(spec_path.read_text(encoding="utf-8")) != spec.to_dict():
                raise ValueError("Frozen reader spec changed; use a separate store")
        else:
            write_once(spec_path, spec.to_dict())
        loader = load_predictor
    if spec.reader_id != args.reader:
        raise ValueError("Stored reader identity mismatch")
    runner = Runner(spec, args.store, loader)
    before = runner.events.read()
    outputs = [runner.infer(request, replay=args.replay) for request in requests]
    after = runner.events.read()
    new = after[len(before):]
    summary = dict(schema="runner-smoke/1", run_id=runner.run_id, reader=spec.to_dict(),
                   outputs=[o.public() for o in outputs],
                   new_inference_calls=sum(e["event"] == "inference_begin" for e in new),
                   model_loads=sum(e["event"] == "model_load_begin" for e in new),
                   event_count_before=len(before), event_count_after=len(after),
                   event_log_sha256=sha_file(runner.events.path) if runner.events.path.exists() else None,
                   replay=args.replay)
    write_once(args.summary, summary)
    print(canonical(dict(reader=args.reader, outputs=len(outputs), new_calls=summary["new_inference_calls"],
                         model_loads=summary["model_loads"], replay=args.replay)), flush=True)


if __name__ == "__main__":
    main()
