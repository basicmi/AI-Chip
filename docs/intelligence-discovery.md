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

## arXiv query sharding and resilience

The arXiv discovery source is split into four independently monitored query
shards: distributed AI systems/inference (`cs.DC`), hardware/accelerator
architecture (`cs.AR`, `eess.SY`), kernels/compilers/ML systems
(`cs.LG`, `cs.PL`), and agentic/physical AI (`cs.AI`, `cs.RO`,
`cs.CV`). Each shard requests 50 records per page, scans at most two pages
per run, and retries transient failures at most twice. A failed shard no
longer suppresses results from the other research areas.

Requests are spaced by at least three seconds between pages and between
configured arXiv shards. Each shard has independent source-health history and
pagination/truncation diagnostics. The bounded 100-record per-shard scan is
an operational compromise, not a completeness guarantee; any full second page
is explicitly flagged as possible lookback-window truncation. Human review
and the existing relevance-quality evaluation remain unchanged.

## Pagination configuration contract

Source Coverage Audit validates pagination diagnostics against the active
source registry. GitHub Release collection currently uses its fixed
three-page bound; arXiv sources use each source's configured `max_pages`
(defaulting to three for older registries). The audit rejects diagnostics
that disagree with the configured bound or report more fetched pages than
allowed. This keeps collector and audit behavior aligned when query shards
use different operational limits.

## Known-item retrieval evaluation

`data/intelligence-retrieval-golden.json` is a small **positive-only**
calibration set of 16 previously reviewed, relevant arXiv papers (12 direct
AI-compute, four adjacent AI-system/physical-AI). Publication calendar dates
are explicit. The offline evaluator runs after source-coverage audit:

```bash
python3 scripts/evaluate_intelligence_retrieval.py \
  --golden data/intelligence-retrieval-golden.json \
  --discovery /tmp/ai-chip-intelligence-discovery.json \
  --registry data/intelligence-sources.json \
  --output /tmp/ai-chip-retrieval-eval.json \
  --markdown /tmp/ai-chip-retrieval-eval.md
```

It reports Recall@25/50/100 where K is the **observed candidate depth
within each source**, not an arbitrary global ranking. Paper IDs match
independently of arXiv version; duplicates across shards count once.
Only papers within the discovery lookback period contribute to the denominator.
Unreachable arXiv shards make the evaluation non-scorable, rather than
misleadingly treating every missing paper as an algorithmic failure.

**Interpretation:** This is a known-item seed-set hit rate, not unbiased
production Recall@K or corpus-wide recall. The dataset was sampled from
papers previously discovered and manually selected, so selection bias is
inherent. Every missing item is a diagnosis candidate, not proof of a bad
query: the cause could be term/category coverage, indexing latency, request
timing or a capped search window. Full-page truncation warnings remain
visible next to the metric. CI checks evaluator correctness but does not
require an arbitrary minimum hit rate.

## Retrieval miss diagnosis (PR #118)

The weekly workflow now follows known-item Recall@K with a deterministic
diagnosis report. It parses the active arXiv shard categories and literal
`all:` query phrases, then compares them with the manually curated title and
abstract excerpt of each missed seed. A category-aware lexical proxy classifies
misses as a likely category-filter gap, query-vocabulary gap, configured-phrase
match not returned, or unknown-category lexical gap.

The report includes category provenance, source shards covering each known
category, phrase matches and evidence-grounded candidate terms. It is not an
arXiv API replay: phrase matching does not prove the API's exact query
semantics, and a phrase match followed by a miss can still reflect indexing,
ranking or page-cap truncation. Category metadata from secondary indexes is
explicitly provisional; uncaptured metadata stays unknown.

Run locally:

```bash
python3 scripts/diagnose_intelligence_retrieval.py \
  --golden data/intelligence-retrieval-golden.json \
  --evaluation /tmp/ai-chip-retrieval-eval.json \
  --registry data/intelligence-sources.json \
  --output /tmp/ai-chip-retrieval-diagnosis.json \
  --markdown /tmp/ai-chip-retrieval-diagnosis.md
```

Candidate terms are review proposals only. The diagnostic does not change
source queries automatically. Broadening OR clauses without measuring result
quality can increase page-cap competition and reduce precision.

## Isolated targeted retrieval experiment (PR #119)

The weekly workflow now runs four bounded, one-page arXiv query experiments
after the baseline Recall@K and miss diagnosis:

1. GPU communication and interconnect.
2. LLM inference energy and KV-cache.
3. Agentic GPU capacity and short-lived jobs.
4. Physical-AI runtime and world-action models.

Each query is limited to 50 results and is kept outside the production source
registry. The runner waits three seconds between experiment queries, uses the
existing Atom parser and bounded retry policy, and applies the same discovery
lookback window. The baseline discovery and recall evaluation must be
scorable before any experimental requests are made.

The report measures incremental unique papers, overlap with the baseline,
cross-group duplicates, known-seed hits and page-cap saturation. It also
includes an explicitly unvalidated rule-based relevance screen for manual
triage. **It does not report measured precision**: that requires independent
human labels for the returned candidates. Experimental results do not enter
the production review queue or change active discovery queries.

Run locally:

```bash
python3 scripts/run_intelligence_retrieval_experiment.py \
  --config data/intelligence-retrieval-experiments.json \
  --discovery /tmp/ai-chip-intelligence-discovery.json \
  --baseline /tmp/ai-chip-intelligence-retrieval-evaluation.json \
  --output /tmp/ai-chip-retrieval-experiment.json \
  --markdown /tmp/ai-chip-retrieval-experiment.md
```


## Human relevance review for targeted retrieval (PR #121)

The targeted-query experiment now retains the complete bounded result set
(up to 50 unique papers per query group), including title, arXiv URL, abstract
excerpt, categories, deterministic screening label and observed position.
The position is newest-first after local date filtering; it is **not** a
relevance rank.

The weekly workflow creates
`ai-chip-intelligence-retrieval-review-template.json` as an Actions artifact.
It selects a deterministic simple-random sample without replacement from
each successfully observed query group (12 papers per group by default).
A paper selected in multiple groups appears once in the template and records
all groups for which it was sampled. The selection seed is derived from the
experiment and group IDs, so the same run is reproducible.

Reviewers should fill `adjudication.label` with one of:
`direct_ai_compute`, `adjacent_ai_systems`, `out_of_scope`, or
`uncertain`, and record a reviewer identifier. The deterministic
`predicted_relevance` field is context only and must not be copied into the
adjudicated label without checking the title and abstract. Direct and adjacent
both count as relevant for retrieval precision; uncertain labels remain
unresolved and are never silently counted as negative.

After annotation, evaluate the edited template:

```bash
python3 scripts/evaluate_intelligence_retrieval_review.py \
  --input reviewed-retrieval-template.json \
  --output retrieval-review-evaluation.json \
  --markdown retrieval-review-evaluation.md
```

Precision is reported separately for each query group. It is only reported
when every sampled paper for that group has a resolved label and reviewer.
For a simple-random sample smaller than the returned population, the report
shows a Wilson 95% interval; when the entire returned set was sampled, the
measured proportion is exact for that bounded set. Partially reviewed groups
show descriptive progress only, not a precision estimate. These results
describe one bounded run and do not establish corpus-wide retrieval quality.
