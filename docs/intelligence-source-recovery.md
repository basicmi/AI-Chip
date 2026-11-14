# Source Reliability and Failure Recovery (PR #102)

This revision strengthens the weekly AI Chip Intelligence discovery pipeline
without changing its formal data or human approval rules.

## Failure categories

Each active source produces one run result with \`status=observed\` or
\`status=unavailable\`. The latter now includes a categorized failure:

- \`http_rate_limit\` — HTTP 429
- \`http_server_error\` — HTTP 5xx
- \`http_client_error\` — other HTTP 4xx
- \`timeout\` — bounded transport timeout
- \`network\` — DNS / connection / URL network failure
- \`parse_error\` — invalid XML/JSON decode
- \`invalid_payload\` — structurally invalid provider response
- \`source_error\` — other unexpected source-handling error

The category and exception *type*, not the exception message, enter the
report. This avoids accidentally recording credentials, query tokens or
other private URL details in a public GitHub Actions artifact.

## Bounded retry

Each source is attempted at most three times with short backoffs (0.2s and
0.4s) for HTTP 429/500/502/503/504, transport timeouts and transient URL or
connection errors. HTTP 4xx excluding 429, invalid payloads and malformed XML
are not retried. Each HTTP request uses a bounded 12-second timeout and an
8 MiB response cap.

Healthy successful sources returning *zero recent items* remain observed,
not unavailable. One failed source never discards valid observations from
other sources. A complete outage continues to fail the independent audit
and prevents both cache checkpoints from being committed.

## Persisted per-source state

\`source_health\` is stored alongside the existing discovery change-detection
cache and committed only after the full PR #100 pipeline audit succeeds.

- One failure: transient
- Two consecutive failed runs: warning
- Three or more: critical
- Next successful run: recovered (failure streak resets)
- Successful run with zero recent items: healthy, not broken

Streaks count failed *runs*, not retry attempts. The previous last-success
timestamp is retained during outages. The cache may be evicted, which resets
streak tracking. No automatic alerts, subscriptions or source replacement
are introduced.

The operational snapshot from PR #101 includes these source diagnostics
when present. Older snapshots without these optional fields remain usable.

## Tests and scope

\`tests/test_intelligence_source_recovery.py\` covers backoff, transient vs
non-retryable failures, recovery after three failed runs, healthy empty feeds,
partial outages and error-message sanitization.

CI uses synthetic offline feeds. This PR does not claim that all curated RSS,
arXiv and GitHub Release endpoints were successfully live-tested, or that
an accepted evidence attachment is a verified technical claim.
