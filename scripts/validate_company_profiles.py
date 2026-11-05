#!/usr/bin/env python3
"""Validate company profiles, source references, evidence and claim relationships."""
import json
import re
import sys
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "company-profiles.json"
DIRECTORY = ROOT / "directory.md"
WORKLOADS = ROOT / "data" / "workloads.json"
BENCHMARKS = ROOT / "data" / "benchmark-projects.json"
COMPATIBILITY = ROOT / "data" / "compatibility.json"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CATEGORIES = {
    "IC Vendors", "Tech Giants & HPC Vendors", "Traditional IP Vendors",
    "Startups", "China AI Accelerator Vendors",
}
REFERENCE_TYPES = {
    "unknown", "company_primary", "vendor_primary", "official_project",
    "research_paper", "independent_media", "repository",
    "government_or_regulatory", "other",
}
EVIDENCE_TYPES = REFERENCE_TYPES - {"unknown"}
CLAIM_STATUSES = {
    "vendor_reported", "source_confirmed", "independently_verified",
    "disputed", "superseded",
}
METRIC_TYPES = {"specification", "theoretical_peak", "vendor_measured", "independent_measured", "production_observed", "derived"}
PRECISIONS = {"FP64", "FP32", "TF32", "BF16", "FP16", "FP8", "FP6", "FP4", "MXFP8", "MXFP6", "MXFP4", "NVFP4", "INT8", "INT4", "INT2", "mixed", "not_applicable", "unspecified"}
SPARSITY_MODES = {"dense", "structured_sparse", "unstructured_sparse", "not_applicable", "unspecified"}
MEASUREMENT_SCOPES = {"die", "chip", "package", "module", "board", "server", "rack", "pod", "cluster", "system"}
METRIC_OPERATIONS = {"matrix", "vector", "scalar", "memory", "interconnect", "communication", "power", "area", "system_configuration", "other"}
DIRECTIONS = {"unidirectional", "bidirectional", "aggregate", "not_applicable", "unspecified"}
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
    if not isinstance(value, str):
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except (TypeError, ValueError):
        return False

def require(obj, fields, where):
    check(isinstance(obj, dict), f"{where}: expected object")
    if isinstance(obj, dict):
        for field in fields:
            check(field in obj, f"{where}: missing {field}")

def main():
    try:
        db = json.loads(DATA.read_text(encoding="utf-8"))
        directory = unescape(DIRECTORY.read_text(encoding="utf-8"))
        workload_db = json.loads(WORKLOADS.read_text(encoding="utf-8"))
        benchmark_db = json.loads(BENCHMARKS.read_text(encoding="utf-8"))
        compatibility_db = json.loads(COMPATIBILITY.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"FAIL: cannot read company profile registry or directory: {exc}", file=sys.stderr)
        return 2

    require(db, ["schema_version", "database_version", "registry_reviewed_at",
                 "scope", "freshness_policy", "comparison_policy",
                 "profile_status_definitions", "companies"], "root")
    if not isinstance(db, dict):
        return 2
    check(db.get("schema_version") == "1.2", "root: schema_version must be 1.2")
    check(valid_date(db.get("registry_reviewed_at")), "root: invalid registry_reviewed_at")
    policy = db.get("freshness_policy", {})
    require(policy, ["fresh_within_days", "stale_after_days",
                     "missing_checked_at_means", "notes"], "freshness_policy")
    if isinstance(policy, dict):
        check(isinstance(policy.get("fresh_within_days"), int) and policy["fresh_within_days"] > 0,
              "freshness_policy: fresh_within_days must be positive")
        check(isinstance(policy.get("stale_after_days"), int) and
              policy["stale_after_days"] > policy.get("fresh_within_days", 0),
              "freshness_policy: stale_after_days must exceed fresh_within_days")
        check(policy.get("missing_checked_at_means") == "unreviewed",
              "freshness_policy: missing checked_at must mean unreviewed")

    comparison = db.get("comparison_policy", {})
    comparison_fields = ["precision_must_match", "sparsity_must_match",
                         "measurement_scope_must_match", "metric_type_must_match",
                         "system_and_chip_metrics_must_not_be_mixed",
                         "source_units_must_be_preserved"]
    require(comparison, comparison_fields + ["notes"], "comparison_policy")
    if isinstance(comparison, dict):
        for field in comparison_fields:
            check(comparison.get(field) is True,
                  f"comparison_policy: {field} must remain true")
        check(isinstance(comparison.get("notes"), str) and bool(comparison["notes"].strip()),
              "comparison_policy: notes must be non-empty")

    workload_ids = {item.get("id") for item in workload_db.get("workloads", []) if isinstance(item, dict)}
    benchmark_ids = {item.get("id") for item in benchmark_db.get("projects", []) if isinstance(item, dict)}
    compatibility_platform_ids = {item.get("id") for item in compatibility_db.get("platforms", []) if isinstance(item, dict)}

    companies = db.get("companies", [])
    check(isinstance(companies, list) and len(companies) > 0,
          "companies must be a non-empty array")
    directory_titles = re.findall(
        r'<div align="center" class="vendor-title"><h3>(.*?)</h3></div>',
        directory, flags=re.S
    )
    check(len(directory_titles) == len(companies),
          f"directory/profile count mismatch: {len(directory_titles)} titles vs {len(companies)} profiles")

    company_ids, anchors = set(), set()
    total_references = total_evidence = total_claims = 0
    unreviewed_profiles = 0

    for index, company in enumerate(companies):
        where = f"companies[{index}]"
        require(company, ["id", "display_name", "category", "directory_anchor",
                          "logo_url", "summary", "profile_status", "last_reviewed",
                          "products", "claims", "evidence", "references"], where)
        if not isinstance(company, dict):
            continue

        cid = company.get("id")
        anchor = company.get("directory_anchor")
        check(isinstance(cid, str) and bool(ID_RE.fullmatch(cid or "")), f"{where}: invalid id")
        check(cid not in company_ids, f"{where}: duplicate company id {cid}")
        company_ids.add(cid)
        check(isinstance(anchor, str) and bool(anchor), f"{where}: missing directory_anchor")
        check(anchor not in anchors, f"{where}: duplicate directory_anchor {anchor}")
        anchors.add(anchor)
        check(anchor is not None and re.search(
            r'<a\s+(?:name|id)="' + re.escape(str(anchor)) + r'"',
            directory
        ) is not None, f"{where}: directory anchor {anchor!r} does not exist")
        check(unescape(str(company.get("display_name", ""))) in directory,
              f"{where}: display_name is not present in directory.md")
        check(company.get("category") in CATEGORIES, f"{where}: invalid category")
        check(valid_url(company.get("logo_url")), f"{where}: invalid logo_url")
        check(isinstance(company.get("summary"), str) and bool(company["summary"].strip()),
              f"{where}: summary must be non-empty")
        status = company.get("profile_status")
        check(status in {"not_reviewed", "partially_reviewed", "reviewed"},
              f"{where}: invalid profile_status")
        last_reviewed = company.get("last_reviewed")
        check(valid_date(last_reviewed, nullable=True), f"{where}: invalid last_reviewed")

        references = company.get("references", [])
        evidence = company.get("evidence", [])
        claims = company.get("claims", [])
        products = company.get("products", [])
        for field, value in (("references", references), ("evidence", evidence),
                             ("claims", claims), ("products", products)):
            check(isinstance(value, list), f"{where}: {field} must be an array")
        if not all(isinstance(value, list) for value in (references, evidence, claims, products)):
            continue

        total_references += len(references)
        total_evidence += len(evidence)
        total_claims += len(claims)
        if status == "not_reviewed":
            unreviewed_profiles += 1
            check(last_reviewed is None, f"{where}: not_reviewed profile must have null last_reviewed")
            check(not evidence and not claims,
                  f"{where}: not_reviewed profile cannot contain audited evidence or claims")
        else:
            check(valid_date(last_reviewed), f"{where}: reviewed profile needs last_reviewed")
            check(bool(claims), f"{where}: reviewed profile needs at least one structured claim")

        reference_ids, reference_urls = set(), set()
        for ri, reference in enumerate(references):
            rwhere = f"{where}.references[{ri}]"
            require(reference, ["id", "label", "url", "source_type", "review_status",
                                "published_at", "checked_at", "notes"], rwhere)
            if not isinstance(reference, dict):
                continue
            rid = reference.get("id")
            check(isinstance(rid, str) and bool(ID_RE.fullmatch(rid or "")), f"{rwhere}: invalid id")
            check(rid not in reference_ids, f"{rwhere}: duplicate reference id {rid}")
            reference_ids.add(rid)
            check(reference.get("url") not in reference_urls, f"{rwhere}: duplicate URL")
            reference_urls.add(reference.get("url"))
            check(valid_url(reference.get("url")), f"{rwhere}: invalid URL")
            check(bool(reference.get("label")), f"{rwhere}: label is required")
            check(reference.get("source_type") in REFERENCE_TYPES, f"{rwhere}: invalid source_type")
            review_status = reference.get("review_status")
            check(review_status in {"unreviewed", "reviewed", "excluded"},
                  f"{rwhere}: invalid review_status")
            check(valid_date(reference.get("published_at"), nullable=True),
                  f"{rwhere}: invalid published_at")
            check(valid_date(reference.get("checked_at"), nullable=True),
                  f"{rwhere}: invalid checked_at")
            if review_status == "unreviewed":
                check(reference.get("checked_at") is None,
                      f"{rwhere}: unreviewed reference cannot have checked_at")
            elif review_status == "reviewed":
                check(valid_date(reference.get("checked_at")),
                      f"{rwhere}: reviewed reference needs checked_at")

        evidence_ids, evidence_independence = set(), {}
        for ei, item in enumerate(evidence):
            ewhere = f"{where}.evidence[{ei}]"
            require(item, ["id", "title", "url", "publisher", "source_type",
                           "independence", "published_at", "checked_at",
                           "review_status", "notes"], ewhere)
            if not isinstance(item, dict):
                continue
            eid = item.get("id")
            check(isinstance(eid, str) and bool(ID_RE.fullmatch(eid or "")), f"{ewhere}: invalid id")
            check(eid not in evidence_ids, f"{ewhere}: duplicate evidence id {eid}")
            evidence_ids.add(eid)
            evidence_independence[eid] = item.get("independence")
            check(valid_url(item.get("url")), f"{ewhere}: invalid URL")
            check(bool(item.get("title")) and bool(item.get("publisher")),
                  f"{ewhere}: title and publisher are required")
            check(item.get("source_type") in EVIDENCE_TYPES, f"{ewhere}: invalid source_type")
            check(item.get("independence") in {"vendor", "project", "independent", "official"},
                  f"{ewhere}: invalid independence")
            check(valid_date(item.get("published_at"), nullable=True),
                  f"{ewhere}: invalid published_at")
            check(valid_date(item.get("checked_at")), f"{ewhere}: checked_at is required")
            check(item.get("review_status") in {"reviewed", "disputed"},
                  f"{ewhere}: invalid review_status")

        product_ids, product_claim_refs = set(), set()
        for pi, product in enumerate(products):
            pwhere = f"{where}.products[{pi}]"
            require(product, ["id", "name", "product_type", "availability", "claim_ids"], pwhere)
            if not isinstance(product, dict):
                continue
            pid = product.get("id")
            check(isinstance(pid, str) and bool(ID_RE.fullmatch(pid or "")), f"{pwhere}: invalid id")
            check(pid not in product_ids, f"{pwhere}: duplicate product id {pid}")
            product_ids.add(pid)
            check(bool(product.get("name")), f"{pwhere}: name is required")
            check(product.get("product_type") in {
                "gpu", "npu", "asic", "dpu", "ip", "system", "compute_in_memory", "other"
            }, f"{pwhere}: invalid product_type")
            check(product.get("availability") in {
                "announced", "sampling", "shipping", "production",
                "roadmap", "discontinued", "unknown"
            }, f"{pwhere}: invalid availability")
            for field in ("family", "form_factor", "package", "system_configuration"):
                if field in product:
                    check(isinstance(product[field], str) and bool(product[field].strip()),
                          f"{pwhere}: {field} must be a non-empty string")
            for field in ("announced_at", "first_available_at"):
                if field in product:
                    check(valid_date(product[field], nullable=True), f"{pwhere}: invalid {field}")
            if "die_count" in product:
                check(isinstance(product["die_count"], int) and product["die_count"] > 0,
                      f"{pwhere}: die_count must be a positive integer")
            related = product.get("related_product_ids", [])
            check(isinstance(related, list), f"{pwhere}: related_product_ids must be an array")
            compatibility_refs = product.get("compatibility_platform_ids", [])
            check(isinstance(compatibility_refs, list),
                  f"{pwhere}: compatibility_platform_ids must be an array")
            if isinstance(compatibility_refs, list):
                check(len(compatibility_refs) == len(set(compatibility_refs)),
                      f"{pwhere}: compatibility_platform_ids must be unique")
                for platform_id in compatibility_refs:
                    check(platform_id in compatibility_platform_ids,
                          f"{pwhere}: unknown compatibility platform {platform_id}")
            check(isinstance(product.get("claim_ids"), list), f"{pwhere}: claim_ids must be an array")
            product_claim_refs.update(product.get("claim_ids", []))

        claim_ids = set()
        claim_subjects = {}
        for ci, claim in enumerate(claims):
            cwhere = f"{where}.claims[{ci}]"
            require(claim, ["id", "subject_type", "subject_id", "topic", "statement",
                            "scope", "claim_status", "evidence_ids", "last_reviewed"], cwhere)
            if not isinstance(claim, dict):
                continue
            clid = claim.get("id")
            check(isinstance(clid, str) and bool(ID_RE.fullmatch(clid or "")), f"{cwhere}: invalid id")
            check(clid not in claim_ids, f"{cwhere}: duplicate claim id {clid}")
            claim_ids.add(clid)
            subject_type, subject_id = claim.get("subject_type"), claim.get("subject_id")
            check(subject_type in {"company", "product"}, f"{cwhere}: invalid subject_type")
            if subject_type == "company":
                check(subject_id == cid, f"{cwhere}: company claim subject_id must equal company id")
            elif subject_type == "product":
                check(subject_id in product_ids or any(p.get("id") == subject_id for p in products),
                      f"{cwhere}: unknown product subject_id {subject_id}")
            check(claim.get("topic") in {
                "product_identity", "architecture", "process_node", "compute",
                "memory_capacity", "memory_bandwidth", "interconnect", "power",
                "software_support", "availability", "deployment", "performance",
                "memory_type", "packaging", "die_count", "form_factor",
                "system_scale", "networking", "thermal", "other"
            }, f"{cwhere}: invalid topic")
            check(bool(claim.get("statement")) and bool(claim.get("scope")),
                  f"{cwhere}: statement and scope are required")
            check(claim.get("claim_status") in CLAIM_STATUSES, f"{cwhere}: invalid claim_status")
            check(valid_date(claim.get("last_reviewed")), f"{cwhere}: invalid last_reviewed")

            metric_context = claim.get("metric_context")
            numeric_value = isinstance(claim.get("value"), (int, float)) and not isinstance(claim.get("value"), bool)
            metric_topics = {"compute", "memory_capacity", "memory_bandwidth", "interconnect", "power"}
            if claim.get("topic") in metric_topics and numeric_value:
                check(isinstance(metric_context, dict),
                      f"{cwhere}: numeric {claim.get('topic')} claim needs metric_context")
            if metric_context is not None:
                require(metric_context, ["metric_type", "measurement_scope", "operation"],
                        f"{cwhere}.metric_context")
                if isinstance(metric_context, dict):
                    check(metric_context.get("metric_type") in METRIC_TYPES,
                          f"{cwhere}: invalid metric_context.metric_type")
                    check(metric_context.get("measurement_scope") in MEASUREMENT_SCOPES,
                          f"{cwhere}: invalid metric_context.measurement_scope")
                    check(metric_context.get("operation") in METRIC_OPERATIONS,
                          f"{cwhere}: invalid metric_context.operation")
                    if "precision" in metric_context:
                        check(metric_context["precision"] in PRECISIONS,
                              f"{cwhere}: invalid metric_context.precision")
                    if "sparsity" in metric_context:
                        check(metric_context["sparsity"] in SPARSITY_MODES,
                              f"{cwhere}: invalid metric_context.sparsity")
                    if "directionality" in metric_context:
                        check(metric_context["directionality"] in DIRECTIONS,
                              f"{cwhere}: invalid metric_context.directionality")
                    if claim.get("topic") == "compute" and numeric_value:
                        check(metric_context.get("precision") in PRECISIONS,
                              f"{cwhere}: compute claim needs a precision label")
                        check(metric_context.get("sparsity") in SPARSITY_MODES,
                              f"{cwhere}: compute claim needs a sparsity label")
                    expected_operations = {"memory_capacity": {"memory"}, "memory_bandwidth": {"memory"},
                                           "interconnect": {"interconnect", "communication"},
                                           "power": {"power"}}
                    if claim.get("topic") in expected_operations:
                        check(metric_context.get("operation") in expected_operations[claim.get("topic")],
                              f"{cwhere}: invalid metric_context.operation for {claim.get('topic')}")
                    if metric_context.get("workload_id") is not None:
                        check(metric_context["workload_id"] in workload_ids,
                              f"{cwhere}: unknown workload_id {metric_context['workload_id']}")
                    if metric_context.get("benchmark_project_id") is not None:
                        check(metric_context["benchmark_project_id"] in benchmark_ids,
                              f"{cwhere}: unknown benchmark_project_id {metric_context['benchmark_project_id']}")
            ev_ids = claim.get("evidence_ids", [])
            check(isinstance(ev_ids, list) and bool(ev_ids), f"{cwhere}: evidence_ids must be non-empty")
            for eid in ev_ids if isinstance(ev_ids, list) else []:
                check(eid in evidence_ids, f"{cwhere}: unknown evidence id {eid}")
            if claim.get("claim_status") == "independently_verified":
                check(any(evidence_independence.get(eid) == "independent" for eid in ev_ids),
                      f"{cwhere}: independently_verified claim needs independent evidence")
            claim_subjects[clid] = (subject_type, subject_id)

        for referenced_claim in product_claim_refs:
            check(referenced_claim in claim_ids,
                  f"{where}: product references unknown claim {referenced_claim}")
        for product in products:
            for claim_id in product.get("claim_ids", []):
                subject = claim_subjects.get(claim_id)
                check(subject == ("product", product.get("id")),
                      f"{where}: product claim {claim_id} has mismatched subject")
            for related_id in product.get("related_product_ids", []):
                check(related_id in product_ids and related_id != product.get("id"),
                      f"{where}: related_product_ids contains unknown or self reference {related_id}")

    if ERRORS:
        print(f"FAIL: {len(ERRORS)} validation error(s)")
        for error in ERRORS:
            print("- " + error)
        return 1

    print(
        f"PASS: {len(companies)} company profiles, {total_references} carried-over source links, "
        f"{total_claims} structured claims, {total_evidence} audited evidence records; "
        f"{unreviewed_profiles} profiles explicitly marked not reviewed."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
