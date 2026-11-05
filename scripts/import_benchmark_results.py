#!/usr/bin/env python3
"""Import public AI accelerator benchmark results into the normalized registry.

The importer preserves source attribution and the original system/workload
context. It never derives cross-suite scores or fills missing measurements.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "benchmark-results.json"
MLPERF_SUMMARY = "https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/summary.json"
MLPERF_RELEASE = "https://mlcommons.org/2026/09/mlperf-inference-v6-1-results/"
INFERENCEX_BASE = "https://inferencex.semianalysis.com"
INFERENCEX_AVAILABILITY = INFERENCEX_BASE + "/api/v1/availability"
INFERENCEX_BENCHMARKS = INFERENCEX_BASE + "/api/v1/benchmarks"
USER_AGENT = "AI-Chip-Landscape-Benchmark-Importer/1.0 (+https://github.com/basicmi/AI-Chip)"


def fetch_json(url: str, timeout: float = 30.0):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"HTTP {response.status} while fetching {url}")
        return json.loads(response.read().decode("utf-8"))


def as_number(value):
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result and abs(result) != float("inf") else None


def hardware_identity(name: str | None):
    text = (name or "").lower()
    rules = [
        (("mi350x",), "AMD", "amd-gpu", "mi350x"),
        (("mi355x",), "AMD", "amd-gpu", "mi355x"),
        (("gb200",), "NVIDIA", "nvidia-gpu", "gb200-nvl72"),
        (("b200",), "NVIDIA", "nvidia-gpu", "b200-sxm"),
        (("gaudi 3", "gaudi3"), "Intel", "intel-gaudi", "gaudi3"),
        (("gaudi 2", "gaudi2"), "Intel", "intel-gaudi", "gaudi2"),
        (("tpu7x", "ironwood"), "Google", "google-tpu", "tpu7x-ironwood"),
        (("tpu v6e", "trillium"), "Google", "google-tpu", "tpu-v6e-trillium"),
        (("trainium3",), "AWS", "aws-trainium", "trainium3"),
        (("trainium2",), "AWS", "aws-trainium", "trainium2"),
        (("maia 200",), "Microsoft", "microsoft-maia", "maia200"),
        (("maia 100",), "Microsoft", "microsoft-maia", "maia100"),
        (("mtia 300",), "Meta", "meta-mtia", "mtia-300"),
        (("mtia v2", "mtia-v2"), "Meta", "meta-mtia", "mtia-v2"),
        (("wse-3", "cerebras"), "Cerebras", "cerebras-wse", "wse3"),
        (("wse-2",), "Cerebras", "cerebras-wse", "wse2"),
    ]
    for needles, vendor, platform_id, product_id in rules:
        if any(needle in text for needle in needles):
            return vendor, platform_id, product_id
    if "nvidia" in text:
        return "NVIDIA", "nvidia-gpu", None
    if "amd" in text:
        return "AMD", "amd-gpu", None
    if "intel" in text or "arc" in text:
        return "Intel", "intel-xpu", None
    return None, None, None


def normalize_mlperf_record(key: str, row: dict):
    vendor, platform_id, product_id = hardware_identity(row.get("accelerator_model_name"))
    location = str(row.get("Location") or "").removeprefix("./")
    detail_url = (
        "https://github.com/mlcommons/inference_results_v6.1/tree/main/"
        + quote(location, safe="/")
        if location else None
    )
    return {
        "id": f"mlperf-inference-v6-1-{key}",
        "source_id": "mlperf-inference-v6.1",
        "source_class": "standardized_public_submission",
        "evidence_level": "mlcommons_published_submission",
        "benchmark_suite": "MLPerf Inference",
        "benchmark_version": str(row.get("version") or "v6.1"),
        "publication_date": "2026-09-16",
        "submitter": str(row.get("Organization") or "Unknown"),
        "accelerator_vendor": vendor,
        "platform_id": platform_id,
        "product_id": product_id,
        "system_type": str(row.get("SystemType") or "unknown").lower(),
        "system_name": str(row.get("SystemName") or row.get("Platform") or "Unknown system"),
        "division": str(row.get("Division") or "unknown").lower(),
        "availability": str(row.get("Availability") or "unknown").lower(),
        "model": str(row.get("Model") or "unknown"),
        "scenario": str(row.get("Scenario") or "unknown"),
        "result_value": as_number(row.get("Result")),
        "result_unit": str(row.get("Units") or ""),
        "accuracy_text": str(row.get("Accuracy") or ""),
        "inferred": as_number(row.get("inferred")) == 1,
        "power_metrics_available": row.get("has_power") is True,
        "design_power_watts": as_number(row.get("design_power_watts")),
        "system": {
            "nodes": as_number(row.get("number_of_nodes")),
            "host_processor_model": str(row.get("host_processor_model_name") or ""),
            "host_processors_per_node": as_number(row.get("host_processors_per_node")),
            "host_processor_core_count": as_number(row.get("host_processor_core_count")),
            "accelerator_model": str(row.get("accelerator_model_name") or ""),
            "accelerators_per_node": as_number(row.get("accelerators_per_node")),
            "total_accelerators": as_number(row.get("total_accelerators")),
            "platform": str(row.get("Platform") or ""),
        },
        "software": {
            "framework": str(row.get("framework") or ""),
            "operating_system": str(row.get("operating_system") or ""),
        },
        "notes": str(row.get("notes") or ""),
        "compliance": str(row.get("compliance") or ""),
        "errors": int(as_number(row.get("errors")) or 0),
        "weight_data_types": str(row.get("weight_data_types") or ""),
        "source_record_key": str(key),
        "source_location": location,
        "source_url": detail_url,
        "dataset_url": "https://raw.githubusercontent.com/mlcommons/inference_results_v6.1/main/summary.json",
        "release_url": MLPERF_RELEASE,
    }


def normalize_inferencex_record(row: dict, endpoint_url: str):
    hardware = str(row.get("hardware") or "")
    vendor, platform_id, product_id = hardware_identity(hardware)
    metrics = row.get("metrics") or {}
    if not isinstance(metrics, dict):
        metrics = {}
    return {
        "id": f"inferencex-{row.get('id')}",
        "source_id": "inferencex",
        "source_class": "third_party_public_benchmark",
        "evidence_level": "publisher_published_observation",
        "benchmark_suite": "SemiAnalysis InferenceX",
        "benchmark_version": "public-api-v1",
        "publication_date": row.get("date"),
        "submitter": "SemiAnalysis",
        "accelerator_vendor": vendor,
        "platform_id": platform_id,
        "product_id": product_id,
        "system_type": "datacenter",
        "system_name": hardware or "Hardware not specified",
        "division": "third_party",
        "availability": "published",
        "model": str(row.get("model") or "unknown"),
        "scenario": str(row.get("benchmark_type") or "unknown"),
        "result_value": None,
        "result_unit": "",
        "accuracy_text": "",
        "inferred": False,
        "power_metrics_available": (
            metrics.get("power_valid") == 1
            and metrics.get("power_metric_schema_version") == 2
        ),
        "design_power_watts": None,
        "system": {
            "hardware": hardware,
            "physical_prefill_gpus": as_number(row.get("num_prefill_gpu")),
            "physical_decode_gpus": as_number(row.get("num_decode_gpu")),
            "is_multinode": bool(row.get("is_multinode", False)),
        },
        "software": {
            "framework": str(row.get("framework") or ""),
            "operating_system": "",
            "image": row.get("image"),
            "recipe_fingerprint": row.get("recipe_fingerprint"),
        },
        "workload": {
            "model": row.get("model"),
            "benchmark_type": row.get("benchmark_type"),
            "isl": row.get("isl"),
            "osl": row.get("osl"),
            "concurrency": row.get("conc"),
            "precision": row.get("precision"),
            "speculative_method": row.get("spec_method"),
            "disaggregated": row.get("disagg"),
        },
        "configuration": {
            key: row.get(key) for key in (
                "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
                "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers",
                "offload_mode", "workflow_run_id", "run_started_at"
            ) if key in row
        },
        "metrics": {
            key: value for key, value in metrics.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        },
        "notes": (
            "Public InferenceX result row. Metric units follow the InferenceX API contract: "
            "time metrics such as p99_itl and p99_tpot are seconds; throughput metrics are "
            "tokens/s per GPU unless the metric name states otherwise. For strict power "
            "comparisons require power_valid=1 and power_metric_schema_version=2."
        ),
        "compliance": "publisher_published",
        "errors": 0,
        "weight_data_types": str(row.get("precision") or ""),
        "source_record_key": str(row.get("id")),
        "source_location": "",
        "source_url": endpoint_url,
        "detail_url": row.get("run_url"),
        "dataset_url": endpoint_url,
        "release_url": INFERENCEX_BASE + "/",
    }


def summarize(records):
    def count(field):
        result = Counter(str(row.get(field) or "unknown") for row in records)
        return dict(sorted(result.items()))
    return {
        "total_records": len(records),
        "by_source": count("source_id"),
        "by_availability": count("availability"),
        "by_division": count("division"),
        "by_system_type": count("system_type"),
        "inferred_records": sum(1 for row in records if row.get("inferred")),
        "power_records": sum(1 for row in records if row.get("power_metrics_available")),
        "submitters": len({row.get("submitter") for row in records}),
        "models": len({row.get("model") for row in records}),
    }


def import_mlperf():
    payload = fetch_json(MLPERF_SUMMARY)
    if not isinstance(payload, dict):
        raise RuntimeError("MLPerf summary.json must be an object keyed by result row")
    records = [normalize_mlperf_record(key, row) for key, row in payload.items() if isinstance(row, dict)]
    source = {
        "id": "mlperf-inference-v6.1",
        "name": "MLPerf Inference v6.1",
        "publisher": "MLCommons",
        "source_class": "standardized_public_submission",
        "version": "v6.1",
        "publication_date": "2026-09-16",
        "results_url": "https://mlcommons.org/benchmarks/inference-datacenter/",
        "release_url": MLPERF_RELEASE,
        "dataset_url": MLPERF_SUMMARY,
        "repository_url": "https://github.com/mlcommons/inference_results_v6.1",
        "record_count": len(records),
        "notes": (
            "Official MLCommons summary.json. Preserve Available, Preview and RDI status, "
            "Closed/Open division and inferred flags. The summary extract does not provide "
            "measured power records; design_power_watts is not a measured power metric."
        ),
    }
    return source, records


def import_inferencex(models: list[str] | None = None):
    availability = fetch_json(INFERENCEX_AVAILABILITY)
    if not isinstance(availability, list):
        raise RuntimeError("InferenceX availability endpoint did not return an array")
    available_models = sorted({
        str(item.get("model")) for item in availability
        if isinstance(item, dict) and item.get("model")
    })
    selected_models = sorted(set(models)) if models else available_models
    records = []
    warnings = []
    for model in selected_models:
        endpoint = INFERENCEX_BENCHMARKS + "?" + urlencode({"model": model})
        try:
            rows = fetch_json(endpoint)
            if not isinstance(rows, list):
                warnings.append(f"{model}: benchmark endpoint did not return an array")
                continue
            records.extend(
                normalize_inferencex_record(row, endpoint)
                for row in rows if isinstance(row, dict) and row.get("id") is not None
            )
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as error:
            warnings.append(f"{model}: {error}")
    source = {
        "id": "inferencex",
        "name": "SemiAnalysis InferenceX",
        "publisher": "SemiAnalysis",
        "source_class": "third_party_public_benchmark",
        "version": "Public API v1",
        "publication_date": None,
        "results_url": INFERENCEX_BASE + "/",
        "api_url": INFERENCEX_BASE + "/api",
        "availability_endpoint": INFERENCEX_AVAILABILITY,
        "benchmark_endpoint": INFERENCEX_BENCHMARKS,
        "record_count": len(records),
        "import_status": "imported" if records else "no_rows_returned",
        "notes": (
            "Public API benchmark rows retain model, hardware, framework, precision, ISL/OSL, "
            "concurrency, parallelism, image, recipe fingerprint, metric map and run URL. "
            "Do not treat missing power validity as valid power; strict power comparisons "
            "require power_valid=1 and power_metric_schema_version=2."
        ),
    }
    return source, records, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mlperf", "inferencex", "all"), default="mlperf")
    parser.add_argument("--model", action="append", dest="models",
                        help="InferenceX display model to import; repeat to select multiple models. Default: all models in availability.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = date.today().isoformat()
    existing = {}
    if args.output.exists():
        existing = json.loads(args.output.read_text(encoding="utf-8"))
    records = list(existing.get("records", []))
    sources = list(existing.get("sources", []))
    replace_sources = set()
    warnings = []

    if args.source in ("mlperf", "all"):
        source, imported = import_mlperf()
        replace_sources.add(source["id"])
        records = [row for row in records if row.get("source_id") != source["id"]]
        records.extend(imported)
        sources = [item for item in sources if item.get("id") != source["id"]]
        sources.append(source)

    if args.source in ("inferencex", "all"):
        source, imported, source_warnings = import_inferencex(args.models)
        warnings.extend(source_warnings)
        replace_sources.add(source["id"])
        records = [row for row in records if row.get("source_id") != source["id"]]
        records.extend(imported)
        sources = [item for item in sources if item.get("id") != source["id"]]
        sources.append(source)

    records.sort(key=lambda row: (row.get("source_id", ""), row.get("id", "")))
    database = {
        "schema_version": "1.0",
        "database_version": datetime.now(timezone.utc).strftime("%Y.%m.%d"),
        "last_imported_at": today,
        "scope": (
            "Normalized public benchmark submissions and observations. Preserve source attribution, "
            "system boundaries, workload and software configuration. This is not a universal leaderboard; "
            "compare only records within a matched benchmark/model/scenario/division/system type/unit/quality context."
        ),
        "sources": sorted(sources, key=lambda item: item.get("id", "")),
        "summary": summarize(records),
        "records": records,
    }

    print(f"Prepared {len(records)} records from {len(sources)} sources.")
    print(json.dumps(database["summary"], indent=2))
    for warning in warnings:
        print("WARNING:", warning, file=sys.stderr)
    if args.dry_run:
        print("Dry run: no file written.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(database, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
