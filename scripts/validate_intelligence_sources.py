#!/usr/bin/env python3
"""Validate the curated sources used by the AI Chip intelligence discovery pipeline."""
import json, re, sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data/intelligence-sources.json"
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def validate_registry(data, *, today=None):
    errors, ids, repos = [], set(), set()
    today = today or date.today()
    if data.get("schema_version") != "1.0": errors.append("schema_version must be 1.0")
    try:
        reviewed = date.fromisoformat(data["last_reviewed"])
        if reviewed > today: errors.append("last_reviewed cannot be in the future")
    except (KeyError, TypeError, ValueError): errors.append("last_reviewed must be an ISO date")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources: return errors + ["sources must be a nonempty array"]
    for i, source in enumerate(sources):
        prefix = f"sources[{i}]"
        if not isinstance(source, dict):
            errors.append(prefix + " must be an object"); continue
        sid, repo = source.get("id"), source.get("repo")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", sid):
            errors.append(prefix + ".id is invalid")
        elif sid in ids: errors.append(prefix + ".id is duplicated")
        ids.add(sid)
        if not isinstance(repo, str) or not REPO.fullmatch(repo): errors.append(prefix + ".repo must be owner/repository")
        elif repo.lower() in repos: errors.append(prefix + ".repo is duplicated")
        repos.add(repo.lower() if isinstance(repo, str) else "")
        expected = "https://github.com/" + repo if isinstance(repo, str) else ""
        if source.get("source_url") != expected: errors.append(prefix + ".source_url must point to its canonical GitHub repository")
        if source.get("kind") != "github_releases": errors.append(prefix + ".kind is unsupported")
        if source.get("priority") not in {"high", "normal", "low"}: errors.append(prefix + ".priority is invalid")
        if type(source.get("active")) is not bool: errors.append(prefix + ".active must be boolean")
        for key in ("name", "category", "description"):
            if not isinstance(source.get(key), str) or not source[key].strip(): errors.append(prefix + "." + key + " must be nonempty")
        parsed = urlparse(source.get("source_url", ""))
        if parsed.scheme != "https" or parsed.netloc != "github.com": errors.append(prefix + ".source_url must use HTTPS github.com")
    return errors

def main():
    try: data = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print("FAIL: " + str(error), file=sys.stderr); return 1
    errors = validate_registry(data)
    if errors:
        for error in errors: print("FAIL: " + error, file=sys.stderr)
        return 1
    active = sum(source["active"] for source in data["sources"])
    print(f"PASS: {len(data['sources'])} registered sources; {active} active.")
    return 0
if __name__ == "__main__": raise SystemExit(main())
