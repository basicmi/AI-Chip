# End-to-End Multi-Layer Capture Harness (PR #85)

The harness combines the existing OTLP JSON, Nsight Systems SQLite and NVIDIA
DCGM capture importers into one reproducible offline analysis bundle. It does
not launch vLLM, start an OTLP receiver, start DCGM Exporter, invoke Nsight
Systems, or collect the artifacts concurrently. Capture the artifacts first,
then process them together under one user-assigned run ID.

## Inputs

- OTLP JSON export OR a directory of saved OTLP JSON batches
- Nsight Systems SQLite export (created with nsys export --type sqlite)
- DCGM Exporter capture JSON created by import_dcgm_telemetry.py

At least one layer is required. Supplying all three creates a full three-layer
bundle. The same --run-id is an operator assertion that these artifacts belong
to one experiment; it is not proof of host or process identity.

## Example

    python3 scripts/run_capture_harness.py \
      --run-id vllm-qwen-3090-20261113 \
      --otel-json /data/run/otlp-export.json \
      --otel-source-url https://trace.example/trace/ACTUAL_TRACE_ID \
      --service-name vllm \
      --nsys-sqlite /data/run/nsys.sqlite \
      --nsys-source-url https://artifacts.example/ACTUAL_SESSION.sqlite \
      --clock-anchors /data/run/verified-clock-anchors.json \
      --dcgm-capture /data/run/dcgm-capture.json \
      --dcgm-source-url https://artifacts.example/ACTUAL_DCGM_CAPTURE.json \
      --device-model 'RTX 3090' \
      --output-dir /data/run/ai-chip-analysis

Replace each URL with a real artifact or trace URL. Do not publish trace payloads
or raw profiler captures in the website repository: they may contain prompts,
identifiers, hostnames or other sensitive data. Output directories and JSON
artifacts are created with private POSIX permissions (0700/0600).

For a saved OTLP receiver directory, use --otel-capture-dir instead of
--otel-json; provide the actual trace-system URL via --otel-source-url.
For Nsight exports without verified clock anchors, omit --clock-anchors:
profiler events remain in their original session clock and are deliberately
excluded from UTC alignment. Clock anchors must be measured independently and
cover the complete exported event window.

## Outputs

- runtime-traces.json: normalized OTLP request records and source diagnostics
- runtime-phases.json: request phase coverage and token-derived TTFT/TPOT
- nsight-profiler.json: CUDA API/kernel events, candidate launch correlations,
  source hash and clock status
- dcgm-hardware-evidence.json: validated per-GPU telemetry evidence
- runtime-dcgm-alignment.json: coarse capture-window comparisons for each
  OTLP request record × DCGM device record
- nsight-dcgm-alignment.json: coarse capture-window comparisons when Nsight
  has verified UTC clock anchors
- capture-report.json: run ID, input provenance, layer coverage, output hashes,
  counts, warnings and limitations

Only files for supplied layers are emitted. Use --overwrite to intentionally
replace files with the same names in an existing output directory.

## Interpretation boundaries

- A shared run ID means the operator grouped the inputs; it does not prove
  collector host, process, GPU or request identity.
- OTLP/DCGM overlap is only a coarse wall-clock observation. DCGM metrics have
  no metric-specific sample window, so they are not joined to individual phases.
- Nsight SQLite timestamps are session-relative nanoseconds. UTC comparison is
  enabled only with independently measured, validated clock anchors.
- Nsight CUPTI correlation IDs are candidate API-to-kernel launch associations,
  not GPU completion dependencies. Kernel-to-request assignment is not inferred.
- GPU UUIDs are not inferred from Nsight local gpuN indexes.
- DRAM activity is not HBM bandwidth; no bandwidth or bottleneck is fabricated.
- Trace-derived TTFT/TPOT require explicit token marker events; aggregate latency
  attributes or completion-token counts do not create token timestamps.
- The report does not make causal claims, rank bottlenecks, or replace published
  benchmark measurements.

The current workflow is offline artifact integration. Simultaneous workload
orchestration, host clock synchronization, GPU UUID reconciliation and
request-to-kernel correlation are separate future engineering steps.
