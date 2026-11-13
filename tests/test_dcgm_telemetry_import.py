import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from import_dcgm_telemetry import import_dcgm, parse_prometheus
from hardware_counter_mapping import normalize_counter
from validate_benchmark_results import validate_hardware_evidence

STAMP1 = "2026-11-13T00:00:00Z"
STAMP2 = "2026-11-13T00:00:01Z"


def row(name, value, uuid="GPU-abc"):
    return name + '{gpu="0",UUID="' + uuid + '"} ' + str(value)


def dataset(a, b):
    return {"source_format": "dcgm_exporter_prometheus_text",
            "snapshots":[{"captured_at": STAMP1, "body": a},
                         {"captured_at": STAMP2, "body": b}]}


class DCGMTelemetryTests(unittest.TestCase):
    def test_activity_power_memory_and_clock_are_validated(self):
        a = "\n".join([row("DCGM_FI_PROF_SM_UTIL_RATIO",0.2),
                       row("DCGM_FI_PROF_DRAM_UTIL_RATIO",0.4),
                       row("DCGM_FI_DEV_BOARD_POWER_WATTS",220),
                       row("DCGM_FI_DEV_FB_USED",1024)])
        b = "\n".join([row("DCGM_FI_PROF_SM_UTIL_RATIO",0.6),
                       row("DCGM_FI_PROF_DRAM_UTIL_RATIO",0.8),
                       row("DCGM_FI_DEV_BOARD_POWER_WATTS",260),
                       row("DCGM_FI_DEV_FB_USED",2048)])
        output=import_dcgm(dataset(a,b),source_url="https://example.org/test-capture")
        self.assertEqual(len(output["records"]),1)
        evidence=output["records"][0]["hardware_evidence"]
        self.assertEqual(validate_hardware_evidence({"hardware_evidence":evidence},"test"),[])
        values={v["metric_id"]:v["value"] for v in evidence["metrics"]}
        self.assertAlmostEqual(values["sm_active_pct"],40)
        self.assertAlmostEqual(values["dram_active_pct"],60)
        self.assertEqual(values["gpu_power_w"],240)
        self.assertEqual(values["hbm_used_bytes"],1536*1048576)
        self.assertTrue(all("sampling_window" not in m for m in evidence["metrics"]))
        self.assertNotIn("dram_bandwidth_bytes_per_s",values)
        self.assertEqual(evidence["metrics"][0]["entity_id"],"GPU-abc")

    def test_parser_handles_comments_and_escaped_labels(self):
        rows=parse_prometheus('# HELP foo hi\n'+row("DCGM_FI_DEV_BOARD_POWER_WATTS",230)+'\n')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["labels"]["UUID"],"GPU-abc")
        with self.assertRaisesRegex(ValueError,"invalid Prometheus numeric value"):
            parse_prometheus("invalid bogus")

    def test_missing_sample_excludes_series_not_interpolated(self):
        output=import_dcgm(dataset(
            row("DCGM_FI_DEV_BOARD_POWER_WATTS",220)+"\n"+row("DCGM_FI_DEV_FB_USED",1024),
            row("DCGM_FI_DEV_BOARD_POWER_WATTS",240)),
            source_url="https://example.org/a")
        self.assertEqual(len(output["records"][0]["hardware_evidence"]["metrics"]),1)
        self.assertEqual(output["records"][0]["excluded_series"][0]["reason"],"missing_samples")

    def test_rejects_out_of_order_scrapes(self):
        data=dataset(row("DCGM_FI_DEV_BOARD_POWER_WATTS",220),row("DCGM_FI_DEV_BOARD_POWER_WATTS",240))
        data["snapshots"][1]["captured_at"]=data["snapshots"][0]["captured_at"]
        with self.assertRaisesRegex(ValueError,"strictly increasing"):
            import_dcgm(data,source_url="https://example.org/a")

    def test_unsupported_fields_do_not_leak_into_metrics(self):
        data=dataset(row("DCGM_FI_DEV_GPU_UTIL",95),row("DCGM_FI_DEV_GPU_UTIL",80))
        with self.assertRaisesRegex(ValueError,"no complete supported"):
            import_dcgm(data,source_url="https://example.org/a")

    def test_sentinel_values_ignored_and_series_excluded(self):
        a=row("DCGM_FI_DEV_BOARD_POWER_WATTS",220)
        b=row("DCGM_FI_DEV_BOARD_POWER_WATTS",-1)
        with self.assertRaisesRegex(ValueError,"no complete supported"):
            import_dcgm(dataset(a,b),source_url="https://example.org/a")

    def test_duplicate_metric_for_device_rejected(self):
        a=row("DCGM_FI_DEV_BOARD_POWER_WATTS",220)
        with self.assertRaisesRegex(ValueError,"duplicate metric"):
            import_dcgm(dataset(a+"\n"+a,a),source_url="https://example.org/a")

    def test_counter_cannot_be_treated_as_gauge_without_delta(self):
        value=normalize_counter("nvidia-dcgm","DCGM_FI_PROF_PCIE_TX_BYTES_TOTAL",1200)
        self.assertFalse(value["mapped"])
        self.assertEqual(value["reason"],"counter_delta_required")

    def test_mib_to_bytes_catalog_mapping(self):
        value=normalize_counter("nvidia-dcgm","DCGM_FI_DEV_FB_USED",2048,entity_id="GPU-abc")
        self.assertTrue(value["mapped"])
        self.assertEqual(value["metric"]["value"],2048*1048576)


if __name__ == "__main__":
    unittest.main()
