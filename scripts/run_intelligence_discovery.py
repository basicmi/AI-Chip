#!/usr/bin/env python3
"""Discover official AI systems releases, vendor feeds and research preprints."""
from __future__ import annotations
import argparse
import email.utils
import hashlib
import html
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import socket
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "AI-Chip-Intelligence-Discovery/1.1 (+https://github.com/basicmi/AI-Chip)"
TOPIC_TERMS = {
    "accelerator": ("accelerator", "gpu", "tpu", "npu", "asic"),
    "memory": ("hbm", "dram", "sram", "memory bandwidth", "kv cache"),
    "packaging": ("packaging", "chiplet", "2.5d", "3d stack", "co-packaged"),
    "interconnect": ("nvlink", "infiniband", "ethernet", "ualink", "interconnect", "optical"),
    "inference": ("inference", "decode", "prefill", "serving", "speculative decoding"),
    "training": ("training", "pretraining", "fine-tuning", "reinforcement learning"),
    "compiler-kernel": ("compiler", "kernel", "triton", "cutlass", "tilelang"),
    "agent-systems": ("agent", "agentic", "tool use", "runtime"),
    "robotics-physical-ai": ("robot", "robotics", "physical ai", "world model"),
    "power-efficiency": ("power", "energy", "efficiency", "performance per watt"),
    "security": ("confidential computing", "security", "encryption", "trusted execution"),
    "benchmark": ("benchmark", "tokens per second", "ttft", "tpot", "throughput"),
}

def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc) if parsed.utcoffset() is not None else None
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(value)
            return parsed.astimezone(timezone.utc) if parsed.utcoffset() is not None else None
        except (TypeError, ValueError, OverflowError):
            return None

RETRY_HTTP_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_ATTEMPTS = 3

def failure_category(error):
    """Classify operational errors without including URLs, credentials or bodies."""
    if isinstance(error, urllib.error.HTTPError):
        return "http_rate_limit" if error.code == 429 else "http_server_error" if error.code >= 500 else "http_client_error"
    if isinstance(error, (TimeoutError, socket.timeout)):
        return "timeout"
    if isinstance(error, (urllib.error.URLError, ConnectionError)):
        return "network"
    if isinstance(error, (ET.ParseError, UnicodeError, json.JSONDecodeError)):
        return "parse_error"
    if isinstance(error, (ValueError, TypeError, KeyError)):
        return "invalid_payload"
    return "source_error"

def retryable(error):
    if isinstance(error, urllib.error.HTTPError):
        return error.code in RETRY_HTTP_STATUS
    return isinstance(error, (TimeoutError, socket.timeout, urllib.error.URLError, ConnectionError))

def bounded_retry(call, *, attempts=MAX_ATTEMPTS, sleep=time.sleep):
    if not isinstance(attempts, int) or not 1 <= attempts <= 3:
        raise ValueError("attempts must be between 1 and 3")
    for attempt in range(1, attempts + 1):
        try:
            return call(), attempt
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError,
                ValueError, RuntimeError, ET.ParseError, OSError) as error:
            if attempt == attempts or not retryable(error):
                raise
            # Local bounded backoff; honor neither untrusted Retry-After nor URL contents.
            sleep(0.2 * (2 ** (attempt - 1)))
    raise RuntimeError("unreachable")

def fetch_bytes(url, *, timeout=12, accept="application/atom+xml, application/rss+xml, application/xml, text/xml, application/json"):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", 200)
        if status < 200 or status >= 300:
            raise RuntimeError("unexpected HTTP status")
        payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError("source response exceeds 8 MiB")
        return payload

def fetch_json(url, *, timeout=20):
    return json.loads(fetch_bytes(url, timeout=timeout, accept="application/vnd.github+json").decode("utf-8"))

def fetch_text(url, *, timeout=20):
    return fetch_bytes(url, timeout=timeout).decode("utf-8", errors="replace")

def release_fingerprint(release):
    payload = {key: release.get(key) for key in ("tag_name", "name", "body", "published_at", "updated_at", "html_url", "prerelease")}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

def clean_text(value):
    if not value:
        return ""
    value = html.unescape(str(value))
    value = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(value.split())

def local_name(tag):
    return tag.rsplit("}", 1)[-1].lower() if isinstance(tag, str) else ""

def child_text(element, names):
    names = set(names)
    for child in list(element):
        if local_name(child.tag) in names:
            value = " ".join(part.strip() for part in child.itertext() if part.strip())
            if value:
                return value
    return ""

def item_link(element):
    links = [child for child in list(element) if local_name(child.tag) == "link"]
    for link in links:
        href = link.attrib.get("href")
        rel = link.attrib.get("rel", "alternate")
        if href and rel in {"alternate", ""}:
            return href.strip()
    if links:
        return " ".join(links[0].itertext()).strip()
    return child_text(element, {"guid", "id"})

def item_authors(element):
    authors = []
    for child in list(element):
        if local_name(child.tag) in {"author", "creator"}:
            name = child_text(child, {"name"}) or " ".join(child.itertext()).strip()
            if name and name not in authors:
                authors.append(name)
    return authors[:8]

def item_categories(element):
    categories = []
    for child in list(element):
        if local_name(child.tag) == "category":
            value = child.attrib.get("term") or child.attrib.get("label") or " ".join(child.itertext()).strip()
            if value and value not in categories:
                categories.append(value)
    return categories[:12]

def parse_feed_document(payload):
    root = ET.fromstring(payload)
    entries = []
    for element in root.iter():
        if local_name(element.tag) in {"item", "entry"}:
            entries.append(element)
    return entries

def candidate_fingerprint(candidate):
    payload = {key: candidate.get(key) for key in ("title", "url", "published_at", "updated_at", "excerpt", "authors", "categories")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def topic_tags(title, excerpt):
    text = (title + " " + excerpt).lower()
    return sorted(tag for tag, terms in TOPIC_TERMS.items() if any(term in text for term in terms))

def build_review_actions(candidate):
    actions = [
        "Open the original source and verify the exact claim and publication date.",
        "Separate chip-level, package-level, board-level, rack-level and datacenter-level specifications.",
        "Classify lifecycle status only when the source explicitly supports announced, sampling, shipping or production.",
        "Keep vendor-reported performance separate from independently measured results.",
    ]
    if candidate.get("candidate_type") == "research_preprint":
        actions = [
            "Check whether the preprint has a peer-reviewed or conference version; arXiv submission alone is not peer review.",
            "Inspect methodology, workload, model, precision, batch/concurrency and hardware configuration before comparing results.",
            "Reproduce or triangulate quantitative claims before adding them to benchmark data.",
            "Separate proposed methods from demonstrated hardware/product capabilities.",
        ]
    elif candidate.get("candidate_type") == "project_release":
        actions = [
            "Inspect release notes and linked commits for user-visible capability changes.",
            "Distinguish merged code, experimental support and production-ready support.",
            "Check affected hardware, software versions, precision and workload scope before changing compatibility data.",
        ]
    elif candidate.get("candidate_type") == "model_repository":
        actions = [
            "Inspect model card, architecture/configuration and immutable repository revision.",
            "Do not infer accelerator compatibility from repository existence or model metadata.",
            "Verify license, availability and model lineage before adding it to the curated model catalog.",
        ]
    return actions

def normalize_candidate(candidate):
    candidate["topic_tags"] = topic_tags(candidate.get("title", ""), candidate.get("excerpt", ""))
    candidate["review_actions"] = build_review_actions(candidate)
    candidate["review_status"] = "requires_human_review"
    return candidate

def collect_releases(source, *, since, fetcher=fetch_json, paging=None):
    repo = source["repo"]
    # GitHub Releases returns newest releases first, but creation order does
    # not guarantee publication order. Fetch a bounded set of pages and do not
    # stop early solely because an older publication date was encountered.
    per_page = 20
    max_pages = 3
    candidates = []
    seen_tags = set()
    pages_fetched = 0
    last_page_full = False
    raw_items = 0
    for page in range(1, max_pages + 1):
        payload = fetcher(f"https://api.github.com/repos/{repo}/releases?per_page={per_page}&page={page}")
        if not isinstance(payload, list) or len(payload) > per_page:
            raise ValueError("GitHub releases API returned malformed or oversized page")
        pages_fetched += 1
        raw_items += len(payload)
        last_page_full = len(payload) == per_page
        for release in payload:
            if not isinstance(release, dict) or release.get("draft") is True:
                continue
            published = parse_time(release.get("published_at") or release.get("created_at"))
            if published is None or published < since:
                continue
            tag, link = release.get("tag_name"), release.get("html_url")
            if not isinstance(tag, str) or not tag or not isinstance(link, str) or not link.startswith("https://github.com/"):
                continue
            if tag in seen_tags:
                continue
            seen_tags.add(tag)
            body = clean_text(release.get("body") or "")
            candidate = {
                "candidate_id": f"github-release:{repo}:{tag}",
                "candidate_type": "project_release",
                "source_id": source["id"], "source_name": source["name"],
                "publisher": source.get("publisher", source["name"]),
                "source_type": "official_project", "independence": "project",
                "category": source["category"], "repo": repo,
                "title": release.get("name") or tag, "tag_name": tag,
                "published_at": published.isoformat().replace("+00:00", "Z"),
                "updated_at": release.get("updated_at"), "url": link,
                "prerelease": bool(release.get("prerelease")),
                "excerpt": body[:1400],
                "body_excerpt": body[:1400],
                "evidence_scope": "official_project_release_metadata",
            }
            candidate["fingerprint"] = candidate_fingerprint(candidate)
            candidates.append(normalize_candidate(candidate))
        if not last_page_full:
            break
    if paging is not None:
        paging.update({
            "pages_fetched": pages_fetched,
            "raw_items_scanned": raw_items,
            "paging_cap_reached": bool(last_page_full and pages_fetched == max_pages),
            "max_pages": max_pages,
            "per_page": per_page,
        })
    return sorted(candidates, key=lambda item: (item["published_at"], item["candidate_id"]), reverse=True)

def collect_rss_atom(source, *, since, fetcher=fetch_text):
    payload = fetcher(source["feed_url"])
    entries = parse_feed_document(payload)
    candidates = []
    for entry in entries:
        title = clean_text(child_text(entry, {"title"}))
        link = item_link(entry)
        published_raw = child_text(entry, {"published", "pubdate", "updated", "date", "issued", "created"})
        published = parse_time(published_raw)
        if not title or not link or published is None or published < since:
            continue
        if not link.startswith(("https://", "http://")):
            continue
        excerpt = clean_text(child_text(entry, {"summary", "description", "encoded", "content", "abstract"}))
        updated = parse_time(child_text(entry, {"updated", "modified"}))
        guid = child_text(entry, {"guid", "id"}) or link
        stable = hashlib.sha256(guid.encode("utf-8")).hexdigest()[:20]
        candidate = {
            "candidate_id": f"feed:{source['id']}:{stable}",
            "candidate_type": "vendor_announcement" if "announcement" in source["category"] or "blog" in source["category"] else "technical_article",
            "source_id": source["id"], "source_name": source["name"],
            "publisher": source["publisher"], "source_type": "vendor_primary",
            "independence": "vendor", "category": source["category"],
            "title": title, "published_at": published.isoformat().replace("+00:00", "Z"),
            "updated_at": updated.isoformat().replace("+00:00", "Z") if updated else None,
            "url": link, "excerpt": excerpt[:1800],
            "authors": item_authors(entry), "categories": item_categories(entry),
            "evidence_scope": "official_vendor_feed_metadata_and_excerpt",
        }
        candidate["fingerprint"] = candidate_fingerprint(candidate)
        candidates.append(normalize_candidate(candidate))
    candidates.sort(key=lambda item: (item["published_at"], item["candidate_id"]), reverse=True)
    return candidates

def collect_arxiv(source, *, since, fetcher=fetch_text, paging=None, sleep=time.sleep):
    per_page = source.get("max_results", 100)
    if type(per_page) is not int or not 1 <= per_page <= 100:
        raise ValueError("arXiv max_results must be 1..100")
    max_pages = 3
    candidates = []
    seen_papers = set()
    pages_fetched = 0
    raw_items_scanned = 0
    last_page_full = False
    for page in range(max_pages):
        if page:
            sleep(3)  # Respect arXiv API spacing between paginated queries.
        params = urllib.parse.urlencode({
            "search_query": source["query"], "start": page * per_page,
            "max_results": per_page,
            "sortBy": "submittedDate", "sortOrder": "descending",
        })
        payload = fetcher("https://export.arxiv.org/api/query?" + params)
        entries = parse_feed_document(payload)
        if len(entries) > per_page:
            raise ValueError("arXiv returned more entries than requested")
        pages_fetched += 1
        raw_items_scanned += len(entries)
        last_page_full = len(entries) == per_page
        for entry in entries:
            title = clean_text(child_text(entry, {"title"}))
            abstract = clean_text(child_text(entry, {"summary"}))
            published = parse_time(child_text(entry, {"published"}))
            raw_id = child_text(entry, {"id"})
            if not title or not raw_id or published is None or published < since:
                continue
            match = re.search(r"arxiv\.org/abs/([^?#]+)", raw_id)
            if not match:
                continue
            paper_id = match.group(1)
            link = "https://arxiv.org/abs/" + paper_id
            updated = parse_time(child_text(entry, {"updated"}))
            if paper_id in seen_papers:
                continue
            seen_papers.add(paper_id)
            candidate = {
                "candidate_id": "arxiv:" + paper_id,
                "candidate_type": "research_preprint",
                "source_id": source["id"], "source_name": source["name"],
                "publisher": "arXiv", "source_type": "research_paper",
                "independence": "independent", "category": source["category"],
                "title": title, "published_at": published.isoformat().replace("+00:00", "Z"),
                "updated_at": updated.isoformat().replace("+00:00", "Z") if updated else None,
                "url": link, "excerpt": abstract[:2400],
                "authors": item_authors(entry), "categories": item_categories(entry),
                "evidence_scope": "arxiv_preprint_metadata_and_abstract_not_peer_reviewed",
                "peer_review_status": "not_verified",
            }
            candidate["fingerprint"] = candidate_fingerprint(candidate)
            candidates.append(normalize_candidate(candidate))
        if not last_page_full:
            break
    if paging is not None:
        paging.update({
            "pages_fetched": pages_fetched,
            "raw_items_scanned": raw_items_scanned,
            "paging_cap_reached": bool(last_page_full and pages_fetched == max_pages),
            "max_pages": max_pages,
            "per_page": per_page,
        })
    candidates.sort(key=lambda item: (item["published_at"], item["candidate_id"]), reverse=True)
    return candidates

def candidate_from_hf(model):
    model_id = model["model_id"]
    payload = {key: model.get(key) for key in ("model_id", "repo_sha", "last_modified", "gated", "private")}
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    candidate = {
        "candidate_id": "hf-model:" + model_id, "fingerprint": fingerprint,
        "candidate_type": "model_repository", "source_id": "huggingface-model-catalog",
        "source_name": "Hugging Face model repository", "publisher": "Hugging Face",
        "source_type": "repository", "independence": "project", "category": "model",
        "title": model_id, "model_id": model_id, "published_at": model.get("last_modified"),
        "url": "https://huggingface.co/" + model_id, "repo_sha": model.get("repo_sha"),
        "excerpt": "", "evidence_scope": "model_repository_metadata_only",
    }
    return normalize_candidate(candidate)

def apply_change_detection(candidates, state, *, now):
    records = state.setdefault("items", {})
    changes = []
    for candidate in candidates:
        candidate_id, fingerprint = candidate["candidate_id"], candidate["fingerprint"]
        previous = records.get(candidate_id)
        if previous is None:
            status, first_seen = "new", now
        elif previous.get("fingerprint") != fingerprint:
            status, first_seen = "updated", previous.get("first_seen_at", now)
        else:
            status, first_seen = "unchanged", previous.get("first_seen_at", now)
        records[candidate_id] = {"fingerprint": fingerprint, "first_seen_at": first_seen, "last_seen_at": now}
        changes.append({**candidate, "change_status": status, "first_seen_at": first_seen, "last_seen_at": now})
    cutoff = parse_time(now) - timedelta(days=180)
    for key, value in list(records.items()):
        seen = parse_time(value.get("last_seen_at"))
        if seen is None or seen < cutoff:
            del records[key]
    return changes

def build_evidence_review_packet(report):
    items = report["review_queue"]
    lines = [
        "# AI Chip Intelligence — Evidence Review Packet", "",
        f"- Generated: {report['generated_at']}",
        f"- Lookback: {report['lookback_days']} days",
        f"- Sources observed: {report['sources_observed']}/{report['source_count']}",
        f"- Candidates: {report['candidate_count']} · new: {report['change_counts']['new']} · updated: {report['change_counts']['updated']} · unchanged: {report['change_counts']['unchanged']}",
        f"- Research preprints: {report['candidate_type_counts'].get('research_preprint', 0)}",
        f"- Vendor announcements/articles: {report['candidate_type_counts'].get('vendor_announcement', 0) + report['candidate_type_counts'].get('technical_article', 0)}",
        "", "## Review queue", "",
    ]
    if not items:
        lines.append("No new or changed candidates in this run.")
    for index, item in enumerate(items[:150], 1):
        lines.extend([
            f"### {index}. [{item['change_status'].upper()}] {item['title']}",
            f"- Type: {item['candidate_type']} · Publisher: {item.get('publisher', 'unknown')}",
            f"- Source: {item['source_name']} · Published: {item.get('published_at') or 'not provided'}",
            f"- Topics: {', '.join(item.get('topic_tags', [])) or 'unclassified'}",
            f"- Evidence scope: {item['evidence_scope']}",
            f"- Original source: {item['url']}",
        ])
        if item.get("authors"):
            lines.append("- Authors: " + ", ".join(item["authors"]))
        if item.get("excerpt"):
            lines.extend(["", "> " + item["excerpt"].replace("\n", " ")[:1000]])
        lines.extend(["", "**Review actions**"])
        lines.extend("- [ ] " + action for action in item.get("review_actions", []))
        lines.extend(["", "**Decision:** pending human review", ""])
    if report["errors"]:
        lines.extend(["## Source errors", ""])
        lines.extend(f"- {error['source_id']}: {error['error']}" for error in report["errors"])
    lines.extend([
        "", "## Evidence-to-PR protocol", "",
        "1. Open the original source; confirm date, author/publisher and the exact wording.",
        "2. Extract atomic claims. Record source type, independence, scope, units and lifecycle status.",
        "3. Seek independent corroboration for performance, availability, compatibility and market claims.",
        "4. Map each approved claim to an existing registry field and schema.",
        "5. Generate a narrowly scoped data patch with source URLs and tests; keep disputed or unverified claims out.",
        "", "> This packet is an investigation queue, not a factual product update. No production registry is modified automatically.",
    ])
    return "\n".join(lines) + "\n"

def run_discovery(registry, catalog, *, now=None, days=45, release_fetcher=fetch_json,
                  feed_fetcher=fetch_text, model_report=None, state=None):
    now_dt = now or datetime.now(timezone.utc)
    if now_dt.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    if days < 1 or days > 180:
        raise ValueError("days must be between 1 and 180")
    now_text = now_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    since = now_dt.astimezone(timezone.utc) - timedelta(days=days)
    source_results, candidates, errors = [], [], []
    state = state if state is not None else {"schema_version": "1.0", "items": {}}
    source_health = state.setdefault("source_health", {})
    if not isinstance(source_health, dict):
        raise ValueError("invalid persistent source_health state")
    for source in registry["sources"]:
        if not source.get("active"):
            continue
        source_id = source["id"]
        previous = source_health.get(source_id, {})
        if not isinstance(previous, dict):
            raise ValueError("invalid source health record")
        failures = previous.get("consecutive_failures", 0)
        if not isinstance(failures, int) or failures < 0:
            raise ValueError("invalid consecutive source failure count")
        kind = source["kind"]
        attempts = 0
        paging = {}
        try:
            def fetch_source():
                if kind == "github_releases":
                    return collect_releases(source, since=since, fetcher=release_fetcher, paging=paging)
                if kind == "rss_atom":
                    return collect_rss_atom(source, since=since, fetcher=feed_fetcher)
                if kind == "arxiv_api":
                    return collect_arxiv(source, since=since, fetcher=feed_fetcher, paging=paging)
                raise ValueError("unsupported_source_kind")
            # Retry the full parse as well as transport, but only for transient
            # network/HTTP errors. A malformed feed is not retried.
            found, attempts = bounded_retry(fetch_source)
            candidates.extend(found)
            status = "recovered" if failures else "healthy"
            source_health[source_id] = {
                "consecutive_failures": 0, "last_success_at": now_text,
                "last_failure_at": previous.get("last_failure_at"),
                "last_failure_category": None,
            }
            source_results.append({
                "source_id": source_id, "source_name": source["name"],
                "kind": kind, "status": "observed", "recent_item_count": len(found),
                "health_transition": status, "consecutive_failures": 0,
                "attempt_count": attempts,
                **({"pagination": paging} if paging else {}),
            })
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError,
                ValueError, RuntimeError, ET.ParseError, OSError) as error:
            category = failure_category(error)
            failures += 1
            tier = "critical" if failures >= 3 else "warning" if failures == 2 else "transient"
            source_health[source_id] = {
                "consecutive_failures": failures,
                "last_success_at": previous.get("last_success_at"),
                "last_failure_at": now_text, "last_failure_category": category,
            }
            errors.append({"source_id": source_id, "error": type(error).__name__,
                           "failure_category": category, "failure_tier": tier})
            source_results.append({
                "source_id": source_id, "source_name": source["name"],
                "kind": kind, "status": "unavailable", "recent_item_count": 0,
                "failure_category": category, "failure_tier": tier,
                "consecutive_failures": failures, "attempt_count": MAX_ATTEMPTS if retryable(error) else 1,
            })
    if model_report is not None:
        for item in model_report.get("models", []):
            if item.get("status") == "observed":
                candidates.append(candidate_from_hf(item))
        for item in model_report.get("new_publisher_candidates", []):
            candidates.append(candidate_from_hf({**item, "gated": None, "private": None}))
        errors.extend({"source_id": "huggingface-model-catalog",
                       "error": item.get("error", "publisher_listing_unavailable")}
                      for item in model_report.get("publisher_discovery_errors", []))
    changes = apply_change_detection(candidates, state, now=now_text)
    counts = {key: sum(item["change_status"] == key for item in changes)
              for key in ("new", "updated", "unchanged")}
    actionable = [item for item in changes if item["change_status"] in {"new", "updated"}]
    actionable.sort(key=lambda item: (item.get("published_at") or "", item["candidate_id"]), reverse=True)
    type_counts = {}
    for item in candidates:
        type_counts[item["candidate_type"]] = type_counts.get(item["candidate_type"], 0) + 1
    report = {
        "schema_version": "1.1", "generated_at": now_text, "lookback_days": days, "read_only": True,
        "source_count": len(source_results), "sources_observed": sum(item["status"] == "observed" for item in source_results),
        "sources_unavailable": sum(row["status"] == "unavailable" for row in source_results), "candidate_count": len(candidates), "candidate_type_counts": type_counts,
        "change_counts": counts, "review_queue": actionable, "all_observations": changes,
        "source_results": source_results, "errors": errors,
        "source_health_summary": {
            "recovered": sum(row.get("health_transition") == "recovered" for row in source_results),
            "critical_failures": sum(row.get("failure_tier") == "critical" for row in source_results),
            "empty_successes": sum(row["status"] == "observed" and row["recent_item_count"] == 0 for row in source_results),
        },
        "model_catalog_summary": {
            "known_models_checked": (model_report or {}).get("model_count", 0),
            "known_model_repositories_observed": (model_report or {}).get("observed", 0),
            "new_publisher_candidates": len((model_report or {}).get("new_publisher_candidates", [])),
        },
        "policy": "Discovery metadata is an investigation lead only. It does not update formal product, company, model or hardware-support registries and does not establish benchmark results or accelerator compatibility.",
    }
    report["evidence_review_packet"] = build_evidence_review_packet(report)
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=ROOT / "data/intelligence-sources.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/model-catalog.json")
    parser.add_argument("--state-file", type=Path, default=ROOT / ".cache/ai-chip-intelligence-state.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-path", type=Path)
    parser.add_argument("--days", type=int, default=45)
    args = parser.parse_args()
    if args.days < 1 or args.days > 180:
        parser.error("--days must be between 1 and 180")
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        from validate_intelligence_sources import validate_registry
        errors = validate_registry(registry)
        if errors:
            raise ValueError("; ".join(errors))
        state = {"schema_version": "1.0", "items": {}}
        if args.state_file.exists():
            state = json.loads(args.state_file.read_text(encoding="utf-8"))
            if state.get("schema_version") != "1.0" or not isinstance(state.get("items"), dict):
                raise ValueError("invalid discovery state file")
        from discover_model_catalog import discover, discover_publisher_candidates
        model_report = discover(catalog, publisher_search=discover_publisher_candidates)
        report = run_discovery(registry, catalog, days=args.days, model_report=model_report, state=state)
        args.state_file.parent.mkdir(parents=True, exist_ok=True)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.summary_path:
            args.summary_path.parent.mkdir(parents=True, exist_ok=True)
            args.summary_path.write_text(report["evidence_review_packet"], encoding="utf-8")
        print(f"PASS: {report['candidate_count']} observations; {len(report['review_queue'])} new/updated review leads; {len(report['errors'])} source errors.")
    except (OSError, ValueError, KeyError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
