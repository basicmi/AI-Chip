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
import math
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

# Stable, source-documented metric semantics. Unknown raw metrics remain preserved
# in the source map but are not promoted into normalized comparison fields.
INFERENCEX_METRIC_DEFINITIONS = {
    "median_intvty": ("median_interactivity", "Median interactivity", "tok/s/user", "higher", "interactivity"),
    "p90_intvty": ("p90_interactivity", "P90 interactivity", "tok/s/user", "higher", "interactivity"),
    "output_tput_per_gpu": ("output_throughput_per_gpu", "Output throughput", "tok/s/GPU", "higher", "throughput"),
    "tput_per_gpu": ("total_throughput_per_gpu", "Total throughput", "tok/s/GPU", "higher", "throughput"),
    "input_tput_per_gpu": ("input_throughput_per_gpu", "Input throughput", "tok/s/GPU", "higher", "throughput"),
    "output_tput_per_total_gpu": ("output_throughput_per_total_gpu", "Output throughput per total GPU", "tok/s/GPU", "higher", "throughput"),
    "input_tput_per_total_gpu": ("input_throughput_per_total_gpu", "Input throughput per total GPU", "tok/s/GPU", "higher", "throughput"),
    "median_ttft": ("median_ttft", "Median TTFT", "s", "lower", "latency"),
    "mean_ttft": ("mean_ttft", "Mean TTFT", "s", "lower", "latency"),
    "p99_ttft": ("p99_ttft", "P99 TTFT", "s", "lower", "latency"),
    "median_tpot": ("median_tpot", "Median TPOT", "s", "lower", "latency"),
    "mean_tpot": ("mean_tpot", "Mean TPOT", "s", "lower", "latency"),
    "p99_tpot": ("p99_tpot", "P99 TPOT", "s", "lower", "latency"),
    "p99_itl": ("p99_itl", "P99 inter-token latency", "s", "lower", "latency"),
    "mean_e2el": ("mean_e2el", "Mean end-to-end latency", "s", "lower", "latency"),
    "avg_power_w": ("mean_gpu_power_per_gpu", "Mean GPU power", "W/GPU", "context", "power"),
    "avg_total_gpu_power_w": ("mean_total_gpu_power", "Mean total GPU power", "W", "context", "power"),
    "p75_power_w": ("p75_gpu_power_per_gpu", "P75 GPU power", "W/GPU", "context", "power"),
    "p75_total_gpu_power_w": ("p75_total_gpu_power", "P75 total GPU power", "W", "context", "power"),
    "p90_power_w": ("p90_gpu_power_per_gpu", "P90 GPU power", "W/GPU", "context", "power"),
    "p90_total_gpu_power_w": ("p90_total_gpu_power", "P90 total GPU power", "W", "context", "power"),
    "total_gpu_energy_j": ("total_gpu_energy", "Total GPU energy", "J", "context", "energy"),
    "joules_per_output_token": ("energy_per_output_token", "Energy per output token", "J/output token", "lower", "energy"),
    "joules_per_total_token": ("energy_per_total_token", "Energy per total token", "J/total token", "lower", "energy"),
    "joules_per_input_token": ("energy_per_input_token", "Energy per input token", "J/input token", "lower", "energy"),
    "joules_per_successful_query": ("energy_per_successful_query", "Energy per successful query", "J/query", "lower", "energy"),
    "prefill_avg_power_w": ("prefill_gpu_power_per_gpu", "Prefill GPU power", "W/GPU", "context", "power"),
    "decode_avg_power_w": ("decode_gpu_power_per_gpu", "Decode GPU power", "W/GPU", "context", "power"),
    "prefill_joules_per_input_token": ("prefill_energy_per_input_token", "Prefill energy per input token", "J/input token", "lower", "energy"),
    "decode_joules_per_output_token": ("decode_energy_per_output_token", "Decode energy per output token", "J/output token", "lower", "energy"),
    "avg_util_pct": ("mean_gpu_utilization", "Mean GPU utilization", "%", "context", "telemetry"),
    "avg_temp_c": ("mean_gpu_temperature", "Mean GPU temperature", "°C", "context", "telemetry"),
    "peak_temp_c": ("peak_gpu_temperature", "Peak GPU temperature", "°C", "context", "telemetry"),
    "avg_mem_used_mb": ("mean_gpu_memory_used", "Mean GPU memory used", "MB", "context", "telemetry"),
}
INFERENCEX_POWER_METRIC_KEYS = {
    "avg_power_w", "avg_total_gpu_power_w", "total_gpu_energy_j",
    "p75_power_w", "p75_total_gpu_power_w", "p90_power_w", "p90_total_gpu_power_w",
    "joules_per_successful_query", "joules_per_output_token", "joules_per_total_token",
    "prefill_avg_power_w", "decode_avg_power_w", "joules_per_input_token",
    "prefill_joules_per_input_token", "decode_joules_per_output_token",
    "avg_cpu_socket_power_w", "avg_total_cpu_power_w", "total_cpu_energy_j",
    "avg_total_module_power_w", "total_module_energy_j",
    "avg_total_cpu_rail_power_w", "total_cpu_rail_energy_j",
    "avg_total_cpu_sysio_power_w", "total_cpu_sysio_energy_j",
}


def normalize_inferencex_metrics(metrics: dict, power_measurement_valid: bool = False):
    normalized = {}
    for source_key, definition in INFERENCEX_METRIC_DEFINITIONS.items():
        value = metrics.get(source_key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            continue
        metric_key, label, unit, direction, family = definition
        if family in {"power", "energy"} and not power_measurement_valid:
            continue
        normalized[metric_key] = {
            "value": value,
            "unit": unit,
            "direction": direction,
            "label": label,
            "source_metric": source_key,
            "family": family,
        }
    return normalized



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
    # Product links are conservative: only map a product when the source key
    # names that exact product/generation. Vendor/platform fallback is broader.
    rules = [
        (("mi350x",), "AMD", "amd-gpu", "mi350x"),
        (("mi355x",), "AMD", "amd-gpu", "mi355x"),
        (("mi455x",), "AMD", "amd-gpu", "mi455x"),
        (("mi300x", "mi325x"), "AMD", "amd-gpu", None),
        (("vera_rubin_nvl72", "vera-rubin-nvl72", "vera rubin nvl72"), "NVIDIA", "nvidia-gpu", "vera-rubin-nvl72"),
        (("rubin_gpu", "rubin-gpu", "rubin gpu"), "NVIDIA", "nvidia-gpu", "rubin-gpu"),
        (("gb200_nvl72", "gb200-nvl72", "gb200 nvl72"), "NVIDIA", "nvidia-gpu", "gb200-nvl72"),
        (("gb300_nvl72", "gb300-nvl72", "gb300 nvl72"), "NVIDIA", "nvidia-gpu", None),
        (("b200_sxm", "b200-sxm", "b200 sxm"), "NVIDIA", "nvidia-gpu", "b200-sxm"),
        (("b300",), "NVIDIA", "nvidia-gpu", None),
        (("h100", "h200", "b100", "a100"), "NVIDIA", "nvidia-gpu", None),
        (("gaudi 3", "gaudi3"), "Intel", "intel-gaudi", "gaudi3"),
        (("gaudi 2", "gaudi2"), "Intel", "intel-gaudi", "gaudi2"),
        (("tpu7x", "ironwood"), "Google", "google-tpu", "tpu7x-ironwood"),
        (("tpu v6e", "tpu_v6e", "tpu-v6e", "trillium"), "Google", "google-tpu", "tpu-v6e-trillium"),
        (("trainium3", "trn3"), "AWS", "aws-trainium", "trainium3"),
        (("trainium2", "trn2"), "AWS", "aws-trainium", "trainium2"),
        (("maia 300", "maia300", "maia-300"), "Microsoft", "microsoft-maia", "maia300"),
        (("maia 200", "maia200", "maia-200"), "Microsoft", "microsoft-maia", "maia200"),
        (("maia 100", "maia100", "maia-100"), "Microsoft", "microsoft-maia", "maia100"),
        (("mtia 300", "mtia-300", "mtia300"), "Meta", "meta-mtia", "mtia-300"),
        (("mtia v2", "mtia-v2", "mtia_v2"), "Meta", "meta-mtia", "mtia-v2"),
        (("wse-3", "wse3"), "Cerebras", "cerebras-wse", "wse3"),
        (("wse-2", "wse2"), "Cerebras", "cerebras-wse", "wse2"),
    ]
    for needles, vendor, platform_id, product_id in rules:
        if any(needle in text for needle in needles):
            return vendor, platform_id, product_id
    if "nvidia" in text or any(token in text for token in (
        "h100", "h200", "a100", "b100", "b200", "b300", "gb200", "gb300",
        "rubin", "rtxpro", "rtx pro"
    )):
        return "NVIDIA", "nvidia-gpu", None
    if "amd" in text or any(token in text for token in ("mi300", "mi325", "mi350", "mi355", "mi455")):
        return "AMD", "amd-gpu", None
    if "intel" in text or "arc" in text:
        return "Intel", "intel-xpu", None
    if "gaudi" in text:
        return "Intel", "intel-gaudi", None
    if "tpu" in text:
        return "Google", "google-tpu", None
    if "trainium" in text or text.startswith("trn"):
        return "AWS", "aws-trainium", None
    if "mtia" in text:
        return "Meta", "meta-mtia", None
    if "maia" in text:
        return "Microsoft", "microsoft-maia", None
    if "cerebras" in text:
        return "Cerebras", "cerebras-wse", None
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


def normalize_inferencex_record(row: dict, endpoint_url: str, model_display_name: str | None = None):
    hardware = str(row.get("hardware") or "")
    vendor, platform_id, product_id = hardware_identity(hardware)
    raw_metrics = row.get("metrics") or {}
    if not isinstance(raw_metrics, dict):
        raw_metrics = {}
    metrics = {
        key: value for key, value in raw_metrics.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    }
    power_measurement_valid = (
        isinstance(metrics.get("power_valid"), (int, float))
        and metrics.get("power_valid") == 1
        and isinstance(metrics.get("power_metric_schema_version"), (int, float))
        and metrics.get("power_metric_schema_version") == 2
    )
    power_metrics_available = power_measurement_valid and any(
        key in metrics for key in INFERENCEX_POWER_METRIC_KEYS
    )
    display_model = str(model_display_name or row.get("model") or "unknown")
    raw_model = str(row.get("model") or "unknown")
    workers = row.get("workers")
    return {
        "id": f"inferencex-{row.get('id')}",
        "source_id": "inferencex",
        "source_class": "third_party_public_benchmark",
        "evidence_level": "publisher_published_observation",
        "benchmark_suite": "SemiAnalysis InferenceX",
        "benchmark_version": None,
        "publication_date": row.get("date"),
        "submitter": "SemiAnalysis",
        "accelerator_vendor": vendor,
        "platform_id": platform_id,
        "product_id": product_id,
        "system_type": "datacenter",
        "system_name": hardware or "Hardware not specified",
        "division": "third_party",
        "availability": "published",
        "model": raw_model,
        "model_display_name": display_model,
        "scenario": str(row.get("benchmark_type") or "unknown"),
        "result_value": None,
        "result_unit": "",
        "accuracy_text": "",
        "inferred": False,
        "power_metrics_available": power_metrics_available,
        "power_measurement_valid": power_measurement_valid,
        "design_power_watts": None,
        "system": {
            "hardware": hardware,
            "physical_prefill_gpus": as_number(row.get("num_prefill_gpu")),
            "physical_decode_gpus": as_number(row.get("num_decode_gpu")),
            "is_multinode": row.get("is_multinode") is True,
            "workers": workers if isinstance(workers, list) else [],
        },
        "software": {
            "framework": str(row.get("framework") or ""),
            "operating_system": "",
            "image": row.get("image"),
            "recipe_fingerprint": row.get("recipe_fingerprint"),
        },
        "workload": {
            "model": raw_model,
            "benchmark_type": row.get("benchmark_type"),
            "isl": row.get("isl"),
            "osl": row.get("osl"),
            "concurrency": row.get("conc"),
            "precision": row.get("precision"),
            "speculative_method": row.get("spec_method"),
            "disaggregated": row.get("disagg") is True,
        },
        "configuration": {
            key: row.get(key) for key in (
                "prefill_tp", "prefill_ep", "prefill_dp_attention", "prefill_num_workers",
                "decode_tp", "decode_ep", "decode_dp_attention", "decode_num_workers",
                "offload_mode", "workflow_run_id", "run_started_at"
            ) if key in row
        },
        "metrics": metrics,
        "normalized_metrics": normalize_inferencex_metrics(metrics, power_measurement_valid),
        "notes": (
            "Raw scalar metrics are preserved. Normalized metrics use source-documented units; "
            "median_intvty is interactivity in tok/s/user, not a latency metric. "
            "Power and energy metrics are normalized only when power_valid=1 and "
            "power_metric_schema_version=2. Missing metrics remain unavailable."
            + ((" Source note: " + str(row.get("notes"))) if row.get("notes") else "")
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
    warnings = []
    if not available_models:
        warnings.append("availability endpoint returned no models; refusing to replace the existing InferenceX snapshot")
    requested_models = sorted(set(models)) if models else available_models
    available_set = set(available_models)
    unknown_models = sorted(set(requested_models) - available_set)
    if unknown_models:
        warnings.append("requested model(s) are not present in availability: " + ", ".join(unknown_models))
    selected_models = [model for model in requested_models if model in available_set]

    records = []
    rows_by_model = {}
    seen_ids = set()
    for model in selected_models:
        endpoint = INFERENCEX_BENCHMARKS + "?" + urlencode({"model": model})
        try:
            rows = fetch_json(endpoint)
            if not isinstance(rows, list):
                warnings.append(f"{model}: benchmark endpoint did not return an array")
                continue
            if not rows:
                warnings.append(f"{model}: availability lists this model but benchmarks returned no rows")
                rows_by_model[model] = 0
                continue
            imported_for_model = 0
            for index, row in enumerate(rows):
                if not isinstance(row, dict) or row.get("id") is None:
                    warnings.append(f"{model}: malformed result row at index {index} (missing object/id)")
                    continue
                record_key = str(row.get("id"))
                if record_key in seen_ids:
                    warnings.append(f"{model}: duplicate benchmark result id {record_key}")
                    continue
                seen_ids.add(record_key)
                records.append(normalize_inferencex_record(row, endpoint, model_display_name=model))
                imported_for_model += 1
            rows_by_model[model] = imported_for_model
            if imported_for_model == 0:
                warnings.append(f"{model}: no valid benchmark rows were imported")
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as error:
            warnings.append(f"{model}: {error}")

    if not records and not warnings:
        warnings.append("no InferenceX benchmark rows were returned; refusing to replace the existing snapshot")

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
        "availability_model_count": len(available_models),
        "selected_models": selected_models,
        "rows_by_model": rows_by_model,
        "record_count": len(records),
        "import_status": "imported" if records else "no_rows_returned",
        "notes": (
            "Public API benchmark rows preserve the raw metric map, normalized metric semantics, "
            "model display name and key, workload shape, precision, physical prefill/decode GPU counts, "
            "parallelism, workers, image, recipe fingerprint and producer run URL. "
            "An empty or partial model refresh aborts without replacing the previous snapshot. "
            "Strict power/energy normalization requires power_valid=1 and power_metric_schema_version=2."
        ),
    }
    return source, records, warnings


def merge_inferencex_records(existing_records: list[dict], imported_records: list[dict],
                             selected_models: list[str] | None = None):
    """Replace all InferenceX rows, or only the selected models for a scoped refresh."""
    if selected_models is None:
        kept = [row for row in existing_records if row.get("source_id") != "inferencex"]
        return kept + imported_records

    selected = set(selected_models)
    selected_raw_models = {row.get("model") for row in imported_records if row.get("model")}
    selected_endpoints = {
        INFERENCEX_BENCHMARKS + "?" + urlencode({"model": model})
        for model in selected
    }
    kept = []
    for row in existing_records:
        if row.get("source_id") != "inferencex":
            kept.append(row)
            continue
        if row.get("model_display_name") in selected:
            continue
        if row.get("model") in selected_raw_models:
            continue
        if row.get("source_url") in selected_endpoints:
            continue
        kept.append(row)
    return kept + imported_records


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
        records = merge_inferencex_records(
            records, imported,
            source.get("selected_models") if args.models else None
        )
        source["record_count"] = sum(1 for row in records if row.get("source_id") == source["id"])
        if args.models:
            source["import_status"] = "partial_model_refresh"
        sources = [item for item in sources if item.get("id") != source["id"]]
        sources.append(source)

    if args.source in ("inferencex", "all"):
        try:
            source, imported, source_warnings = import_inferencex(args.models)
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as error:
            print(f"ERROR: InferenceX import failed: {error}", file=sys.stderr)
            print("Import aborted; existing registry was left unchanged.", file=sys.stderr)
            return 2
        warnings.extend(source_warnings)
        replace_sources.add(source["id"])
        records = [row for row in records if row.get("source_id") != source["id"]]
        records.extend(imported)
        sources = [item for item in sources if item.get("id") != source["id"]]
        sources.append(source)

    # Fail closed: a partial InferenceX API outage must never replace a previously
    # imported complete snapshot with an incomplete subset (or an empty dataset).
    if warnings:
        for warning in warnings:
            print("ERROR:", warning, file=sys.stderr)
        print("Import aborted; existing registry was left unchanged.", file=sys.stderr)
        return 2

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
