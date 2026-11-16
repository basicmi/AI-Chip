#!/usr/bin/env python3
"""Deterministic, relevance-gated claim extraction; never verifies truth or writes registries."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

METHOD = "deterministic_rules_v2"

# Ordered from specific system domains to broader technical categories.
# Terms are matched on token boundaries; e.g. "eda" must not match inside a URL.
TOPICS = {
    "interconnect": (
        "nvlink", "infiniband", "ualink", "interconnect", "fabric",
        "all-reduce", "allreduce", "all-to-all", "alltoall", "collective communication",
    ),
    "memory_bandwidth": ("memory bandwidth", "hbm bandwidth", "bandwidth", "tb/s", "gb/s"),
    "memory_capacity": (
        "hbm", "dram", "sram", "kv cache", "memory capacity", "memory footprint",
        "memory utilization", "memory pool", "gpu memory", "memory allocation",
    ),
    "gpu_scheduling": (
        "gpu scheduling", "accelerator scheduling", "workload scheduling",
        "dynamic scheduling", "gpu utilization", "accelerator utilization",
        "gpu capacity", "idle gpu", "command scheduling", "gpu excursion",
        "resource scheduling", "workload placement", "job placement",
    ),
    "inference_serving": (
        "llm inference", "model inference", "inference serving", "inference engine",
        "serving engine", "on-device inference", "gpu inference", "continuous batching",
        "prefill", "decode", "speculative decoding", "time to first token",
        "time per output token", "inference pipeline", "inference environment",
        "batch makespan",
    ),
    "training_systems": (
        "distributed training", "large-scale training", "training throughput",
        "training efficiency", "training system", "training cluster", "pretraining",
        "post-training", "activation checkpointing", "optimizer state", "tensor parallel",
        "pipeline parallel", "expert parallel", "data parallel", "fsdp",
        "scaling law", "scaling laws", "lora fine-tuning", "lora finetuning",
    ),
    "agent_runtime": (
        "agent runtime", "agentic runtime", "agent orchestration", "tool execution",
        "tool calling", "gpu coding agent", "agent sandbox", "agent scheduling",
        "multi-agent system", "long-running agent", "agent workflow", "agent state",
        "coding agent", "llm agent workload",
    ),
    "compiler_kernel": (
        "compiler", "kernel", "cuda", "rocm", "triton", "cutlass",
        "flashattention", "flash attention", "tilelang", "tile lang", "ptx",
        "code generation", "operator fusion",
    ),
    "packaging": (
        "chiplet", "2.5d", "3d stack", "co-packaged", "packaging",
        "hybrid bonding", "interposer",
    ),
    "process_node": ("process node", "nm process", "nanometer", "pdk"),
    "power": (
        "power consumption", "power efficiency", "energy efficiency",
        "joules/token", "tdp", "watt", "power",
    ),
    "compute": (
        "gpu", "gpus", "accelerator", "accelerators", "tpu", "npu", "asic", "fpga",
        "graphics processor", "reconfigurable logic", "custom chip", "flops", "tops",
        "tensor core", "fp8", "fp4", "bf16", "int8", "int4", "compute throughput",
        "compute density", "matrix multiplication", "matmul", "systolic array", "compute",
    ),
    "performance": (
        "tokens/s", "tokens per second", "ttft", "tpot", "throughput", "latency",
        "speedup", "performance", "faster", "execution time",
    ),
    "software_support": (
        "supports", "support for", "compatibility", "backend", "runtime",
        "software stack", "framework integration", "api support",
    ),
    "availability": (
        "shipping", "available now", "sampling", "in production",
        "production availability", "volume production", "mass production",
        "generally available", "launches", "launched",
    ),
    "architecture": (
        "model architecture", "architecture", "expert parallel", "mixture of experts",
        "transformer", "attention", "mamba", "state space model", "looped transformer",
        "latent attention", "microarchitecture", "cpu architecture", "cpu core",
        "data-center cpu", "cache hierarchy", "memory subsystem", "sve", "avx", "sme",
    ),
    "rtl_eda": (
        "rtl", "verilog", "synthesis", "eda", "place and route", "timing closure",
        "critical path", "formal verification", "logic synthesis", "chip physical design",
        "vlsi physical design",
    ),
    "benchmark": (
        "mlperf", "inferencex", "gpu benchmark", "accelerator benchmark",
        "ai chip benchmark", "llm serving benchmark", "inference benchmark",
        "training benchmark", "spec cpu", "hardware counters", "cpi",
    ),
    "physical_ai": ("robotics", "embodied ai", "physical ai", "world model", "robot learning"),
}

DIRECT_ANCHORS = (
    "gpu", "gpus", "accelerator", "accelerators", "tpu", "npu", "asic", "fpga",
    "hbm", "dram", "sram", "nvlink", "infiniband", "ualink", "cuda", "rocm",
    "triton", "cutlass", "flashattention", "flash attention", "tilelang", "kernel",
    "compiler", "chiplet", "2.5d", "3d stack", "process node", "semiconductor",
    "silicon", "verilog", "rtl", "eda", "tensor core", "fp8", "fp4", "bf16",
    "int8", "int4", "kv cache", "prefill", "decode", "continuous batching",
    "speculative decoding", "ttft", "tpot", "tokens/s", "tokens per second",
    "inference engine", "inference serving", "serving engine", "distributed training",
    "tensor parallel", "pipeline parallel", "expert parallel", "all-reduce", "allreduce",
    "alltoall", "mixture of experts", "systolic array", "matrix multiplication", "matmul",
    "memory bandwidth", "memory capacity", "joules/token", "mlperf", "inferencex",
    "gpu scheduling", "accelerator scheduling", "gpu utilization", "accelerator utilization",
    "gpu capacity", "idle gpu", "command scheduling", "gpu excursion", "workload placement",
    "job placement", "graphics processor", "reconfigurable logic", "custom chip",
    "gpu inference", "on-device inference", "gpu memory", "lora fine-tuning",
    "lora finetuning", "llm agent workload", "inference environment", "batch makespan",
    "microarchitecture", "cpu architecture", "cpu core", "data-center cpu",
    "cache hierarchy", "memory subsystem", "hardware counters", "spec cpu",
)

ADJACENT_ANCHORS = (
    "model architecture", "llm architecture", "transformer", "attention",
    "mixture of experts", "mamba", "state space model", "looped transformer",
    "latent attention", "scaling law", "scaling laws", "agent runtime",
    "agentic runtime", "agent orchestration", "tool execution", "tool calling",
    "gpu coding agent", "agent sandbox", "agent scheduling", "multi-agent system",
    "long-running agent", "agent workflow", "agent state", "robotics", "embodied ai",
    "physical ai", "world model", "robot learning", "training efficiency",
    "training system", "training cluster", "large-scale training", "pretraining",
    "post-training",
)

SIGNALS = tuple(dict.fromkeys(
    term for terms in TOPICS.values() for term in terms
))
UNITS = (
    r"tokens?\s*/\s*s|tokens?\s+per\s+second|TB\s*/\s*s|GB\s*/\s*s|MB\s*/\s*s|"
    r"PFLOPS?|TFLOPS?|GFLOPS?|TOPS|TB|GB|MB|PB|kW|MW|W|nm|ms|us|µs|μs|"
    r"GPUs?|accelerators?|chips?|nodes?|[MB]\s+parameters?|%"
)
METRIC_RE = re.compile(
    r"(?<![\w.])(?P<value>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s*(?P<unit>" + UNITS + r")(?![\w])", re.I
)
SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")
SCOPES = [
    (re.compile(r"\bper\s+(?:GPU|accelerator|chip|die|package|board|server|rack|node|system)\b", re.I), "explicit_per_unit"),
    (re.compile(r"\b(?:rack|pod|cluster|system|server|board|module|package|chip|GPU)-level\b", re.I), "explicit_level"),
    (re.compile(r"\b(?:aggregate|total|combined)\b", re.I), "explicit_aggregate"),
]
QUALIFIERS = (
    "up to", "peak", "maximum", "dense", "sparse", "theoretical",
    "measured", "vendor-reported",
)
PERFORMANCE_TERMS = (
    "tokens/s", "tokens per second", "ttft", "tpot", "throughput", "latency",
    "speedup", "performance", "faster", "inference flops", "compute cost",
    "time to first token", "time per output token", "execution time",
)
AVAILABILITY_TERMS = (
    "shipping", "available now", "sampling", "in production",
    "production availability", "volume production", "mass production",
    "generally available", "launches", "launched",
)
SOFTWARE_TERMS = (
    "support", "supports", "compatible", "backend", "kernel", "compiler",
    "runtime", "cuda", "rocm", "triton", "cutlass", "flashattention", "tilelang",
)
ROADMAP_TERMS = (
    "roadmap", "plans to", "plan to", "will support", "will ship", "expected to",
    "scheduled for", "coming soon", "future release", "aims to", "intends to",
    "we plan to",
)
SPECULATION_TERMS = (
    "we hypothesize", "we speculate", "may enable", "might enable", "could enable",
    "potentially", "possibly", "we conjecture", "it is likely", "appears to",
)
MARKETING_TERMS = (
    "world's first", "world's fastest", "industry-leading", "best-in-class",
    "unprecedented", "revolutionary", "breakthrough", "state-of-the-art",
    "record-breaking",
)


def clean(value):
    value = unescape(str(value or ""))
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\x60+", "", value)
    return " ".join(value.split())


def stable_id(*parts):
    raw = "\x1f".join(str(x or "") for x in parts)
    return "claim-" + hashlib.sha256(raw.encode()).hexdigest()[:20]


def matching_terms(text, terms):
    """Match complete tokens/phrases so short terms cannot match inside URLs or words."""
    found = []
    for term in terms:
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        if re.search(pattern, text, re.I):
            found.append(term)
    return found


def topic_for(sentence):
    for topic, terms in TOPICS.items():
        if matching_terms(sentence, terms):
            return topic
    return "other"


def relevance_for(text):
    direct = matching_terms(text, DIRECT_ANCHORS)
    adjacent = matching_terms(text, ADJACENT_ANCHORS)
    if direct:
        return "direct_ai_compute", direct
    if adjacent:
        return "adjacent_ai_systems", adjacent
    return None, []


def scope_for(sentence):
    for pattern, label in SCOPES:
        match = pattern.search(sentence)
        if match:
            return {"status": label, "text": match.group(0)}
    return {"status": "not_explicitly_stated", "text": None}


def evidence_class_for(candidate):
    source_type = candidate.get("source_type")
    if candidate.get("candidate_type") == "research_preprint" or source_type == "research_paper":
        return "research_preprint"
    if source_type in ("vendor_primary", "company_primary"):
        return "vendor_primary_statement"
    if source_type == "official_project":
        return "project_maintainer_statement"
    if source_type == "repository":
        return "repository_metadata"
    if source_type == "independent_media":
        return "independent_reporting"
    return "unclassified_source"


def claim_type_for(sentence, candidate, metrics):
    if metrics and matching_terms(sentence, PERFORMANCE_TERMS):
        return "performance_result"
    if matching_terms(sentence, AVAILABILITY_TERMS):
        return "availability_or_lifecycle"
    if matching_terms(sentence, SOFTWARE_TERMS):
        return "software_or_capability"
    if metrics:
        return "quantitative_specification"
    if candidate.get("candidate_type") == "research_preprint":
        return "research_finding"
    return "qualitative_capability"


def assertion_class_for(sentence, claim_type, candidate):
    if matching_terms(sentence, ROADMAP_TERMS):
        return "roadmap_or_future_intent"
    if matching_terms(sentence, SPECULATION_TERMS):
        return "speculation_or_hypothesis"
    source_type = candidate.get("source_type")
    if source_type in ("vendor_primary", "company_primary") and matching_terms(sentence, MARKETING_TERMS):
        return "vendor_marketing_claim"
    if claim_type == "performance_result":
        if candidate.get("candidate_type") == "research_preprint" or source_type == "research_paper":
            return "research_result_candidate"
        if source_type in ("vendor_primary", "company_primary"):
            return "vendor_reported_result_candidate"
        return "performance_result_candidate"
    if claim_type == "quantitative_specification":
        return "technical_specification_candidate"
    if claim_type == "availability_or_lifecycle":
        return "availability_statement"
    if claim_type == "software_or_capability":
        return "capability_or_compatibility_statement"
    if candidate.get("candidate_type") == "research_preprint" or source_type == "research_paper":
        return "research_finding_candidate"
    if source_type in ("vendor_primary", "company_primary"):
        return "vendor_technical_statement"
    return "technical_statement_candidate"


def source_for(candidate):
    keys = (
        "candidate_id", "source_id", "source_name", "publisher", "source_type",
        "independence", "url", "published_at", "evidence_scope",
    )
    return {
        key: candidate.get(key, "unknown" if key in ("source_type", "independence", "evidence_scope") else None)
        for key in keys
    }


def extract_candidate_claims(candidate, diagnostics=None):
    diagnostics = diagnostics if diagnostics is not None else {}
    title = clean(candidate.get("title"))
    excerpt = clean(candidate.get("excerpt") or candidate.get("body_excerpt"))
    url = candidate.get("url")
    diagnostics.update({
        "candidate_relevance": "out_of_scope",
        "sentences_seen": 0,
        "sentences_filtered_out_of_scope": 0,
        "short_sentences": 0,
    })
    if not excerpt or not isinstance(url, str):
        diagnostics["skip_reason"] = "missing_excerpt_or_url"
        return []
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        diagnostics["skip_reason"] = "invalid_source_url"
        return []
    context_relevance, context_signals = relevance_for(" ".join(x for x in (title, excerpt) if x))
    if not context_relevance:
        diagnostics["skip_reason"] = "candidate_out_of_scope"
        return []
    diagnostics["candidate_relevance"] = context_relevance
    output = []
    seen = set()
    # The title is context only; it is not an asserted fact and must not become a Claim.
    for sentence in (x.strip(" \t\r-•") for x in SPLIT_RE.split(excerpt)):
        if len(sentence) < 18:
            diagnostics["short_sentences"] += 1
            continue
        diagnostics["sentences_seen"] += 1
        sentence_relevance, sentence_signals = relevance_for(sentence)
        topic = topic_for(sentence)
        # A paper must be relevant at candidate level, and a sentence must carry
        # its own system signal or a recognizable technical topic.
        if not sentence_relevance and topic == "other":
            diagnostics["sentences_filtered_out_of_scope"] += 1
            continue
        relevance_class = sentence_relevance or context_relevance
        relevance_signals = sentence_signals or context_signals
        metrics = list(METRIC_RE.finditer(sentence))
        claim_type = claim_type_for(sentence, candidate, metrics)
        assertion_class = assertion_class_for(sentence, claim_type, candidate)
        signals = matching_terms(sentence, SIGNALS)
        matches = metrics if metrics else [None]
        for match in matches:
            value = float(match.group("value").replace(",", "")) if match else None
            if value is not None and value.is_integer():
                value = int(value)
            unit = match.group("unit").strip() if match else None
            identity = (candidate.get("candidate_id"), sentence, value, unit)
            if identity in seen:
                continue
            seen.add(identity)
            output.append({
                "claim_id": stable_id(*identity),
                "candidate_id": candidate.get("candidate_id"),
                "claim_type": claim_type,
                "assertion_class": assertion_class,
                "topic": topic,
                "relevance": {
                    "class": relevance_class,
                    "matched_signals": relevance_signals[:12],
                },
                "statement": sentence[:1200],
                "value": value,
                "unit": unit,
                "scope": scope_for(sentence),
                "qualifiers": matching_terms(sentence.lower(), QUALIFIERS),
                "source": source_for(candidate),
                "evidence_class": evidence_class_for(candidate),
                "evidence_quote": sentence[:1200],
                "extraction": {
                    "method": METHOD,
                    "confidence": "low",
                    "matched_signals": signals[:12],
                    "requires_semantic_review": True,
                },
                "review_status": "unverified_candidate",
                "review_gates": [
                    "Verify that the quoted text actually asserts this claim.",
                    "Resolve company, product, architecture and generation; do not infer identity from publisher alone.",
                    "Confirm units, precision, sparsity, measurement scope and configuration before recording numeric values.",
                    "Classify the source as vendor, project-maintainer, research-preprint or independent reporting; do not infer independent measurement.",
                    "Check whether the statement is a measured result, specification, roadmap, capability claim or hypothesis.",
                    "Seek independent corroboration before treating performance, compatibility or availability as verified.",
                ],
            })
    return output


def validate_claim(claim):
    errors = []
    required = (
        "claim_id", "candidate_id", "claim_type", "assertion_class", "topic",
        "relevance", "statement", "scope", "source", "evidence_class",
        "evidence_quote", "extraction", "review_status", "review_gates",
    )
    for key in required:
        if key not in claim:
            errors.append("missing " + key)
    if not isinstance(claim.get("statement"), str) or not claim["statement"].strip():
        errors.append("statement must be nonempty")
    if claim.get("review_status") != "unverified_candidate":
        errors.append("claim must remain unverified")
    extraction = claim.get("extraction", {})
    if extraction.get("method") != METHOD:
        errors.append("unsupported extraction method")
    if extraction.get("confidence") != "low":
        errors.append("deterministic extraction confidence must remain low")
    if not isinstance(claim.get("review_gates"), list) or not claim["review_gates"]:
        errors.append("review_gates must be nonempty")
    relevance = claim.get("relevance", {})
    if relevance.get("class") not in ("direct_ai_compute", "adjacent_ai_systems"):
        errors.append("invalid relevance class")
    if not isinstance(relevance.get("matched_signals"), list) or not relevance["matched_signals"]:
        errors.append("relevance signals must be nonempty")
    if claim.get("evidence_class") not in (
        "research_preprint", "vendor_primary_statement", "project_maintainer_statement",
        "repository_metadata", "independent_reporting", "unclassified_source",
    ):
        errors.append("invalid evidence class")
    source = claim.get("source", {})
    url = source.get("url") if isinstance(source, dict) else None
    parsed = urlparse(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        errors.append("source URL must be HTTP(S)")
    value = claim.get("value")
    if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
        errors.append("value must be numeric or null")
    if value is not None and not isinstance(claim.get("unit"), str):
        errors.append("numeric value requires unit")
    return errors


def _round_robin_claims(source_groups, limit):
    """Select claims fairly across sources, then across candidates within each source."""
    source_ids = list(source_groups)
    candidate_positions = {source_id: 0 for source_id in source_ids}
    claim_positions = {
        source_id: [0] * len(groups)
        for source_id, groups in source_groups.items()
    }
    selected = []
    while len(selected) < limit:
        emitted = False
        for source_id in source_ids:
            groups = source_groups[source_id]
            if not groups:
                continue
            start = candidate_positions[source_id]
            for offset in range(len(groups)):
                index = (start + offset) % len(groups)
                if claim_positions[source_id][index] >= len(groups[index]):
                    continue
                selected.append(groups[index][claim_positions[source_id][index]])
                claim_positions[source_id][index] += 1
                candidate_positions[source_id] = (index + 1) % len(groups)
                emitted = True
                break
            if len(selected) >= limit:
                break
        if not emitted:
            break
    return selected


def extract_report(discovery, generated_at=None, max_claims=3000, max_claims_per_candidate=25):
    now = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    candidates = discovery.get("review_queue", [])
    source_groups = {}
    errors = []
    diagnostics_rows = []
    valid_before_limits = 0
    valid_after_candidate_limits = 0
    for candidate in candidates:
        diagnostics = {}
        extracted = extract_candidate_claims(candidate, diagnostics)
        valid = []
        for claim in extracted:
            problems = validate_claim(claim)
            if problems:
                errors.append({"candidate_id": candidate.get("candidate_id"), "errors": problems})
            else:
                valid.append(claim)
        valid_before_limits += len(valid)
        if len(valid) > max_claims_per_candidate:
            valid = valid[:max_claims_per_candidate]
        valid_after_candidate_limits += len(valid)
        if valid:
            source_id = candidate.get("source_id") or "unknown_source"
            source_groups.setdefault(source_id, []).append(valid)
        diagnostics_rows.append(diagnostics)

    claims = _round_robin_claims(source_groups, max_claims)
    topic_counts = Counter(claim["topic"] for claim in claims)
    type_counts = Counter(claim["claim_type"] for claim in claims)
    assertion_counts = Counter(claim["assertion_class"] for claim in claims)
    evidence_counts = Counter(claim["evidence_class"] for claim in claims)
    relevance_counts = Counter(claim["relevance"]["class"] for claim in claims)
    source_counts = Counter(claim["source"].get("source_id") or "unknown_source" for claim in claims)
    dropped = valid_before_limits - len(claims)
    return {
        "schema_version": "1.0",
        "generated_at": now,
        "input_candidate_count": len(candidates),
        "candidate_count_with_claims": sum(bool(group) for groups in source_groups.values() for group in groups),
        "candidate_count_without_claims": len(candidates) - sum(bool(group) for groups in source_groups.values() for group in groups),
        "out_of_scope_candidate_count": sum(row.get("skip_reason") == "candidate_out_of_scope" for row in diagnostics_rows),
        "filtered_sentence_count": sum(row.get("sentences_filtered_out_of_scope", 0) for row in diagnostics_rows),
        "claim_count": len(claims),
        "claim_count_before_limits": valid_before_limits,
        "claim_count_after_candidate_limits": valid_after_candidate_limits,
        "claims_dropped_by_limits": dropped,
        "truncated": dropped > 0,
        "max_claims": max_claims,
        "max_claims_per_candidate": max_claims_per_candidate,
        "topic_counts": dict(sorted(topic_counts.items())),
        "claim_type_counts": dict(sorted(type_counts.items())),
        "assertion_class_counts": dict(sorted(assertion_counts.items())),
        "evidence_class_counts": dict(sorted(evidence_counts.items())),
        "relevance_counts": dict(sorted(relevance_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "extraction_method": METHOD,
        "claims": claims,
        "errors": errors,
        "policy": (
            "Extracted Claims are unverified candidates. Relevance and assertion classes are deterministic "
            "routing labels, not semantic truth judgments. This extractor does not establish truth, infer "
            "product identity, verify compatibility, or modify production registries. Candidate and global "
            "limits are applied with source- and candidate-balanced selection."
        ),
    }


def markdown_summary(report):
    lines = [
        "# AI Chip Intelligence — Claim Extraction",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Input candidates: {report['input_candidate_count']}",
        f"- Candidates with Claims: {report['candidate_count_with_claims']}",
        f"- Out-of-scope candidates: {report['out_of_scope_candidate_count']}",
        f"- Sentences filtered as out of scope: {report['filtered_sentence_count']}",
        f"- Extracted Claim candidates: {report['claim_count']} / {report['claim_count_before_limits']} before limits",
        f"- Candidate/global limits dropped: {report['claims_dropped_by_limits']} (truncated: {str(report['truncated']).lower()})",
        f"- Extraction method: {report['extraction_method']}",
        "",
        "## Relevance distribution",
        "",
    ]
    for key, value in report["relevance_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Topic distribution", ""])
    for key, value in report["topic_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Assertion classification", ""])
    for key, value in report["assertion_class_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Evidence source class", ""])
    for key, value in report["evidence_class_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Claim candidates", ""])
    if not report["claims"]:
        lines.append("No claim candidates met the extraction rules.")
    for index, claim in enumerate(report["claims"][:100], 1):
        value = f" · {claim['value']} {claim['unit']}" if claim.get("value") is not None else ""
        lines.extend([
            f"### {index}. [{claim['topic']}] {claim['statement']}",
            f"- Type: {claim['claim_type']} · Assertion: {claim['assertion_class']}{value}",
            f"- Evidence class: {claim['evidence_class']} · Relevance: {claim['relevance']['class']}",
            f"- Source: {claim['source'].get('publisher') or claim['source'].get('source_name')} · {claim['source']['url']}",
            f"- Scope: {claim['scope']['status']} · {claim['scope'].get('text') or 'not stated'}",
            f"- Extraction: {claim['extraction']['method']} · confidence {claim['extraction']['confidence']} · human review required",
            "",
        ])
    lines.extend([
        "## Guardrails",
        "",
        "- These are candidate claims, not verified facts.",
        "- Relevance and assertion labels are deterministic routing hints, not semantic judgments.",
        "- A research result is not automatically an independently measured result; a vendor statement is not independent corroboration.",
        "- Product identity, units, measurement conditions, lifecycle and evidence independence require human review.",
        "- No production registry is modified and no compatibility or benchmark status is inferred.",
    ])
    if report["errors"]:
        lines.extend(["", "## Rejected extraction records", ""])
        lines.extend(
            f"- {item['candidate_id']}: {', '.join(item['errors'])}"
            for item in report["errors"]
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary-path", type=Path)
    parser.add_argument("--max-claims", type=int, default=3000)
    parser.add_argument("--max-claims-per-candidate", type=int, default=25)
    args = parser.parse_args()
    if not 1 <= args.max_claims <= 10000:
        parser.error("--max-claims must be between 1 and 10000")
    if not 1 <= args.max_claims_per_candidate <= 100:
        parser.error("--max-claims-per-candidate must be between 1 and 100")
    try:
        discovery = json.loads(args.input.read_text(encoding="utf-8"))
        report = extract_report(
            discovery,
            max_claims=args.max_claims,
            max_claims_per_candidate=args.max_claims_per_candidate,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.summary_path:
            args.summary_path.parent.mkdir(parents=True, exist_ok=True)
            args.summary_path.write_text(markdown_summary(report), encoding="utf-8")
        print(
            f"PASS: {report['input_candidate_count']} candidates; "
            f"{report['claim_count']} in-scope unverified Claims; "
            f"{report['out_of_scope_candidate_count']} candidates filtered."
        )
    except (OSError, ValueError, TypeError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
