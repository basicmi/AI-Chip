# Intelligence Operations Dashboard (PR #101, extended by PR #107)

The static page \`/intelligence-operations/\` presents **operational** data
from one or more completed weekly GitHub Actions runs. It makes no API calls,
uses local browser file inputs, and cannot change review states or hardware
databases.

## Workflow outputs

After a successful end-to-end audit, the weekly workflow creates
\`ai-chip-intelligence-operations.json\` in the
\`ai-chip-intelligence-discovery\` artifact. Snapshot schema 1.1 retains
per-source request diagnostics and adds aggregate request totals:

- number of sources with request telemetry;
- total fetch attempts, including pagination and retries;
- failed fetch attempts;
- successful response payload bytes;
- sources whose maximum individual request took at least five seconds.

Per-source diagnostics include request count, failed count, average and
maximum latency, and successful payload bytes. The allowlisted snapshot
does not copy source URLs, query strings, credentials, response bodies or
raw exception messages.

Older operational snapshot schema 1.0 files remain supported by the page.
For those files, request metrics display as unavailable rather than zero.
A schema 1.1 snapshot can also contain individual sources without telemetry
when it is built from a legacy discovery artifact; the telemetry-source
count makes that coverage explicit.

## Compare runs

1. Download the artifact from each desired weekly run.
2. Select their \`ai-chip-intelligence-operations.json\` files together.
3. Review the sorted per-run table for changes in source availability,
   request volume, failures and slow sources.
4. Select a run for per-source request latency, payload size, outages and
   restored cache-file indicators.

The page accepts up to 52 files, each up to 2 MiB. Duplicate run
timestamps, invalid summaries, unknown status values, inconsistent request
metrics or mismatched source counts fail closed. Every displayed trend point
must originate in an explicitly selected completed-run snapshot. If a failed
run, expired artifact or omitted run is missing, the visualization does not
impute it. A single snapshot is not a historical trend.

## Metric interpretation

- Request counts include retries and pagination calls.
- Failed requests are transport/HTTP fetch attempts that raised; a request
  that failed and then succeeded on retry contributes to both counts.
- Response bytes count successful payloads only.
- Average and maximum latency are per individual request, not end-to-end
  source processing time.
- The five-second marker is a review threshold, not an outage or quality
  verdict.
- Missing telemetry is distinct from a measured zero-request source.

## Boundaries

- Operational source availability measures endpoint/parse success, not
  correctness of underlying technical claims.
- No autonomous ongoing monitoring, scheduled notification or GitHub
  repository write is introduced by the dashboard.
- Source/feed health is not independent corroboration.
- Local files stay in the browser session.
- The separate Evidence Review Workbench and gated human Evidence-to-PR
  approval flow are unchanged.

CI verifies the snapshot generator and uses synthetic multi-run JSON inputs
to check table ordering, cache indicators, source diagnostics, request
aggregation and malformed/mismatched input rejection.
