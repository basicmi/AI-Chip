#!/usr/bin/env python3
"""Validate independently curated model catalog and cross-reference support paths."""
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/model-catalog.json"
SUPPORT = ROOT / "data/model-support.json"
ACCESS = {"open_weights", "gated_weights", "api_only", "not_assessed"}
STATUS = {"official_model_card", "existing_support_registry"}
CAPABILITIES = {"coding", "reasoning", "agentic", "long_context", "multimodal", "tool_use"}
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_catalog(catalog, support, *, today=None):
    errors = []
    today = today or date.today()
    if catalog.get("schema_version") != "1.0":
        errors.append("catalog schema_version must be 1.0")
    try:
        reviewed = date.fromisoformat(catalog["last_reviewed"])
        if reviewed > today:
            errors.append("catalog last_reviewed cannot be in the future")
    except (KeyError, ValueError, TypeError):
        errors.append("catalog last_reviewed must be an ISO date")
    models = catalog.get("models")
    if not isinstance(models, list) or not models:
        return errors + ["catalog models must be a nonempty array"]
    ids, repos = set(), set()
    for i, model in enumerate(models):
        w = f"models[{i}]"
        if not isinstance(model, dict):
            errors.append(w + " must be an object")
            continue
        mid = model.get("id")
        if not isinstance(mid, str) or not ID.fullmatch(mid):
            errors.append(w + ".id is invalid")
        elif mid in ids:
            errors.append(w + ".id is duplicated")
        ids.add(mid)
        repository = model.get("model_id")
        if not isinstance(repository, str) or not repository or repository in repos:
            errors.append(w + ".model_id must be unique and nonempty")
        repos.add(repository)
        for key in ("display_name", "publisher", "family", "parameter_count",
                    "modality", "architecture", "notes"):
            if not isinstance(model.get(key), str) or not model[key].strip():
                errors.append(w + "." + key + " must be nonempty")
        source_url = model.get("model_url")
        try:
            parsed = urlparse(source_url)
            if parsed.scheme != "https" or not parsed.netloc or not parsed.path.strip("/"):
                errors.append(w + ".model_url must be a HTTPS model page")
        except (ValueError, TypeError):
            errors.append(w + ".model_url must be a HTTPS model page")
        if model.get("access") not in ACCESS:
            errors.append(w + ".access is invalid")
        if model.get("catalog_source_status") not in STATUS:
            errors.append(w + ".catalog_source_status is invalid")
        try:
            checked = date.fromisoformat(model["catalog_checked_at"])
            if checked > today:
                errors.append(w + ".catalog_checked_at is in the future")
        except (KeyError, ValueError, TypeError):
            errors.append(w + ".catalog_checked_at must be an ISO date")
        context = model.get("context_length_tokens")
        if context is not None and (type(context) is not int or context <= 0):
            errors.append(w + ".context_length_tokens must be positive integer or null")
        if model.get("license") is not None and not isinstance(model.get("license"), str):
            errors.append(w + ".license must be a string or null")
        capabilities = model.get("capabilities")
        if not isinstance(capabilities, list) or len(set(capabilities)) != len(capabilities) or not set(capabilities).issubset(CAPABILITIES):
            errors.append(w + ".capabilities must be a unique array of known capabilities")
    support_models = support.get("models", [])
    support_ids = {m.get("id") for m in support_models}
    if not support_ids.issubset(ids):
        errors.append("every supported model must be represented in the independent model catalog")
    by_id = {m.get("id"): m for m in models if isinstance(m, dict)}
    for old in support_models:
        fresh = by_id.get(old.get("id"))
        if fresh and any(fresh.get(key) != old.get(key) for key in
                         ("model_id", "display_name", "publisher")):
            errors.append(f"catalog model {old.get('id')} disagrees with support registry")
    for p in support.get("support_paths", []):
        if p.get("model_id") not in ids:
            errors.append(f"support path {p.get('id')} refers to absent catalog model")
    return errors


def main():
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        support = json.loads(SUPPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print("FAIL: cannot load catalog: " + str(error), file=sys.stderr)
        return 1
    errors = validate_catalog(catalog, support)
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    supported = {p["model_id"] for p in support["support_paths"]}
    print(f"PASS: {len(catalog['models'])} catalog checkpoints; {len(supported)} with curated accelerator evidence; {len(catalog['models'])-len(supported)} catalog-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
