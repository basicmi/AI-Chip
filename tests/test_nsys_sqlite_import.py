import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_nsys_sqlite import import_nsys
from validate_benchmark_results import validate_runtime_trace

SOURCE = "https://example.org/reports/nsys-session.sqlite"


def fixture(path, *, include_kernel=True, include_runtime=True):
    db = sqlite3.connect(path)
    try:
        db.execute("CREATE TABLE StringIds (id INTEGER, value TEXT)")
        db.executemany("INSERT INTO StringIds VALUES (?, ?)", [
            (1, "flash_attention_kernel"), (2, "ncclKernel_AllReduce"),
            (3, "cudaLaunchKernel"), (4, "cudaMemcpyAsync"),
        ])
        if include_kernel:
            db.execute("CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL "
                       "(start INTEGER, end INTEGER, deviceId INTEGER, contextId INTEGER, "
                       "streamId INTEGER, correlationId INTEGER, globalPid INTEGER, shortName INTEGER)")
            db.executemany("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
                (100_000_000, 200_000_000, 0, 3, 7, 11, 123 << 24, 1),
                (220_000_000, 270_000_000, 1, 4, 8, 12, 123 << 24, 2),
            ])
        if include_runtime:
            db.execute("CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME "
                       "(start INTEGER, end INTEGER, correlationId INTEGER, globalTid INTEGER, nameId INTEGER)")
            db.executemany("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?, ?, ?, ?, ?)", [
                (10_000_000, 50_000_000, 11, (123 << 24) + 20, 3),
                (55_000_000, 90_000_000, 12, (123 << 24) + 20, 4),
                (5_000_000, 9_000_000, 11, (345 << 24) + 20, 3),
            ])
        db.commit()
    finally:
        db.close()


class NsightImportTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.path = Path(self.work.name) / "test.sqlite"
        fixture(self.path)

    def test_kernel_name_stream_context_gpu_and_nccl_classification(self):
        report = import_nsys(self.path, source_url=SOURCE)
        self.assertEqual(report["clock_alignment_status"], "unavailable_no_verified_anchors")
        self.assertEqual(report["records"], [])
        self.assertEqual(report["diagnostics"]["kernel_events"], 2)
        self.assertEqual(report["diagnostics"]["cuda_api_events"], 3)
        kernels = [item for item in report["events"] if item["source_table"] == "CUPTI_ACTIVITY_KIND_KERNEL"]
        self.assertEqual(kernels[0]["event"]["name"], "flash_attention_kernel")
        self.assertEqual(kernels[0]["event"]["stream_id"], "cuda:gpu0:ctx3:stream7")
        self.assertEqual(kernels[0]["event"]["entity_id"], "gpu0")
        self.assertEqual(kernels[1]["event"]["category"], "communication")
        self.assertEqual(kernels[1]["communication_label_basis"], "kernel_name_nccl_heuristic")

    def test_scoped_cupti_launch_correlations_do_not_become_dependencies(self):
        report = import_nsys(self.path, source_url=SOURCE)
        runtimes = [item for item in report["events"] if item["source_table"] == "CUPTI_ACTIVITY_KIND_RUNTIME"]
        self.assertEqual(runtimes[0]["candidate_kernel_event_ids"], [])
        self.assertEqual(runtimes[1]["candidate_kernel_event_ids"], ["nsys-kernel-0"])
        self.assertEqual(runtimes[2]["candidate_kernel_event_ids"], ["nsys-kernel-1"])
        self.assertTrue(all("depends_on_event_ids" not in item["event"] for item in report["events"]))

    def test_explicit_utc_clock_anchors_yield_valid_existing_runtime_trace(self):
        anchors = {"method": "piecewise_linear", "anchors": [
            {"monotonic_ns": 0, "utc_at": "2026-11-13T00:00:00Z"},
            {"monotonic_ns": 500_000_000, "utc_at": "2026-11-13T00:00:00.500Z"},
        ], "max_error_ns": 0}
        report = import_nsys(self.path, source_url=SOURCE, anchors=anchors)
        self.assertEqual(report["clock_alignment_status"], "verified_anchors_supplied_by_caller")
        trace = report["records"][0]["runtime_trace"]
        self.assertEqual(validate_runtime_trace(trace, "test"), [])
        self.assertTrue(all("correlation_id" not in event for event in trace["events"]))
        self.assertEqual(trace["sampling"]["started_at"], 5_000_000)
        self.assertEqual(trace["sampling"]["ended_at"], 270_000_000)

    def test_anchor_window_must_cover_trace_no_extrapolation(self):
        anchors = {"method": "piecewise_linear", "anchors": [
            {"monotonic_ns": 10_000_000, "utc_at": "2026-11-13T00:00:00Z"},
            {"monotonic_ns": 250_000_000, "utc_at": "2026-11-13T00:00:00.240Z"},
        ], "max_error_ns": 0}
        with self.assertRaisesRegex(ValueError, "contain every exported event"):
            import_nsys(self.path, source_url=SOURCE, anchors=anchors)

    def test_missing_kernel_table_fail_closed(self):
        other = Path(self.work.name) / "without_kernel.sqlite"
        fixture(other, include_kernel=False)
        with self.assertRaisesRegex(ValueError, "no CUPTI_ACTIVITY_KIND_KERNEL"):
            import_nsys(other, source_url=SOURCE)

    def test_missing_optional_runtime_table_is_supported(self):
        other = Path(self.work.name) / "kernel_only.sqlite"
        fixture(other, include_runtime=False)
        report = import_nsys(other, source_url=SOURCE)
        self.assertEqual(report["diagnostics"]["cuda_api_events"], 0)

    def test_invalid_timestamps_are_skipped_and_reported(self):
        db = sqlite3.connect(self.path)
        db.execute("INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,?,?,?,?,?,?)", (0, 0, 0, 1, 2, 3, 123 << 24, 1))
        db.commit()
        db.close()
        report = import_nsys(self.path, source_url=SOURCE)
        self.assertEqual(report["diagnostics"]["skipped"]["kernel_invalid_timing"], 1)
        self.assertEqual(report["diagnostics"]["kernel_events"], 2)

    def test_no_invented_utc_mapping_from_timestamp_values(self):
        report = import_nsys(self.path, source_url=SOURCE)
        self.assertNotIn("runtime_trace", report)
        self.assertEqual(report["time_window_ns"], {"started_at": 5_000_000, "ended_at": 270_000_000})


if __name__ == "__main__":
    unittest.main()
