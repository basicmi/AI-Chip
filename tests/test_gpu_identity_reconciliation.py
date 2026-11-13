import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reconcile_gpu_identities import reconcile_gpu_identities
NSYS_SHA, DCGM_SHA, INVENTORY_SHA = "a" * 64, "b" * 64, "c" * 64

def fixtures():
    nsys = {"artifact_sha256": NSYS_SHA,
        "events": [{"device_id": 0, "event": {"event_id": "kernel-0", "entity_id": "gpu0"}},
                   {"device_id": 0, "event": {"event_id": "kernel-1", "entity_id": "gpu0"}}],
        "records": [{"id": "nsys-1", "runtime_trace": {"events": [
            {"event_id": "kernel-0", "entity_id": "gpu0"},
            {"event_id": "kernel-1", "entity_id": "gpu0"}]}}]}
    dcgm = {"records": [{"id": "dcgm-1", "device_identity": "GPU-abcdef12",
        "hardware_evidence": {"provenance": {"artifact_sha256": DCGM_SHA},
        "metrics": [{"metric_id": "gpu_power_w", "entity_id": "GPU-abcdef12"}]}}]}
    manifest = {"schema_version": "1.0", "host_id": "node-0",
        "identity_source": {"method": "nvidia-smi query: index,uuid,pci.bus_id",
            "artifact_sha256": INVENTORY_SHA, "collected_at": "2026-11-13T10:00:00Z"},
        "nsys_artifact_sha256": NSYS_SHA, "dcgm_artifact_sha256": DCGM_SHA,
        "devices": [{"nsys_device_id": 0, "cuda_device_id": 0,
            "dcgm_entity_id": "GPU-abcdef12", "pci_bus_id": "00000000:41:00.0"}]}
    return nsys, dcgm, manifest

class GPUIdentityReconciliationTests(unittest.TestCase):
    def test_maps_local_nsys_index_to_dcgm_uuid_without_mutating_sources(self):
        nsys, dcgm, manifest = fixtures()
        old_nsys, old_dcgm = copy.deepcopy(nsys), copy.deepcopy(dcgm)
        nsys_records, dcgm_records, report = reconcile_gpu_identities(nsys, dcgm, manifest)
        self.assertEqual(report["status"], "operator_attested_exact_artifact_match")
        self.assertEqual(report["mapped_device_count"], 1)
        self.assertEqual(nsys_records[0]["runtime_trace"]["events"][0]["entity_id"], "GPU-abcdef12")
        self.assertEqual(nsys_records[0]["canonical_device_ids"], ["GPU-abcdef12"])
        self.assertEqual(dcgm_records[0]["canonical_device_id"], "GPU-abcdef12")
        self.assertEqual(dcgm_records[0]["hardware_evidence"]["metrics"][0]["entity_id"], "GPU-abcdef12")
        self.assertEqual(nsys, old_nsys)
        self.assertEqual(dcgm, old_dcgm)

    def test_rejects_profiler_artifact_hash_mismatch(self):
        nsys, dcgm, manifest = fixtures()
        manifest["nsys_artifact_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "Nsight artifact hash"):
            reconcile_gpu_identities(nsys, dcgm, manifest)

    def test_rejects_dcgm_artifact_hash_mismatch(self):
        nsys, dcgm, manifest = fixtures()
        manifest["dcgm_artifact_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "DCGM artifact hash"):
            reconcile_gpu_identities(nsys, dcgm, manifest)

    def test_rejects_duplicate_pci_bus_id_and_duplicate_indices(self):
        nsys, dcgm, manifest = fixtures()
        second = dict(manifest["devices"][0])
        second.update({"nsys_device_id": 1, "cuda_device_id": 1, "dcgm_entity_id": "GPU-12345678"})
        manifest["devices"].append(second)
        with self.assertRaisesRegex(ValueError, "duplicate PCI Bus ID"):
            reconcile_gpu_identities(nsys, dcgm, manifest)

    def test_rejects_incomplete_device_mapping(self):
        nsys, dcgm, manifest = fixtures()
        manifest["devices"][0]["nsys_device_id"] = 1
        with self.assertRaisesRegex(ValueError, "cover exactly the Nsight"):
            reconcile_gpu_identities(nsys, dcgm, manifest)

    def test_rejects_invalid_pci_address_and_naive_inventory_time(self):
        nsys, dcgm, manifest = fixtures()
        manifest["devices"][0]["pci_bus_id"] = "GPU0"
        with self.assertRaisesRegex(ValueError, "PCI domain"):
            reconcile_gpu_identities(nsys, dcgm, manifest)
        nsys, dcgm, manifest = fixtures()
        manifest["identity_source"]["collected_at"] = "2026-11-13T10:00:00"
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            reconcile_gpu_identities(nsys, dcgm, manifest)

    def test_rejects_metric_identity_conflict(self):
        nsys, dcgm, manifest = fixtures()
        dcgm["records"][0]["hardware_evidence"]["metrics"][0]["entity_id"] = "GPU-other"
        with self.assertRaisesRegex(ValueError, "does not match"):
            reconcile_gpu_identities(nsys, dcgm, manifest)

if __name__ == "__main__":
    unittest.main()
