# Intelligence source runtime telemetry (PR #106)

## Why

The 24-source Intelligence pipeline already reports success/failure,
consecutive failure streaks, pagination and item counts. It did not record
how long each real request took, how many retries were consumed, or how
much response data was transferred. As a result, a source could be slow or
intermittently rate-limited while still appearing simply "observed".

## What is added

Every active source now receives URL-free request diagnostics:

- \`request_count\`: actual fetch attempts, including retries and pages;
- \`failed_request_count\`: transport/HTTP fetch calls that raised;
- \`response_bytes\`: payload bytes returned by successful fetch calls;
- \`total_elapsed_ms\`, \`average_request_ms\`, \`max_request_ms\`;
- \`last_http_error_status\` and sanitized \`last_request_failure_category\`.

The diagnostics are attached to both successful and unavailable source
records. The existing Source Coverage Audit validates internal consistency,
aggregates totals and renders a per-source table in its Markdown artifact.
Sources with any request taking at least five seconds are counted for review;
this is an observation threshold, not a source outage verdict.

Metrics include GitHub Releases and arXiv pages, RSS/Atom fetches, and
transient retries. They intentionally exclude full URLs, query strings,
credentials, response bodies, and raw exception messages.

## Validation

Offline tests use injected fetchers and a deterministic clock to cover:
successful payload accounting, elapsed-time calculation, 503 retry then
success, 404 failure classification, parser failure after a successful HTTP
fetch, coverage aggregation, malformed counters, and backward compatibility
with older Discovery artifacts that lack telemetry.

The standard validation workflow runs this suite alongside the existing
source recovery, pagination, source coverage, data integrity and browser
smoke tests.

## Live validation boundary

The weekly workflow already supports \`workflow_dispatch\` and uploads
\`ai-chip-intelligence-discovery\` plus the source-coverage artifacts. No
actual Discovery run appeared in the latest 100 repository Actions records
when checked on 2026-11-16, so this PR does **not** claim any current live
endpoint health or latency measurements. After merge, manually run
**Weekly AI Chip intelligence discovery** from Actions (default branch,
45-day lookback) and inspect the new per-source request table in the
uploaded coverage report and Step Summary.

A low response count does not prove a source is broken; a 5-second request
does not prove it is unhealthy; a successful HTTP fetch does not establish
the truth of its content. The report remains operational telemetry only.
