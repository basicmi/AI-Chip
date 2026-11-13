#!/usr/bin/env python3
"""Source-aware mapping from profiler/telemetry fields to canonical hardware metrics."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "hardware-counter-mappings.json"


def load_catalog(path: Path = CATALOG_PATH):
    return json.loads(path.read_text(encoding="utf-8"))


def find_mapping(source_id: str, source_metric: str, catalog=None):
    catalog = catalog or load_catalog()
    for mapping in catalog.get("mappings", []):
        if mapping.get("source_id") == source_id and mapping.get("source_metric") == source_metric:
            return mapping
    return None


def normalize_counter(source_id: str, source_metric: str, value=None, *,
                      counter_delta=None, scope=None, aggregation=None,
                      entity_id=None, catalog=None):
    """Return one canonical evidence metric, or a non-mapped result.

    Monotonic counters are intentionally not differenced here: callers must supply
    a separately calculated counter_delta from two valid observations.
    """
    mapping = find_mapping(source_id, source_metric, catalog)
    if mapping is None:
        return {"mapped": False, "reason": "no_exact_source_mapping", "source_metric": source_metric}

    if mapping["mapping_status"] == "reference_only":
        return {
            "mapped": False,
            "reason": "reference_only_semantics_not_normalized",
            "source_metric": source_metric,
            "notes": mapping["notes"],
        }

    semantics = mapping["value_semantics"]
    if semantics == "monotonic_counter":
        if counter_delta is None:
            return {
                "mapped": False,
                "reason": "counter_delta_required",
                "source_metric": source_metric,
                "notes": "Supply counter_delta computed from two valid, ordered observations; raw cumulative values are not interval traffic.",
            }
        value = counter_delta
    elif value is None:
        return {"mapped": False, "reason": "value_required", "source_metric": source_metric}

    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{source_metric}: value must be a finite non-negative number")

    conversion = mapping["conversion"]
    if conversion == "ratio_to_percent":
        if value > 1:
            raise ValueError(f"{source_metric}: ratio input must be in [0, 1]")
        normalized_value = value * 100
    elif conversion == "mib_to_bytes":
        normalized_value = value * 1048576
    elif conversion == "mhz_to_hz":
        normalized_value = value * 1_000_000
    elif conversion == "identity":
        normalized_value = value
    else:
        raise ValueError(f"{source_metric}: unsupported conversion {conversion}")

    resolved_scope = scope or mapping["default_scope"]
    resolved_aggregation = aggregation or mapping["default_aggregation"]
    resolved_entity_id = entity_id or mapping.get("entity_id")
    if resolved_scope == "per_link" and not resolved_entity_id:
        raise ValueError(f"{source_metric}: per-link metrics require an entity_id")

    metric = {
        "metric_id": mapping["canonical_metric_id"],
        "value": normalized_value,
        "unit": mapping["canonical_unit"],
        "measurement_kind": mapping["measurement_kind"],
        "aggregation": resolved_aggregation,
        "scope": resolved_scope,
        "source_name": source_metric,
        "mapping_quality": mapping["mapping_quality"],
        "mapping_note": mapping["notes"],
    }
    if mapping.get("link_type"):
        metric["link_type"] = mapping["link_type"]
    if resolved_entity_id:
        metric["entity_id"] = resolved_entity_id
    return {"mapped": True, "metric": metric, "mapping_id": mapping["id"]}


def normalize_payload(payload, catalog=None):
    """Normalize a self-describing JSON counter export into a v1.0 evidence bundle."""
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    source_id = payload.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("source_id is required")
    for field in ("collector", "system_scope", "sampling", "provenance"):
        if not isinstance(payload.get(field), dict):
            raise ValueError(f"{field} must be an object")
    counters = payload.get("counters")
    if not isinstance(counters, list) or not counters:
        raise ValueError("counters must be a non-empty array")

    metrics, unmapped = [], []
    for index, counter in enumerate(counters):
        if not isinstance(counter, dict):
            raise ValueError(f"counters[{index}] must be an object")
        source_metric = counter.get("source_metric")
        if not isinstance(source_metric, str) or not source_metric:
            raise ValueError(f"counters[{index}].source_metric is required")
        result = normalize_counter(
            source_id, source_metric, counter.get("value"),
            counter_delta=counter.get("counter_delta"),
            scope=counter.get("scope"), aggregation=counter.get("aggregation"),
            entity_id=counter.get("entity_id"), catalog=catalog,
        )
        if result["mapped"]:
            metrics.append(result["metric"])
        else:
            unmapped.append({
                "source_metric": source_metric,
                "reason": result["reason"],
                "notes": result.get("notes"),
            })

    evidence = {
        "schema_version": "1.0",
        "collector": payload["collector"],
        "system_scope": payload["system_scope"],
        "sampling": payload["sampling"],
        "provenance": payload["provenance"],
        "metrics": metrics,
    }
    if payload.get("notes"):
        evidence["notes"] = payload["notes"]
    return {"hardware_evidence": evidence, "unmapped_counters": unmapped}
