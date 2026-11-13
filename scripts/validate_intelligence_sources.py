#!/usr/bin/env python3
"""Validate curated sources for the AI Chip intelligence discovery pipeline."""
import json, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/intelligence-sources.json"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
KINDS = {"github_releases", "rss_atom", "arxiv_api"}

def valid_https(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except (TypeError, ValueError):
        return False

def validate_registry(data, *, today=None):
    errors, ids, repos, feed_urls = [], set(), set(), set()
    today = today or date.today()
    if data.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    try:
        reviewed = date.fromisoformat(data["last_reviewed"])
        if reviewed > today:
            errors.append("last_reviewed cannot be in the future")
    except (KeyError, TypeError, ValueError):
        errors.append("last_reviewed must be an ISO date")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["sources must be a nonempty array"]
    for i, source in enumerate(sources):
        prefix = f"sources[{i}]"
        if not isinstance(source, dict):
            errors.append(prefix + " must be an object")
            continue
        sid, kind = source.get("id"), source.get("kind")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", sid):
            errors.append(prefix + ".id is invalid")
        elif sid in ids:
            errors.append(prefix + ".id is duplicated")
        ids.add(sid)
        if kind not in KINDS:
            errors.append(prefix + ".kind is unsupported")
        if not valid_https(source.get("source_url")):
            errors.append(prefix + ".source_url must be HTTPS")
        if source.get("priority") not in {"high", "normal", "low"}:
            errors.append(prefix + ".priority is invalid")
        if type(source.get("active")) is not bool:
            errors.append(prefix + ".active must be boolean")
        for key in ("name", "category", "description"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                errors.append(prefix + "." + key + " must be nonempty")
        if kind == "github_releases":
            repo = source.get("repo")
            if not isinstance(repo, str) or not REPO.fullmatch(repo):
                errors.append(prefix + ".repo must be owner/repository")
            elif repo.lower() in repos:
                errors.append(prefix + ".repo is duplicated")
            repos.add(repo.lower() if isinstance(repo, str) else "")
            if source.get("source_url") != "https://github.com/" + str(repo):
                errors.append(prefix + ".source_url must point to its canonical GitHub repository")
        elif kind == "rss_atom":
            feed_url = source.get("feed_url")
            if not valid_https(feed_url):
                errors.append(prefix + ".feed_url must be HTTPS")
            elif feed_url in feed_urls:
                errors.append(prefix + ".feed_url is duplicated")
            feed_urls.add(feed_url)
            if not isinstance(source.get("publisher"), str) or not source["publisher"].strip():
                errors.append(prefix + ".publisher must be nonempty")
        elif kind == "arxiv_api":
            if not isinstance(source.get("query"), str) or not source["query"].strip():
                errors.append(prefix + ".query must be nonempty")
            if source.get("source_url") != "https://arxiv.org/":
                errors.append(prefix + ".source_url must be https://arxiv.org/")
            limit = source.get("max_results", 100)
            if type(limit) is not int or not 1 <= limit <= 200:
                errors.append(prefix + ".max_results must be an integer from 1 to 200")
    return errors

def main():
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    errors = validate_registry(data)
    if errors:
        for error in errors:
            print("FAIL: " + error, file=sys.stderr)
        return 1
    active = sum(source["active"] for source in data["sources"])
    counts = {kind: sum(source["active"] and source["kind"] == kind for source in data["sources"]) for kind in sorted(KINDS)}
    print(f"PASS: {len(data['sources'])} registered sources; {active} active; {counts}.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
