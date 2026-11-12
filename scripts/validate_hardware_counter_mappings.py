#!/usr/bin/env python3
"""Validate the source-aware hardware counter mapping catalog."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "hardware-counter-mappings.json"
SCHEMA = ROOT / "schemas" / "hardware-counter-mappings.schema.json"
METRIC_SCHEMA = ROOT / "schemas" / "benchmark-results.schema.json"
sys.path.insert(0, str(ROOT / "scripts"))
from validate_benchmark_results import HARDWARE_EVIDENCE_UNITS, HARDWARE_EVIDENCE_SCOPES


def validate_catalog(catalog, metric_units=None):
    errors = []
    metric_units = metric_units or HARDWARE_EVIDENCE_UNITS
    if not isinstance(catalog, dict) or catalog.get("schema_version") != "1.0":
        return ["catalog: schema_version must be 1.0"]
    sources = catalog.get("sources")
    mappings = catalog.get("mappings")
    if not isinstance(sources, list) or not sources:
        return ["catalog: sources must be a non-empty array"]
    if not isinstance(mappings, list) or not mappings:
        return ["catalog: mappings must be a non-empty array"]

    source_ids, mapping_ids, source_keys = set(), set(), set()
    for index, source in enumerate(sources):
        where = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{where}: must be an object")
            continue
        sid = source.get("id")
        if not isinstance(sid, str) or not sid:
            errors.append(f"{where}: id is required")
        elif sid in source_ids:
            errors.append(f"{where}: duplicate source id {sid}")
        else:
            source_ids.add(sid)
        if not isinstance(source.get("vendor"), str) or not source["vendor"].strip():
            errors.append(f"{where}: vendor is required")
        if not isinstance(source.get("collector"), str) or not source["collector"].strip():
            errors.append(f"{where}: collector is required")
        url = source.get("documentation_url")
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            errors.append(f"{where}: documentation_url must be HTTP(S)")
        if source.get("status") not in {"current", "preview", "archived"}:
            errors.append(f"{where}: invalid status")
        if not isinstance(source.get("notes"), str) or not source["notes"].strip():
            errors.append(f"{where}: notes are required")

    for index, mapping in enumerate(mappings):
        where = f"mappings[{index}]"
        if not isinstance(mapping, dict):
            errors.append(f"{where}: must be an object")
            continue
        mid = mapping.get("id")
        if not isinstance(mid, str) or not mid:
            errors.append(f"{where}: id is required")
        elif mid in mapping_ids:
            errors.append(f"{where}: duplicate mapping id {mid}")
        else:
            mapping_ids.add(mid)
        sid = mapping.get("source_id")
        if not isinstance(sid, str) or sid not in source_ids:
            errors.append(f"{where}: unknown source_id {sid}")
        source_metric = mapping.get("source_metric")
        if not isinstance(source_metric, str) or not source_metric.strip():
            errors.append(f"{where}: source_metric is required")
        elif (sid, source_metric) in source_keys:
            errors.append(f"{where}: duplicate source metric mapping {sid}/{source_metric}")
        source_keys.add((sid, source_metric))
        canonical = mapping.get("canonical_metric_id")
        status = mapping.get("mapping_status")
        conversion = mapping.get("conversion")
        source_unit = mapping.get("source_unit")
        canonical_unit = mapping.get("canonical_unit")
        if status not in {"direct", "unit_converted", "proxy", "reference_only"}:
            errors.append(f"{where}: invalid mapping_status")
        if status == "reference_only":
            if canonical is not None or canonical_unit is not None or conversion != "none":
                errors.append(f"{where}: reference_only mappings cannot claim a canonical metric or conversion")
        else:
            if canonical not in metric_units:
                errors.append(f"{where}: unknown canonical_metric_id {canonical}")
            elif canonical_unit != metric_units[canonical]:
                errors.append(f"{where}: canonical_unit for {canonical} must be {metric_units[canonical]}")
            if conversion == "identity" and source_unit != canonical_unit:
                errors.append(f"{where}: identity conversion requires matching source and canonical units")
            elif conversion == "ratio_to_percent" and (source_unit != "ratio" or canonical_unit != "%"):
                errors.append(f"{where}: ratio_to_percent requires ratio -> %")
            elif conversion == "mhz_to_hz" and (source_unit != "MHz" or canonical_unit != "Hz"):
                errors.append(f"{where}: mhz_to_hz requires MHz -> Hz")
            elif conversion not in {"identity", "ratio_to_percent", "mhz_to_hz"}:
                errors.append(f"{where}: invalid conversion for mapped metric")
        if status == "direct" and conversion != "identity":
            errors.append(f"{where}: direct mapping must use identity conversion")
        if status == "unit_converted" and conversion not in {"ratio_to_percent", "mhz_to_hz"}:
            errors.append(f"{where}: unit_converted mapping must declare a supported conversion")
        if status == "proxy" and mapping.get("mapping_quality") != "proxy":
            errors.append(f"{where}: proxy status must retain proxy mapping_quality")
        if not isinstance(mapping.get("mapping_quality"), str) or mapping.get("mapping_quality") not in {"direct", "proxy"}:
            errors.append(f"{where}: mapping_quality must be direct or proxy")
        if mapping.get("default_scope") not in HARDWARE_EVIDENCE_SCOPES:
            errors.append(f"{where}: invalid default_scope")
        if mapping.get("default_scope") == "per_link":
            if mapping.get("link_type") not in {"nvlink", "pcie", "infiniband", "roce", "ethernet", "other"}:
                errors.append(f"{where}: per-link mapping requires link_type")
            if not isinstance(mapping.get("entity_id"), str) or not mapping["entity_id"]:
                errors.append(f"{where}: per-link mapping requires entity_id")
        if mapping.get("default_aggregation") not in {"instantaneous", "mean", "max", "min", "p50", "p95", "p99", "sum", "rate"}:
            errors.append(f"{where}: invalid default_aggregation")
        if mapping.get("measurement_kind") not in {"hardware_counter", "telemetry", "derived"}:
            errors.append(f"{where}: invalid measurement_kind")
        if mapping.get("value_semantics") not in {
            "gauge", "ratio", "monotonic_counter", "profile_window_bytes",
            "profiler_metric", "bitmask", "reference_only"
        }:
            errors.append(f"{where}: invalid value_semantics")
        field_id = mapping.get("source_field_id")
        if field_id is not None and (
            isinstance(field_id, bool) or not isinstance(field_id, int) or field_id < 0
        ):
            errors.append(f"{where}: source_field_id must be a non-negative integer or null")
        link_type = mapping.get("link_type")
        if link_type is not None and link_type not in {
            "nvlink", "pcie", "infiniband", "roce", "ethernet", "other"
        }:
            errors.append(f"{where}: invalid link_type")
        if not isinstance(mapping.get("notes"), str) or not mapping["notes"].strip():
            errors.append(f"{where}: notes are required")
        if mapping.get("value_semantics") == "monotonic_counter" and mapping.get("default_aggregation") != "sum":
            errors.append(f"{where}: monotonic counters must normalize to interval sum after delta calculation")

    return errors


def main():
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        json.loads(SCHEMA.read_text(encoding="utf-8"))
        json.loads(METRIC_SCHEMA.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"FAIL: cannot load hardware counter mapping files: {error}", file=sys.stderr)
        return 2
    errors = validate_catalog(catalog)
    if errors:
        print("FAIL: hardware counter mapping catalog")
        for error in errors:
            print(f"- {error}")
        return 1
    sources = len(catalog["sources"])
    mappings = len(catalog["mappings"])
    print(f"PASS: {mappings} hardware counter mappings across {sources} collector families.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
