#!/usr/bin/env python3
"""Read-only availability/metadata check of curated Hugging Face model IDs."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def query_repo(model_id, opener=urllib.request.urlopen):
    url = "https://huggingface.co/api/models/" + quote(model_id, safe="/")
    request = urllib.request.Request(url, headers={"User-Agent": "AI-Chip-model-catalog-audit/1.0"})
    try:
        with opener(request, timeout=12) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or payload.get("id") != model_id:
            raise ValueError("unexpected model response identifier")
        return {"status": "observed", "repo_sha": payload.get("sha"),
                "last_modified": payload.get("lastModified"),
                "gated": payload.get("gated"), "private": payload.get("private")}
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        return {"status": "unavailable", "error": type(error).__name__}


PUBLISHER_ORGS = ("Qwen", "deepseek-ai", "moonshotai", "openai", "meta-llama", "mistralai")


def discover_publisher_candidates(catalog, *, opener=urllib.request.urlopen, limit=30):
    """Read public HF organization indexes. Candidates are unverified, not curated models."""
    known = {m["model_id"] for m in catalog["models"]}
    candidates, errors = [], []
    for organization in PUBLISHER_ORGS:
        url = ("https://huggingface.co/api/models?author=" + quote(organization) +
               "&sort=createdAt&direction=-1&limit=" + str(limit))
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AI-Chip-model-catalog-audit/1.0"})
            with opener(request, timeout=12) as response:
                data = json.load(response)
            if not isinstance(data, list):
                raise ValueError("expected list from model API")
            for item in data:
                if not isinstance(item, dict):
                    continue
                model_id = item.get("id")
                if (isinstance(model_id, str) and model_id.startswith(organization + "/")
                        and model_id not in known):
                    candidates.append({
                        "model_id": model_id,
                        "created_at": item.get("createdAt"),
                        "last_modified": item.get("lastModified"),
                        "repo_sha": item.get("sha"),
                        "status": "discovery_candidate_not_reviewed",
                    })
        except (urllib.error.URLError, ValueError, TimeoutError) as error:
            errors.append({"publisher_org": organization, "error": type(error).__name__})
    return {"candidates": candidates, "source_errors": errors,
            "note": "Publisher listing only: entries may be variants, stale, gated, test uploads or unverified; manual review required."}


def discover(catalog, query=query_repo, publisher_search=None):
    rows = []
    for model in catalog["models"]:
        model_id = model["model_id"]
        rows.append({"model_id": model_id, "catalog_checked_at": model["catalog_checked_at"],
                     "catalog_source_status": model["catalog_source_status"],
                     **query(model_id)})
    discovery = publisher_search(catalog) if publisher_search else {"candidates": [], "source_errors": []}
    return {"schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "read_only": True,
            "model_count": len(rows),
            "observed": sum(row["status"] == "observed" for row in rows),
            "models": rows,
            "new_publisher_candidates": discovery["candidates"],
            "publisher_discovery_errors": discovery["source_errors"],
            "note": "Presence, modified timestamp and SHA from HF API do not establish hardware runtime support or validate all model-card metadata."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=ROOT / "data/model-catalog.json")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        catalog = json.loads(args.input.read_text(encoding="utf-8"))
        report = discover(catalog, publisher_search=discover_publisher_candidates)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: observed {report['observed']}/{report['model_count']} known model APIs; {len(report['new_publisher_candidates'])} unreviewed publisher candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
