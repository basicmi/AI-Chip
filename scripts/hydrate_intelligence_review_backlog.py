#!/usr/bin/env python3
"""Restore full unverified Claim payloads from retained historical Actions artifacts.

The cache intentionally keeps review state separate from factual verification.
This one-time migration rehydrates the 2,525 Claim IDs already present in the
persistent cache; it never changes a human decision or promotes a Claim.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from triage_intelligence_claims import build_queue

ARTIFACT_MANIFEST = (
    {"artifact_id": 14191101297, "run_id": 43787532670},
    {"artifact_id": 14191697562, "run_id": 43789263891},
    {"artifact_id": 14193774090, "run_id": 43795362021},
    {"artifact_id": 14195870093, "run_id": 43798131776},
    {"artifact_id": 14204506216, "run_id": 43820741766},
    {"artifact_id": 14211068232, "run_id": 43837297395},
    {"artifact_id": 14240845899, "run_id": 43898014328},
    {"artifact_id": 14284954184, "run_id": 43986167889},
)


def parse_utc(value):
    if not isinstance(value, str):
        raise ValueError("artifact timestamp must be an ISO-8601 string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("artifact timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def download_artifact(repo, artifact_id, token):
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GITHUB_TOKEN is required for historical artifact recovery")
    url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AI-Chip-review-backlog-recovery",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def read_json_member(archive, basename):
    matches = [name for name in archive.namelist() if Path(name).name == basename]
    if len(matches) != 1:
        raise ValueError(f"artifact must contain exactly one {basename}")
    try:
        return json.loads(archive.read(matches[0]).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {basename} in historical artifact") from error


def extract_claims(archive_bytes, manifest):
    try:
        archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    except (zipfile.BadZipFile, OSError) as error:
        raise ValueError(f"artifact {manifest['artifact_id']} is not a valid ZIP") from error
    with archive:
        discovery = read_json_member(archive, "ai-chip-intelligence-discovery.json")
        claims_report = read_json_member(archive, "ai-chip-intelligence-claims.json")
        graph = read_json_member(archive, "ai-chip-intelligence-evidence-graph.json")

    rows = claims_report.get("claims")
    if claims_report.get("schema_version") != "1.0" or not isinstance(rows, list):
        raise ValueError("historical Claim Extraction schema mismatch")
    if claims_report.get("claim_count") != len(rows):
        raise ValueError("historical Claim Extraction count mismatch")
    if discovery.get("schema_version") != "1.1" or not isinstance(discovery.get("review_queue"), list):
        raise ValueError("historical discovery schema mismatch")
    generated = parse_utc(discovery.get("generated_at"))

    # Recompute the full (not top-100 truncated) deterministic triage metadata
    # with the same scoring implementation. This is a routing score, not truth.
    triage = build_queue(discovery, claims_report, graph, now=generated, top=1000)
    priorities = {}
    for group in triage.get("queue", []):
        priority = {
            "score": group.get("score", 0),
            "score_factors": group.get("score_factors", {}),
            "risk_flags": group.get("risk_flags", []),
            "related_claim_ids": group.get("related_claim_ids", []),
            "duplicate_collapsed_count": group.get("duplicate_collapsed_count", 0),
            "ranking_method": triage.get("ranking_method"),
            "score_is_truth_confidence": False,
        }
        for claim_id in group.get("related_claim_ids", []):
            if claim_id in priorities:
                raise ValueError("historical triage repeats a Claim ID")
            priorities[claim_id] = priority

    recovered = {}
    for claim in rows:
        claim_id = claim.get("claim_id") if isinstance(claim, dict) else None
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError("historical Claim has an invalid ID")
        if claim_id in recovered:
            raise ValueError("historical artifact repeats a Claim ID")
        if claim.get("review_status") != "unverified_candidate":
            raise ValueError("historical Claim is not marked unverified")
        if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
            raise ValueError("historical Claim has no statement")
        if not isinstance(claim.get("source"), dict) or not claim["source"].get("url"):
            raise ValueError("historical Claim has no source provenance")
        if claim_id not in priorities:
            raise ValueError("historical Claim is missing from recomputed triage")
        recovered[claim_id] = {
            "claim_snapshot": copy.deepcopy(claim),
            "priority": copy.deepcopy(priorities[claim_id]),
            "generated_at": iso(generated),
            "artifact_id": manifest["artifact_id"],
            "run_id": manifest["run_id"],
        }
    if set(priorities) != set(recovered):
        raise ValueError("recomputed triage does not cover every historical Claim")
    return recovered, generated


def hydrate_state(state, *, repo, token, fetcher=download_artifact,
                  artifact_manifest=ARTIFACT_MANIFEST, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    if not isinstance(state, dict) or state.get("schema_version") != "1.0" or not isinstance(state.get("items"), dict):
        raise ValueError("review cache must use schema 1.0 with an items object")

    items = state["items"]
    missing_payload = [
        claim_id for claim_id, row in items.items()
        if not isinstance(row, dict) or not isinstance(row.get("claim_snapshot"), dict)
    ]
    if not items:
        return {
            "schema_version": "1.0", "status": "skipped_empty_state",
            "generated_at": iso(now), "state_item_count": 0,
            "recovered_claim_count": 0, "hydrated_item_count": 0,
            "missing_claim_ids": [], "artifact_ids": [],
            "note": "No persisted review backlog exists yet; normal discovery will retain payloads for new Claims.",
        }, False
    if not missing_payload:
        return {
            "schema_version": "1.0", "status": "skipped_already_hydrated",
            "generated_at": iso(now), "state_item_count": len(items),
            "recovered_claim_count": 0, "hydrated_item_count": 0,
            "missing_claim_ids": [], "artifact_ids": [],
            "note": "Every persisted review item already has a Claim payload.",
        }, False

    recovered = {}
    first_seen = {}
    last_seen = {}
    artifact_ids = []
    download_errors = []
    for manifest in artifact_manifest:
        artifact_id = manifest["artifact_id"]
        try:
            payload = fetcher(repo, artifact_id, token)
        except (OSError, TimeoutError, ConnectionError, urllib.error.URLError) as error:
            download_errors.append({
                "artifact_id": artifact_id,
                "error_type": type(error).__name__,
            })
            continue
        rows, generated = extract_claims(payload, manifest)
        artifact_ids.append(artifact_id)
        stamp = iso(generated)
        for claim_id, record in rows.items():
            first_seen[claim_id] = min(first_seen.get(claim_id, stamp), stamp)
            last_seen[claim_id] = max(last_seen.get(claim_id, stamp), stamp)
            previous = recovered.get(claim_id)
            if previous:
                old_claim = previous["claim_snapshot"]
                new_claim = record["claim_snapshot"]
                if (old_claim.get("candidate_id") != new_claim.get("candidate_id")
                        or old_claim.get("statement") != new_claim.get("statement")):
                    raise ValueError("same historical Claim ID has conflicting identity/content")
                if record["generated_at"] >= previous["generated_at"]:
                    recovered[claim_id] = record
            else:
                recovered[claim_id] = record

    if not recovered:
        return {
            "schema_version": "1.0", "status": "unavailable",
            "generated_at": iso(now), "state_item_count": len(items),
            "recovered_claim_count": 0, "hydrated_item_count": 0,
            "missing_claim_ids": sorted(missing_payload),
            "artifact_ids": artifact_ids, "download_errors": download_errors,
            "note": "No historical artifacts could be downloaded; cache was left unchanged.",
        }, False

    hydrated = 0
    added = 0
    for claim_id, record in recovered.items():
        row = items.get(claim_id)
        if row is None:
            row = {
                "first_seen_at": first_seen[claim_id],
                "last_seen_at": last_seen[claim_id],
            }
            items[claim_id] = row
            added += 1
        if not isinstance(row, dict):
            raise ValueError("review cache contains an invalid Claim record")
        snapshot = row.get("claim_snapshot")
        origin = row.get("snapshot_origin") or {}
        if not isinstance(snapshot, dict) or record["generated_at"] >= origin.get("generated_at", ""):
            row["claim_snapshot"] = record["claim_snapshot"]
            row["priority"] = record["priority"]
            row["snapshot_origin"] = {
                "artifact_id": record["artifact_id"],
                "run_id": record["run_id"],
                "generated_at": record["generated_at"],
            }
            row["score"] = record["priority"]["score"]
            row["score_factors"] = record["priority"]["score_factors"]
            row["risk_flags"] = record["priority"]["risk_flags"]
            row["source_url"] = record["claim_snapshot"]["source"]["url"]
            row["topic"] = record["claim_snapshot"].get("topic")
            hydrated += 1

    missing_after = sorted(
        claim_id for claim_id, row in items.items()
        if not isinstance(row, dict) or not isinstance(row.get("claim_snapshot"), dict)
    )
    status = "complete" if not missing_after and not download_errors else "partial"
    report = {
        "schema_version": "1.0", "status": status, "generated_at": iso(now),
        "state_item_count": len(items), "recovered_claim_count": len(recovered),
        "hydrated_item_count": hydrated, "new_state_items_added": added,
        "claim_payloads_available": len(items) - len(missing_after),
        "claim_payloads_missing": len(missing_after),
        "missing_claim_ids": missing_after,
        "artifact_ids": artifact_ids, "download_errors": download_errors,
        "priority_model": "transparent_rule_based_v1_recomputed_from_original_run",
        "priority_is_truth_confidence": False,
        "decisions_changed": 0,
        "note": "Recovered Claim text and source excerpts remain unverified candidates; no review decision or factual status was changed.",
    }
    state["backlog_hydration"] = {
        "status": status, "hydrated_at": iso(now),
        "artifact_ids": artifact_ids, "claim_payloads_available": report["claim_payloads_available"],
        "claim_payloads_missing": report["claim_payloads_missing"],
    }
    return report, True


def markdown_report(report):
    lines = [
        "# Historical Claim Backlog Recovery", "",
        f"- Status: **{report['status']}**",
        f"- Cache items: {report['state_item_count']}",
        f"- Recovered unique Claims: {report['recovered_claim_count']}",
        f"- Newly hydrated cache items: {report['hydrated_item_count']}",
        f"- Claim payloads available: {report.get('claim_payloads_available', 0)}",
        f"- Claim payloads still missing: {report.get('claim_payloads_missing', 0)}",
        f"- Artifacts read: {len(report.get('artifact_ids', []))}",
        f"- Human decisions changed: {report.get('decisions_changed', 0)}",
        "",
        "All restored records remain unverified Claim candidates. Priority scores route review work; they are not truth-confidence scores.",
    ]
    if report.get("download_errors"):
        lines.extend(["", "## Artifacts unavailable", ""])
        lines.extend(f"- Artifact {row['artifact_id']}: {row['error_type']}" for row in report["download_errors"])
    if report.get("missing_claim_ids"):
        lines.extend(["", "## Claim IDs without recovered payloads", ""])
        lines.extend(f"- {claim_id}" for claim_id in report["missing_claim_ids"][:50])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "basicmi/AI-Chip"))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    try:
        state = json.loads(args.state.read_text(encoding="utf-8")) if args.state.exists() else {
            "schema_version": "1.0", "items": {}
        }
        report, changed = hydrate_state(state, repo=args.repo, token=args.token)
        if changed:
            args.state.parent.mkdir(parents=True, exist_ok=True)
            args.state.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown_report(report), encoding="utf-8")
        print(f"Review backlog hydration: {report['status']}; {report.get('claim_payloads_available', 0)} payloads available.")
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
