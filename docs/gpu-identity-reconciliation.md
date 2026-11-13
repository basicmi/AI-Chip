# GPU identity reconciliation

The end-to-end capture harness can optionally reconcile local Nsight GPU
indices with NVIDIA DCGM GPU UUIDs. This is required before a per-GPU profiler
event and a per-GPU telemetry metric can be treated as referring to the same
physical device.

## Why an explicit manifest is required

Nsight Systems exports CUDA device IDs as session-local gpuN values. DCGM
usually exposes a stable GPU UUID. CUDA ordinals can be changed by
CUDA_VISIBLE_DEVICES, container remapping or process launch order. PCI Bus IDs
are useful host-local cross-checks, but are not globally unique. The harness
therefore does not infer an identity from matching index numbers, model names,
event timestamps or device ordering.

## Manifest

Create a JSON file with one row per GPU present in both the Nsight and DCGM
artifacts:

    {
      "schema_version": "1.0",
      "host_id": "node-0",
      "identity_source": {
        "method": "nvidia-smi query: index,uuid,pci.bus_id",
        "artifact_sha256": "64-character SHA-256 of the captured inventory output",
        "collected_at": "2026-11-13T10:00:00Z"
      },
      "nsys_artifact_sha256": "64-character SHA-256 of the exact Nsight SQLite export",
      "dcgm_artifact_sha256": "64-character SHA-256 of the exact DCGM capture JSON",
      "devices": [
        {
          "nsys_device_id": 0,
          "cuda_device_id": 0,
          "dcgm_entity_id": "GPU-...",
          "pci_bus_id": "00000000:41:00.0"
        }
      ]
    }

The artifact hashes for Nsight and DCGM must match the imported files exactly.
The identity inventory is operator-attested and its hash is retained; this
offline workflow does not execute nvidia-smi or independently verify the
inventory's physical truth. The manifest must cover exactly the device indices
and DCGM UUIDs present in the two captures. Duplicate CUDA ordinals, PCI Bus
IDs, Nsight indices or DCGM UUIDs are rejected.

## Run

Add --gpu-identity-map /path/to/gpu-identity-map.json to the normal
scripts/run_capture_harness.py invocation. Both --nsys-sqlite and
--dcgm-capture are required when this option is used.

The harness retains the original Nsight and DCGM artifacts unchanged. It emits
gpu-identity-reconciliation.json and applies the explicit canonical UUID to
the in-memory copies used for Nsight/DCGM alignment. The Nsight alignment only
pairs a profiler trace with a DCGM device when the trace contains an event for
that mapped GPU. The original local gpuN values remain visible in the raw
nsight-profiler.json.

## Interpretation limits

- The mapping is an operator assertion bound to exact profiler and DCGM input
  hashes, not independent hardware attestation by this script.
- CUDA ordinals are process-local; PCI Bus IDs are host-local.
- This establishes device identity only. It does not assign an OTel request or
  runtime phase to a CUDA kernel.
- It does not calibrate host clocks, translate timestamps or infer causal
  dependencies. Cross-host clock calibration and request-to-kernel correlation
  remain separate evidence requirements.
