#!/usr/bin/env python3
"""Reconcile local Nsight GPU indices with DCGM UUIDs using an explicit inventory manifest."""
from __future__ import annotations
import copy
import re
from datetime import datetime

SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
PCI_BDF_RE = re.compile(r"^(?:[0-9a-fA-F]{4}|[0-9a-fA-F]{8}):[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]$")

def _is_utc_datetime(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.utcoffset() is not None
    except ValueError:
        return False

def _sha(value, label):
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(label + " must be a 64-character SHA-256 digest")
    return value.lower()

def _dcgm_artifact_hashes(report):
    values = set()
    for record in report.get("records", []):
        provenance = record.get("hardware_evidence", {}).get("provenance", {})
        digest = provenance.get("artifact_sha256")
        if digest:
            values.add(_sha(digest, "DCGM evidence artifact_sha256"))
    if len(values) != 1:
        raise ValueError("DCGM records must carry one consistent source artifact SHA-256")
    return values.pop()

def reconcile_gpu_identities(nsys_report, dcgm_report, manifest):
    """Return normalized copies plus an auditable, fail-closed identity report."""
    if not isinstance(nsys_report, dict) or not isinstance(dcgm_report, dict):
        raise ValueError("Nsight and DCGM importer reports must be objects")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "1.0":
        raise ValueError("GPU identity manifest schema_version must be 1.0")
    host_id = manifest.get("host_id")
    if not isinstance(host_id, str) or not host_id.strip() or len(host_id) > 128:
        raise ValueError("GPU identity manifest requires a non-empty host_id")
    source = manifest.get("identity_source")
    if not isinstance(source, dict):
        raise ValueError("identity_source must describe the inventory evidence")
    method = source.get("method")
    if not isinstance(method, str) or not method.strip():
        raise ValueError("identity_source.method is required")
    inventory_sha = _sha(source.get("artifact_sha256"), "identity_source.artifact_sha256")
    if not _is_utc_datetime(source.get("collected_at")):
        raise ValueError("identity_source.collected_at must be timezone-aware ISO date-time")
    expected_nsys = _sha(manifest.get("nsys_artifact_sha256"), "nsys_artifact_sha256")
    expected_dcgm = _sha(manifest.get("dcgm_artifact_sha256"), "dcgm_artifact_sha256")
    actual_nsys = _sha(nsys_report.get("artifact_sha256"), "Nsight report artifact_sha256")
    actual_dcgm = _dcgm_artifact_hashes(dcgm_report)
    if expected_nsys != actual_nsys:
        raise ValueError("GPU identity manifest Nsight artifact hash does not match the imported profiler file")
    if expected_dcgm != actual_dcgm:
        raise ValueError("GPU identity manifest DCGM artifact hash does not match the imported telemetry file")

    rows = manifest.get("devices")
    if not isinstance(rows, list) or not rows:
        raise ValueError("GPU identity manifest requires a non-empty devices array")
    by_nsys, by_dcgm, pci_seen, cuda_seen = {}, {}, set(), set()
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"devices[{index}] must be an object")
        nsys_id, cuda_id = row.get("nsys_device_id"), row.get("cuda_device_id")
        dcgm_id, pci = row.get("dcgm_entity_id"), row.get("pci_bus_id")
        if type(nsys_id) is not int or nsys_id < 0:
            raise ValueError(f"devices[{index}].nsys_device_id must be a non-negative integer")
        if type(cuda_id) is not int or cuda_id < 0:
            raise ValueError(f"devices[{index}].cuda_device_id must be a non-negative integer")
        if not isinstance(dcgm_id, str) or not dcgm_id.startswith("GPU-") or len(dcgm_id) < 8:
            raise ValueError(f"devices[{index}].dcgm_entity_id must be a GPU UUID")
        if not isinstance(pci, str) or not PCI_BDF_RE.fullmatch(pci):
            raise ValueError(f"devices[{index}].pci_bus_id must be a PCI domain:bus:device.function address")
        if nsys_id in by_nsys:
            raise ValueError(f"duplicate Nsight device index {nsys_id}")
        if cuda_id in cuda_seen:
            raise ValueError(f"duplicate CUDA device index {cuda_id}")
        if dcgm_id in by_dcgm:
            raise ValueError(f"duplicate DCGM GPU UUID {dcgm_id}")
        if pci.lower() in pci_seen:
            raise ValueError(f"duplicate PCI Bus ID {pci}")
        item = {"canonical_device_id": dcgm_id, "nsys_device_id": nsys_id,
                "cuda_device_id": cuda_id, "dcgm_entity_id": dcgm_id, "pci_bus_id": pci.lower()}
        by_nsys[nsys_id], by_dcgm[dcgm_id] = item, item
        cuda_seen.add(cuda_id)
        pci_seen.add(pci.lower())
        normalized.append(item)

    observed_nsys = {item.get("device_id") for item in nsys_report.get("events", [])
                     if type(item.get("device_id")) is int}
    observed_dcgm = {item.get("device_identity") for item in dcgm_report.get("records", [])
                     if isinstance(item.get("device_identity"), str)}
    if observed_nsys != set(by_nsys):
        raise ValueError("GPU identity manifest must cover exactly the Nsight device indices; "
                         f"observed={sorted(observed_nsys)}, mapped={sorted(by_nsys)}")
    if observed_dcgm != set(by_dcgm):
        raise ValueError("GPU identity manifest must cover exactly the DCGM device UUIDs; "
                         f"observed={sorted(observed_dcgm)}, mapped={sorted(by_dcgm)}")

    nsys_records = copy.deepcopy(nsys_report.get("records", []))
    for record in nsys_records:
        mapped_ids = set()
        for event in record.get("runtime_trace", {}).get("events", []):
            entity = event.get("entity_id")
            match = re.fullmatch(r"gpu([0-9]+)", entity) if isinstance(entity, str) else None
            if match:
                device = by_nsys.get(int(match.group(1)))
                if device is None:
                    raise ValueError("runtime trace contains an unmapped Nsight GPU entity")
                event["entity_id"] = device["canonical_device_id"]
                mapped_ids.add(device["canonical_device_id"])
        record["canonical_device_ids"] = sorted(mapped_ids)

    dcgm_records = copy.deepcopy(dcgm_report.get("records", []))
    for record in dcgm_records:
        source_id = record["device_identity"]
        device = by_dcgm[source_id]
        record["canonical_device_id"] = device["canonical_device_id"]
        for metric in record["hardware_evidence"].get("metrics", []):
            if metric.get("entity_id") != source_id:
                raise ValueError("DCGM metric entity_id does not match its enclosing device identity")
            metric["entity_id"] = device["canonical_device_id"]

    report = {
        "schema_version": "1.0", "generated_by": "scripts/reconcile_gpu_identities.py",
        "status": "operator_attested_exact_artifact_match", "host_id": host_id,
        "identity_source": {"method": method, "artifact_sha256": inventory_sha,
                            "collected_at": source["collected_at"]},
        "nsys_artifact_sha256": actual_nsys, "dcgm_artifact_sha256": actual_dcgm,
        "mapped_device_count": len(normalized),
        "mappings": sorted(normalized, key=lambda item: item["nsys_device_id"]),
        "identity_semantics": "DCGM GPU UUID is the canonical entity ID; Nsight gpuN is replaced only by the explicit manifest mapping.",
        "limitations": [
            "The mapping is an operator attestation; this tool verifies its structure and exact profiler/telemetry artifact hashes, not the physical truth of the inventory observation.",
            "The inventory evidence artifact is identified by its supplied SHA-256; its contents are not independently collected or re-read by this offline tool.",
            "CUDA device indices are process-local and may change when CUDA_VISIBLE_DEVICES or container remapping changes.",
            "A PCI Bus ID is host-local and must not be treated as a globally unique device identity.",
            "GPU identity reconciliation does not correlate an OTel request or runtime phase with a CUDA kernel.",
            "No clock synchronization, temporal correction, causal dependency or bottleneck attribution is inferred.",
        ],
    }
    return nsys_records, dcgm_records, report
