#!/usr/bin/env python3
"""Advisory HTTP audit for source links used by the AI Chip Landscape.

This script never edits registry data. 403/429 responses are treated as blocked,
not broken, because many publishers apply bot protection to automated clients.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import ssl

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "AI-Chip-Landscape-Link-Auditor/1.0 (+https://github.com/basicmi/AI-Chip)"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def add_link(records: dict[str, set[str]], url, label: str):
    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
        return
    records[url].add(label)


def collect_links_from_data(profiles, compatibility, workloads, benchmarks):
    records: dict[str, set[str]] = defaultdict(set)
    for company in profiles.get("companies", []):
        company_name = company.get("display_name", company.get("id", "company"))
        for reference in company.get("references", []):
            add_link(records, reference.get("url"), f"{company_name} · reference · {reference.get('label', reference.get('id', ''))}")
        for evidence in company.get("evidence", []):
            add_link(records, evidence.get("url"), f"{company_name} · evidence · {evidence.get('title', evidence.get('id', ''))}")

    for platform in compatibility.get("platforms", []):
        for url in platform.get("evidence_urls", []):
            add_link(records, url, f"{platform.get('name', platform.get('id'))} · platform evidence")
    for integration in compatibility.get("integrations", []):
        add_link(records, integration.get("project_url"), f"{integration.get('project', integration.get('id'))} · project")
        for evidence in integration.get("evidence", []):
            add_link(records, evidence.get("url"), f"{integration.get('project', integration.get('id'))} · evidence")

    for path in workloads.get("paths", []):
        for url in path.get("source_urls", []):
            add_link(records, url, f"{path.get('id')} · workload path")

    for project in benchmarks.get("projects", []):
        name = project.get("name", project.get("id", "benchmark"))
        for field in ("official_url", "repository_url", "results_url", "methodology_url"):
            add_link(records, project.get(field), f"{name} · {field}")
        for source in project.get("sources", []):
            if isinstance(source, str):
                add_link(records, source, f"{name} · source")
            elif isinstance(source, dict):
                add_link(records, source.get("url"), f"{name} · {source.get('title', 'source')}")
    return records


def classify_status(status_code: int, original_url: str, final_url: str | None = None) -> str:
    if status_code in (401, 403, 429, 451):
        return "blocked"
    if status_code in (404, 410):
        return "broken"
    if 200 <= status_code < 300:
        return "redirected" if final_url and final_url.rstrip("/") != original_url.rstrip("/") else "ok"
    if 300 <= status_code < 400:
        return "redirected"
    return "http_error"


def check_url(url: str, timeout: float = 8.0) -> dict:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"}
    last_error = None
    for method in ("HEAD", "GET"):
        request = Request(url, headers=headers, method=method)
        if method == "GET":
            request.add_header("Range", "bytes=0-0")
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                final_url = response.geturl()
                return {
                    "url": url,
                    "status": classify_status(status, url, final_url),
                    "http_status": status,
                    "final_url": final_url,
                    "detail": "",
                }
        except HTTPError as error:
            if method == "HEAD" and error.code in (405, 501):
                last_error = f"HEAD not supported ({error.code}); retried with GET"
                continue
            return {
                "url": url,
                "status": classify_status(error.code, url, error.geturl()),
                "http_status": error.code,
                "final_url": error.geturl(),
                "detail": str(error.reason or ""),
            }
        except (URLError, TimeoutError, socket.timeout, ssl.SSLError) as error:
            last_error = str(getattr(error, "reason", error))
            if method == "HEAD":
                continue
            return {
                "url": url,
                "status": "unreachable",
                "http_status": None,
                "final_url": "",
                "detail": last_error,
            }
    return {
        "url": url,
        "status": "unreachable",
        "http_status": None,
        "final_url": "",
        "detail": last_error or "No HTTP response",
    }


def build_report(records, results, checked_at: str) -> str:
    counts = Counter(item["status"] for item in results)
    lines = [
        "# AI Chip Landscape — Source Link Audit",
        "",
        f"- Checked at: {checked_at}",
        f"- Unique URLs: {len(records)}",
        f"- Results: {sum(counts.values())}",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status in ("ok", "redirected", "blocked", "broken", "unreachable", "http_error"):
        lines.append(f"| {status} | {counts.get(status, 0)} |")
    issues = [item for item in results if item["status"] != "ok"]
    lines.extend(["", "## Links requiring attention", ""])
    if not issues:
        lines.append("No non-OK responses were returned.")
    else:
        lines.extend(["| Status | HTTP | URL | Referenced by | Detail |", "|---|---:|---|---|---|"])
        for item in issues:
            labels = "; ".join(sorted(records[item["url"]]))
            detail = (item.get("detail") or "").replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {item['status']} | {item.get('http_status') or '—'} | "
                f"[link]({item['url']}) | {labels} | {detail} |"
            )
    lines.extend([
        "",
        "> This audit is advisory. HTTP 403/429 and other blocked responses are not classified as broken. "
        "A reachable URL does not prove that its content supports a particular technical claim.",
        "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    profiles = load_json(ROOT / "data" / "company-profiles.json")
    compatibility = load_json(ROOT / "data" / "compatibility.json")
    workloads = load_json(ROOT / "data" / "workloads.json")
    benchmarks = load_json(ROOT / "data" / "benchmark-projects.json")
    records = collect_links_from_data(profiles, compatibility, workloads, benchmarks)

    results = [None] * len(records)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(check_url, url, args.timeout): index
                   for index, url in enumerate(sorted(records))}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    report = build_report(records, results, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote advisory link report to {args.output} ({len(records)} unique URLs).")
    else:
        print(report)


if __name__ == "__main__":
    main()
