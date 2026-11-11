"""Observed process resources, plus optional device-wide nvidia-smi samples."""
from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time

import psutil


class ResourceMonitor:
    def __init__(self, gpu=False):
        self.process = psutil.Process()
        self.gpu = gpu
        self.stop_event = threading.Event()
        self.samples = []
        self.gpu_samples = []
        self.gpu_error = None
        self.start_wall = time.perf_counter()
        initial = self.process.cpu_times()
        self.start_cpu = initial.user + initial.system
        self.thread = threading.Thread(target=self._sample, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def _sample(self):
        last_gpu = -100.
        binary = shutil.which("nvidia-smi") if self.gpu else None
        if self.gpu and not binary:
            self.gpu_error = "nvidia-smi_not_available"
        while not self.stop_event.is_set():
            self.samples.append(dict(seconds=time.perf_counter() - self.start_wall,
                                     rss_bytes=self.process.memory_info().rss, threads=self.process.num_threads()))
            if binary and time.perf_counter() - last_gpu >= 2.:
                try:
                    result = subprocess.run([binary, "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits", "-i", "0"],
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, check=True, timeout=4,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0)
                    util, memory = [float(s.strip()) for s in result.stdout.strip().splitlines()[0].split(',')]
                    self.gpu_samples.append(dict(seconds=time.perf_counter() - self.start_wall,
                                                 device_utilization_percent=util, device_used_mib=memory))
                except Exception as exc:
                    self.gpu_error = type(exc).__name__
                last_gpu = time.perf_counter()
            self.stop_event.wait(.25)

    def finish(self, outputs=()):
        self.stop_event.set()
        self.thread.join(timeout=5.)
        cpu = self.process.cpu_times()
        cpu_seconds = cpu.user + cpu.system - self.start_cpu
        elapsed = time.perf_counter() - self.start_wall
        allocated = [o.runtime_metadata['peak_allocated_bytes'] for o in outputs if 'peak_allocated_bytes' in o.runtime_metadata]
        reserved = [o.runtime_metadata['peak_reserved_bytes'] for o in outputs if 'peak_reserved_bytes' in o.runtime_metadata]
        return dict(wall_seconds=elapsed, process_cpu_seconds=cpu_seconds,
                    average_cpu_percent_of_one_core=100 * cpu_seconds / elapsed if elapsed else None,
                    process_sample_count=len(self.samples), process_peak_sampled_rss_bytes=max(
                        (s['rss_bytes'] for s in self.samples), default=None),
                    process_peak_sampled_thread_count=max((s['threads'] for s in self.samples), default=None),
                    gpu_device_sample_count=len(self.gpu_samples), gpu_query_error=self.gpu_error,
                    gpu_device_peak_utilization_percent=max((s['device_utilization_percent'] for s in self.gpu_samples), default=None),
                    gpu_device_peak_used_mib=max((s['device_used_mib'] for s in self.gpu_samples), default=None),
                    native_peak_allocated_bytes=max(allocated, default=None), native_peak_reserved_bytes=max(reserved, default=None),
                    gpu_scope='device-wide utilization includes other applications; native CUDA memory is reader-reported',
                    samples=self.samples, gpu_samples=self.gpu_samples)
