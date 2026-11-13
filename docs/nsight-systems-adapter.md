# Nsight Systems SQLite Adapter (PR #83)

This adapter imports CUDA kernel and CUDA runtime API events from a **local Nsight
Systems SQLite export**; it is not a profiler and never runs GPU code on behalf
of a user. NVIDIA documents CUPTI_ACTIVITY_KIND_KERNEL, CUPTI_ACTIVITY_KIND_RUNTIME,
StringIds and the different correlation identifiers:
https://docs.nvidia.com/nsight-systems/AnalysisGuide/

## Capture and export

On an NVIDIA GPU host with Nsight Systems installed, profile an **actual**
workload. For example (replace this with your inference command):

    nsys profile --trace=cuda,nvtx -o ./nsys-capture python3 your_inference.py
    nsys export --type sqlite --output ./nsys-capture.sqlite ./nsys-capture.nsys-rep

Read-only import:

    python3 scripts/import_nsys_sqlite.py \
      --input ./nsys-capture.sqlite \
      --output ./nsys-events.json \
      --source-url https://YOUR-PROFILER-ARTIFACT.example/capture

Replace the URL above with the real, user-managed artifact/source URL. The SQLite
file itself remains unchanged. The resulting JSON includes raw event intervals
(in source session nanoseconds), GPU device index, CUDA context/stream, names,
and CPU API launch-correlation candidate IDs. The source SQLite SHA-256 is kept.

**No clock anchors = no runtime_trace records.** The SQLite timestamps are
not assumed to be UTC. This prevents silently overlaying a GPU session time
axis with separately collected OpenTelemetry request wall time.

## Optional, independently verified clock mapping

If you have explicit anchors measured for this *same profiler session*, save
a JSON file with a piecewise-linear monotonic-to-UTC mapping:

    {
      "method": "piecewise_linear",
      "anchors": [
        {"monotonic_ns": 1000000, "utc_at": "2026-11-13T00:00:00Z"},
        {"monotonic_ns": 5000000, "utc_at": "2026-11-13T00:00:00.004Z"}
      ],
      "max_error_ns": 1000
    }

Run with --clock-anchors anchors.json. **These numbers are format examples
only, not valid calibration data.** Anchors must bracket every imported event,
be increasing and carry a measured error bound. The adapter validates the
resulting trace with the existing AI-Chip trace validator.

Calibrated output has records[].runtime_trace with clock_domain=monotonic_ns,
and can be supplied to the existing runtime trace alignment/decomposition tools.
These events contain no request or token markers: they are not automatically
merged with OTLP traces. A future step needs independently validated correlation,
process/GPU identity and clock-domain mapping before claiming request-to-kernel
alignment or bottleneck causality.

## Semantics and limits

- CUDA API to kernel candidate links use **same-process** CUPTI correlationId.
  A numeric correlationId alone is not globally unique. Candidate is not a
  completion dependency, synchronization edge or request/phase membership.
- Kernel names are looked up through StringIds. Communication category applies
  only to a name-based NCCL heuristic; no assumption that every communication
  operation is identified or that every NCCL kernel measures network transfer.
- Per-GPU entity IDs use local Nsight device indices, not UUIDs. Do not join
  these to independent GPU telemetry unless a verified identity mapping exists.
- No NVTX-to-GPU causal mapping, automatic device-to-host time conversion,
  artificially precise attribution or published benchmark numbers are created.
- Requires kernel table. Runtime API table is optional. Unknown/invalid
  intervals are rejected with explicit counts; schema drift in required
  columns is an error. Each import is limited to 100k input events by default.

Test:

    python3 -m unittest discover -s tests -p 'test_nsys_sqlite_import.py' -v
