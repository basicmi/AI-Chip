# AI Chip Intelligence Discovery and Claim Extraction

The intelligence pipeline is a read-only discovery and evidence triage layer.
It does not write to formal company, product, model-support or benchmark registries.

## Claim extraction

scripts/extract_intelligence_claims.py consumes the discovery report review
queue and emits structured claim candidates. Version 2 is a deterministic,
relevance-gated first stage based on token-boundary topic signals and
numeric-unit patterns. It is not LLM semantic understanding; it is testable
in CI and has no model/API credentials.

Version 2 introduced deterministic relevance labels and fair source/candidate
limits. The first post-merge live run exposed remaining false positives from
generic single-word signals, so Version 3 tightens both candidate and
sentence-level relevance.

Version 3 makes these changes:

1. Generic words such as "compiler", "kernel", "inference", "serving",
   "parallelism" and "LLM" are no longer sufficient relevance anchors.
   A GPU mention requires a paired AI-workload and system/performance context;
   generic compiler/kernel work requires an explicit AI workload and execution
   context. Specific accelerator, memory, interconnect, ISA, RTL/EDA and
   low-level GPU software terms remain direct anchors.
2. Candidate-level relevance is context only. A Claim sentence must carry its
   own specific hardware or AI-system signal. A narrow exception allows a
   sentence that reports a GPU resource/metric when the candidate itself is
   already classified as adjacent AI-system work.
3. Robotics/agent candidates no longer cause every sentence in their abstract
   to become a Claim; unrelated methodology sentences are filtered.
4. The arXiv query removes broad single-word OR terms and retains explicit
   accelerator, GPU software, memory, inference/serving, distributed-training,
   agent-runtime and architecture phrases.
5. Regression tests use real false-positive patterns observed in the
   2026-11-16 live run, alongside positive TPU/NPU/GPU kernel cases.

Claims still carry separate `relevance.class`, `topic`, `claim_type`,
`assertion_class` and `evidence_class` labels. Human-review triage keeps
direct compute/system evidence distinct from adjacent workload evidence.
The score prioritizes review effort, not factual confidence.

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
