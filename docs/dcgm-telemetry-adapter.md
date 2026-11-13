# DCGM Exporter Telemetry Adapter (PR #84)

This adapter captures actual DCGM Exporter Prometheus text from a locally
accessible /metrics endpoint and transforms supported, measured gauge samples
to AI-Chip hardware_evidence. It does NOT fabricate HBM bandwidth from DRAM
activity ratio or derive performance bottlenecks from GPU utilization.

DCGM field semantics: https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html
DCGM Exporter: https://github.com/NVIDIA/dcgm-exporter

## Two-step capture and import

Run against an accessible **DCGM Exporter /metrics** endpoint; the endpoint
is generally port 9400 when default-configured, but depends on deployment.

    python3 scripts/import_dcgm_telemetry.py \
      --endpoint http://127.0.0.1:9400/metrics \
      --count 10 --interval-seconds 1 \
      --capture-output /tmp/dcgm-capture.json

Then normalize against the existing versioned DCGM mapping catalog:

    python3 scripts/import_dcgm_telemetry.py \
      --input /tmp/dcgm-capture.json \
      --output /tmp/dcgm-evidence.json \
      --source-url https://YOUR-ARTIFACT-SERVER.example/capture \
      --device-model 'RTX 3090'

Use a **real** source URL, not the placeholder. No GPU is needed to run the
fixture tests. The adapter accepts Prometheus text as returned by DCGM
Exporter, retaining raw snapshot text and response-receipt UTC timestamps
in the capture file. Raw captures may contain sensitive node information.

## Supported normalized values

- DCGM_FI_PROF_SM_UTIL_RATIO -> sm_active_pct (ratio to %)
- DCGM_FI_PROF_TENSOR_UTIL_RATIO -> tensor_active_pct
- DCGM_FI_PROF_DRAM_UTIL_RATIO -> dram_active_pct (NOT bandwidth)
- DCGM_FI_DEV_BOARD_POWER_WATTS -> gpu_power_w
- DCGM_FI_DEV_FB_USED -> hbm_used_bytes (MiB to bytes; generic GPU framebuffer
  memory usage, NOT proof the GPU memory implementation is HBM)
- DCGM_FI_DEV_SM_CLOCK / DCGM_FI_DEV_MEM_CLOCK -> clocks in Hz
- DCGM_FI_DEV_GPU_TEMP_CELSIUS -> temperature

The canonical registry retains its existing key hbm_used_bytes for measured
device framebuffer memory, even on GDDR GPUs; this is an imperfect vocabulary
choice, so the source mapping and metric note explicitly explain it.

Device UUID is preferred for identity; local gpu index is accepted but labeled
local-gpu:N and is NOT a stable cross-host device identity. Only fields that
are explicitly present and fully sampled at every capture time are mapped.
Unsupported fields, missing samples, sentinel (-1 / NaN), and cumulative
byte totals without independently measured deltas cannot silently create
metric evidence. Counter values are never inferred from rates.

Arithmetic mean of discrete scrape observations is reported for each
device/metric, with sample count and receipt-time interval. These are NOT
time-weighted averages or phase-contained sampling windows. Individual
sampling_window is omitted to prevent unsupported phase attribution by the
existing trace alignment tool. GPU- or host-time alignment and verified
bottleneck evidence remain future work.

**Caveat:** DCGM exporter values depend on GPU and DCGM version, export
configuration, and field availability. A consumer RTX 3090 may not expose
all PROF_* metrics; missing support is recorded as missing, never zero.
