# AI Chip Intelligence Discovery and Claim Extraction

The intelligence pipeline is a read-only discovery and evidence triage layer.
It does not write to formal company, product, model-support or benchmark registries.

## Claim extraction

scripts/extract_intelligence_claims.py consumes the discovery report review
queue and emits structured claim candidates. Version 2 is a deterministic,
relevance-gated first stage based on token-boundary topic signals and
numeric-unit patterns. It is not LLM semantic understanding; it is testable
in CI and has no model/API credentials.

Version 2 makes four changes:

1. A candidate must have a hardware, AI-compute, systems, compiler/runtime,
   model-architecture, agent-runtime or physical-AI relevance anchor. A
   generic mention of "agent", "inference", "performance", "benchmark" or
   a number is not sufficient by itself.
2. A title is context for relevance, not an asserted Claim. Claims are
   extracted from the source excerpt only. Sentences without their own
   technical topic or system anchor are filtered.
3. Claims carry separate `relevance.class`, `topic`, `claim_type`,
   `assertion_class` and `evidence_class` labels. This distinguishes
   direct compute/system evidence from adjacent research, and separates
   roadmap intent, speculation, vendor marketing language, technical
   specifications, research-result candidates and capability statements.
4. Per-candidate and global limits are explicit. If the queue is capped,
   selection is round-robin across sources and candidates rather than allowing
   the first high-volume source to consume the entire budget.
5. Human-review triage carries the relevance, assertion and evidence labels
   forward. Direct compute/system evidence receives a modest review-priority
   boost over adjacent research; roadmap, speculation, vendor-marketing and
   preprint labels add caution flags. These scores prioritize review effort,
   not factual confidence.

Each record preserves the original candidate and source URL, a quote from the
source excerpt, claim type/topic, numeric value and unit when recognized,
explicit scope markers, qualifiers, relevance and evidence labels, extraction
method and human-review gates. Deterministic extraction confidence remains
low; the new labels are routing hints, not truth or quality scores.

The extractor can miss claims, split sentences imperfectly or produce false
positives. It does not resolve product identity, infer chip-vs-system scope
when the source is silent, decide truth, or verify performance/compatibility.
"Supports FP8" remains a candidate claim, not a verified support path. An arXiv
record remains a preprint unless peer review is separately established.

## Evidence-to-PR workflow

Claim Candidates JSON and Markdown summaries are retained as GitHub Actions
artifacts for 30 days. They are an investigation queue, not an automated data
patch. Reviewers verify the original source, preserve units/scope, seek
independent corroboration, and only then map accepted claims to formal fields.

No company/product/model-support/benchmark registry is modified automatically.
No PR is auto-created or auto-merged by scheduled discovery.

## Run locally

    python3 -m unittest discover -s tests -p "test_intelligence_claims.py"
    python3 scripts/extract_intelligence_claims.py --input /tmp/ai-chip-intelligence.json --output /tmp/ai-chip-claims.json --summary-path /tmp/ai-chip-claims.md

## Cross-source evidence graph (PR #91)

See [Evidence Graph and Cross-source Review](evidence-graph-review.md) for exact
text deduplication and optional reviewer-scoped numeric comparisons.

Default weekly runs create an unverified Claim -> Source graph and a Markdown
review report. No automatic independent corroboration or production database
update is performed.
