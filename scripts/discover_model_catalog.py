#!/usr/bin/env python3
"""Read-only availability/metadata check of curated Hugging Face model IDs."""
import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER_ORGS = ("Qwen", "deepseek-ai", "moonshotai", "openai", "meta-llama", "mistralai")
PUBLISHER_EXPAND_FIELDS = (
    "createdAt", "lastModified", "sha", "pipeline_tag", "library_name",
    "tags", "downloads", "likes", "gated", "private",
)


def parse_timestamp(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            return None
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def model_metadata(payload):
    """Keep only public, useful repository metadata; never infer runtime support."""
    tags = payload.get("tags")
    return {
        "repo_sha": payload.get("sha"),
        "created_at": payload.get("createdAt"),
        "last_modified": payload.get("lastModified"),
        "pipeline_tag": payload.get("pipeline_tag"),
        "library_name": payload.get("library_name"),
        "tags": tags if isinstance(tags, list) else [],
        "downloads": payload.get("downloads"),
        "likes": payload.get("likes"),
        "gated": payload.get("gated"),
        "private": payload.get("private"),
    }


def query_repo(model_id, opener=urllib.request.urlopen):
    url = "https://huggingface.co/api/models/" + quote(model_id, safe="/")
    request = urllib.request.Request(url, headers={"User-Agent": "AI-Chip-model-catalog-audit/1.0"})
    try:
        with opener(request, timeout=12) as response:
            payload = json.load(response)
        if not isinstance(payload, dict) or payload.get("id") != model_id:
            raise ValueError("unexpected model response identifier")
        return {"status": "observed", **model_metadata(payload)}
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        return {"status": "unavailable", "error": type(error).__name__}


def discover_publisher_candidates(catalog, *, opener=urllib.request.urlopen, limit=30,
                                  days=45, now=None):
    """Read recent public HF organization listings; candidates remain unverified."""
    if type(days) is not int or not 1 <= days <= 180:
        raise ValueError("days must be between 1 and 180")
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    cutoff = now_dt.astimezone(timezone.utc) - timedelta(days=days)
    known = {m["model_id"] for m in catalog["models"]}
    candidates, errors = [], []
    for organization in PUBLISHER_ORGS:
        params = [
            ("author", organization), ("sort", "createdAt"),
            ("direction", "-1"), ("limit", str(limit)),
        ]
        params.extend(("expand[]", field) for field in PUBLISHER_EXPAND_FIELDS)
        url = "https://huggingface.co/api/models?" + urlencode(params)
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
                if (not isinstance(model_id, str)
                        or not model_id.startswith(organization + "/")
                        or model_id in known):
                    continue
                metadata = model_metadata(item)
                created = parse_timestamp(metadata["created_at"])
                # Missing creation dates are retained as explicitly undated leads;
                # a repository's last commit is not a substitute for its creation.
                if created is not None and created < cutoff:
                    continue
                candidates.append({
                    "model_id": model_id,
                    **metadata,
                    "date_status": "observed" if created is not None else "unknown",
                    "status": "discovery_candidate_not_reviewed",
                })
        except (urllib.error.URLError, ValueError, TimeoutError) as error:
            errors.append({"publisher_org": organization, "error": type(error).__name__})
    candidates.sort(key=lambda row: (
        row.get("created_at") or "", row["model_id"]), reverse=True)
    return {
        "candidates": candidates,
        "source_errors": errors,
        "note": "Recent publisher listing only: entries may be variants, adapters, stale, gated or test uploads; manual review required.",
    }


def discover(catalog, query=query_repo, publisher_search=None, *, days=45, now=None):
    if type(days) is not int or not 1 <= days <= 180:
        raise ValueError("days must be between 1 and 180")
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    rows = []
    for model in catalog["models"]:
        model_id = model["model_id"]
        rows.append({
            "model_id": model_id,
            "catalog_checked_at": model["catalog_checked_at"],
            "catalog_source_status": model["catalog_source_status"],
            **query(model_id),
        })
    discovery = (publisher_search(catalog, days=days, now=now_dt)
                 if publisher_search else {"candidates": [], "source_errors": []})
    return {
        "schema_version": "1.1",
        "generated_at": now_dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lookback_days": days,
        "read_only": True,
        "model_count": len(rows),
        "observed": sum(row["status"] == "observed" for row in rows),
        "models": rows,
        "new_publisher_candidates": discovery["candidates"],
        "publisher_discovery_errors": discovery["source_errors"],
        "note": "Presence, repository metadata and SHA do not establish hardware runtime support or validate all model-card metadata.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=ROOT / "data/model-catalog.json")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--days", type=int, default=45)
    args = p.parse_args()
    if args.days < 1 or args.days > 180:
        p.error("--days must be between 1 and 180")
    try:
        catalog = json.loads(args.input.read_text(encoding="utf-8"))
        report = discover(catalog, publisher_search=discover_publisher_candidates, days=args.days)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: observed {report['observed']}/{report['model_count']} known model APIs; "
          f"{len(report['new_publisher_candidates'])} recent/undated unreviewed publisher candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
