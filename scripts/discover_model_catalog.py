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


def discover(catalog, query=query_repo):
    rows = []
    for model in catalog["models"]:
        model_id = model["model_id"]
        rows.append({"model_id": model_id, "catalog_checked_at": model["catalog_checked_at"],
                     "catalog_source_status": model["catalog_source_status"],
                     **query(model_id)})
    return {"schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "read_only": True,
            "model_count": len(rows),
            "observed": sum(row["status"] == "observed" for row in rows),
            "models": rows,
            "note": "Presence, modified timestamp and SHA from HF API do not establish hardware runtime support or validate all model-card metadata."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=ROOT / "data/model-catalog.json")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    try:
        catalog = json.loads(args.input.read_text(encoding="utf-8"))
        report = discover(catalog)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: observed {report['observed']}/{report['model_count']} model APIs; review results before changing catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
