#!/usr/bin/env python3
"""Validate model-level hardware support mappings against product and software registries."""
import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "model-support.json"
PROFILES = ROOT / "data" / "company-profiles.json"
COMPATIBILITY = ROOT / "data" / "compatibility.json"
ERRORS = []

def check(condition, message):
    if not condition:
        ERRORS.append(message)

def valid_date(value, nullable=False):
    if nullable and value is None:
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False

def valid_url(value):
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except (TypeError, ValueError):
        return False

def main():
    try:
        db = json.loads(DATA.read_text(encoding="utf-8"))
        profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
        compatibility = json.loads(COMPATIBILITY.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot load model support inputs: {exc}", file=sys.stderr)
        return 2

    check(db.get("schema_version") == "1.0", "schema_version must be 1.0")
    check(valid_date(db.get("last_reviewed")), "invalid last_reviewed")
    companies = profiles.get("companies", [])
    products = {
        item.get("id"): item
        for company in companies for item in company.get("products", [])
        if isinstance(item, dict)
    }
    platforms = {item.get("id") for item in compatibility.get("platforms", [])}
    integrations = {item.get("id"): item for item in compatibility.get("integrations", [])}
    models = db.get("models", [])
    paths = db.get("support_paths", [])
    check(isinstance(models, list) and bool(models), "models must be a non-empty array")
    check(isinstance(paths, list) and bool(paths), "support_paths must be a non-empty array")
    model_ids = [item.get("id") for item in models if isinstance(item, dict)]
    check(len(model_ids) == len(set(model_ids)), "duplicate model IDs")
    known_models = set(model_ids)
    path_ids = [item.get("id") for item in paths if isinstance(item, dict)]
    check(len(path_ids) == len(set(path_ids)), "duplicate support path IDs")
    for index, path in enumerate(paths):
        where = f"support_paths[{index}]"
        if not isinstance(path, dict):
            check(False, f"{where} must be an object")
            continue
        check(path.get("model_id") in known_models, f"{where}: unknown model_id")
        check(path.get("platform_id") in platforms, f"{where}: unknown platform_id")
        check(path.get("support_level") in db.get("support_levels", {}), f"{where}: unknown support_level")
        product_ids = path.get("product_ids", [])
        integration_ids = path.get("integration_ids", [])
        check(isinstance(product_ids, list), f"{where}: product_ids must be an array")
        check(isinstance(integration_ids, list), f"{where}: integration_ids must be an array")
        for product_id in product_ids if isinstance(product_ids, list) else []:
            product = products.get(product_id)
            check(product is not None, f"{where}: unknown product_id {product_id}")
            if product:
                check(path.get("platform_id") in product.get("compatibility_platform_ids", []),
                      f"{where}: product {product_id} is not linked to platform {path.get('platform_id')}")
        for integration_id in integration_ids if isinstance(integration_ids, list) else []:
            integration = integrations.get(integration_id)
            check(integration is not None, f"{where}: unknown integration_id {integration_id}")
            if integration:
                check(integration.get("platform_id") == path.get("platform_id"),
                      f"{where}: integration {integration_id} belongs to another platform")
                if product_ids and integration.get("product_ids"):
                    check(set(product_ids).issubset(set(integration["product_ids"])),
                          f"{where}: product mapping exceeds integration's product-specific evidence")
        check(bool(path.get("software_stack")) and bool(path.get("hardware_scope")) and bool(path.get("limitations")),
              f"{where}: software_stack, hardware_scope and limitations are required")
        check(isinstance(path.get("precision_modes"), list) and bool(path.get("precision_modes")),
              f"{where}: precision_modes must be a non-empty array")
        evidence = path.get("evidence", [])
        check(isinstance(evidence, list) and bool(evidence), f"{where}: evidence must be non-empty")
        for evidence_index, item in enumerate(evidence if isinstance(evidence, list) else []):
            ewhere = f"{where}.evidence[{evidence_index}]"
            check(item.get("type") in {"vendor_docs", "upstream_docs", "research_paper", "independent_media", "independent_test"},
                  f"{ewhere}: invalid evidence type")
            check(valid_url(item.get("url")), f"{ewhere}: invalid URL")
            check(valid_date(item.get("checked_at")), f"{ewhere}: invalid checked_at")
            check(bool(item.get("publisher")) and bool(item.get("claim")), f"{ewhere}: publisher and claim required")
        if path.get("support_level") == "independently_tested":
            check(any(item.get("type") == "independent_test" for item in evidence),
                  f"{where}: independently_tested needs independent_test evidence")

    if ERRORS:
        print(f"FAIL: {len(ERRORS)} validation error(s)")
        for error in ERRORS:
            print("- " + error)
        return 1
    print(f"PASS: {len(models)} model families, {len(paths)} model-to-hardware support paths.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
