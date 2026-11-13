# AI Chip Intelligence Discovery and Claim Extraction

The intelligence pipeline is a read-only discovery and evidence triage layer.
It does not write to formal company, product, model-support or benchmark registries.

## Claim extraction

scripts/extract_intelligence_claims.py consumes the discovery report review
queue and emits structured claim candidates. Version 1 is a deterministic,
conservative baseline based on technical topic signals and numeric-unit
patterns. It is not LLM semantic understanding; it is testable in CI and has
no model/API credentials.

Each record preserves the original candidate and source URL, a quote from the
source excerpt, claim type/topic, numeric value and unit when recognized,
explicit scope markers, qualifiers, extraction method and human-review gates.

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
