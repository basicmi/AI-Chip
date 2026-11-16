# AI Chip Intelligence Discovery and Claim Extraction

The intelligence pipeline is a read-only discovery and evidence triage layer.
It does not write to formal company, product, model-support or benchmark registries.


## GitHub API authentication

The scheduled discovery workflow passes its short-lived, read-only
`GITHUB_TOKEN` to the release collector. The collector attaches a Bearer token
and the documented GitHub API version only when the destination host is
exactly `api.github.com` over HTTPS. It never forwards this credential to
RSS/Atom publishers, arXiv, or arbitrary URLs.

This avoids exhausting the unauthenticated GitHub REST API quota during a
multi-project release scan. A GitHub 403 is classified as rate limiting only
when the response explicitly reports `X-RateLimit-Remaining: 0`; other 403
responses remain ordinary client/permission errors. No token value is written
to reports or logs. Local runs remain supported without a token, subject to
the unauthenticated API quota.

## Claim extraction

scripts/extract_intelligence_claims.py consumes the discovery report review
queue and emits structured claim candidates. Version 2 is a deterministic,
relevance-gated first stage based on token-boundary topic signals and
numeric-unit patterns. It is not LLM semantic understanding; it is testable
in CI and has no model/API credentials.

Version 2 introduced deterministic relevance labels and fair source/candidate
limits. Version 3 tightened broad single-word query and sentence relevance
signals after the first live run. The first live run after PR #112 then exposed
two remaining classes of error: generic GPU/HPC papers entering through CUDA
or broad GPU terms, and useful AI runtime papers being missed when their
titles used terms such as MoE serving or on-device RL rather than the current
anchor vocabulary.

Version 4 makes these changes:

1. Specific AI hardware and AI-system signals remain direct anchors, including
   NPU/TPU/ASIC/FPGA, HBM, chip design, KV cache, speculative decoding,
   distributed training, MoE inference/serving, NCCL and named LLM serving
   runtimes.
2. Generic CUDA/ROCm/Triton/compiler/kernel or GPU mentions are contextual.
   They need a specific AI workload plus an execution/system concern; generic
   CUDA linear algebra, neural-network verification solvers and general GPU
   numerical-bug studies are not treated as AI-chip contributions by default.
3. Generic "world model" is no longer sufficient for relevance. Robot,
   robotics, VLA, physical-AI and world-action-model signals remain adjacent
   workload topics, while weather and research-field world models are not
   pulled in solely by the phrase "world model".
4. Candidate relevance is still only context. A sentence must carry a
   hardware/system signal or a measured system result; metric-bearing
   sentences may be retained when the candidate itself is already a direct
   AI-system contribution.
5. An offline, human-curated golden set now evaluates three-way candidate
   relevance (direct, adjacent, out of scope) and sentence-level Claim
   extraction. The evaluator reports precision, recall, F1, a confusion
   matrix, false positives/negatives, quote fidelity and repeated sentence
   rows. It runs in CI and in the weekly discovery workflow.

The golden set is a calibration seed, not a statistically representative
production sample. Its recall is only recall against judged examples; it
cannot measure papers that the upstream arXiv query never retrieved.
Deterministic extraction confidence remains low, and all Claims remain
unverified until human review.

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


## Offline quality evaluation

The weekly discovery workflow runs
`scripts/evaluate_intelligence_quality.py` against
`data/intelligence-quality-golden.json`. It emits a JSON and Markdown report
as part of the same 30-day Actions artifact. The golden set was curated from
real candidates observed in the first post-PR-112 run on 2026-11-16.

Candidate relevance is scored as a three-class problem (direct AI compute,
adjacent AI systems, out of scope), with a separate binary relevant-vs-out-of-
scope precision/recall view. Sentence extraction is evaluated against
human-curated sentence fragments, with repeated numeric rows collapsed to
sentence granularity and reported separately. Quote fidelity is checked
against the supplied abstract excerpt.

The seed set contains 25 candidates (12 direct, 4 adjacent, 9 out of scope)
and 16 sentence-extraction cases. It is intentionally small and curated to
cover positive cases and known false-positive patterns. Do not interpret its
scores as unbiased production estimates. It cannot measure recall over papers
that arXiv search did not return, nor can it establish claim truth.

## Evidence-to-PR workflow

Claim Candidates JSON and Markdown summaries are retained as GitHub Actions
artifacts for 30 days. They are an investigation queue, not an automated data
patch. Reviewers verify the original source, preserve units/scope, seek
independent corroboration, and only then map accepted claims to formal fields.

No company/product/model-support/benchmark registry is modified automatically.
No PR is auto-created or auto-merged by scheduled discovery.

## Run locally

    python3 -m unittest discover -s tests -p "test_intelligence_claims.py"
    python3 -m unittest discover -s tests -p "test_intelligence_quality.py"
    python3 scripts/evaluate_intelligence_quality.py --golden data/intelligence-quality-golden.json
    python3 scripts/extract_intelligence_claims.py --input /tmp/ai-chip-intelligence.json --output /tmp/ai-chip-claims.json --summary-path /tmp/ai-chip-claims.md

## Cross-source evidence graph (PR #91)

See [Evidence Graph and Cross-source Review](evidence-graph-review.md) for exact
text deduplication and optional reviewer-scoped numeric comparisons.

Default weekly runs create an unverified Claim -> Source graph and a Markdown
review report. No automatic independent corroboration or production database
update is performed.
