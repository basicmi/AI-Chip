# Intelligence Operations Dashboard (PR #101)

The static page \`/intelligence-operations/\` presents **operational** data
from one or more completed weekly GitHub Actions runs. It makes no API calls,
uses local browser file inputs, and cannot change review states or hardware
databases.

## Workflow outputs

After a successful PR #100 end-to-end audit, the weekly workflow creates
\`ai-chip-intelligence-operations.json\` in the existing
\`ai-chip-intelligence-discovery\` artifact. The snapshot contains source
availability per source, number of new/updated leads, claims, unresolved
backlog, oldest first-seen wait, warnings and a presence check on the
restored change-detection and backlog cache files.

File-present signals mean a cache file was available at the start of the
run. They do **not** prove it is fresh, complete or continuously retained.
An audit-failed run does not produce a successful snapshot; examine its
Actions logs and partial health artifact separately.

## Compare runs

1. Download the artifact from each desired weekly run.
2. Select their \`ai-chip-intelligence-operations.json\` files together.
3. Review the sorted per-run table; select a run for individual source
   diagnostics, source outages and restored cache-file indicators.

The page accepts up to 52 files, each up to 2 MiB. Duplicate run
timestamps, invalid summaries, unknown status values or mismatched source
counts fail closed. Every displayed trend point must originate in an
explicitly selected completed-run snapshot. If a failed run, expired
artifact or omitted run is missing, the visualization **does not**
impute it. A single snapshot is not a historical trend.

## Boundaries

- Operational source availability measures endpoint/parse success, not
  correctness of underlying technical claims.
- No autonomous ongoing monitoring, scheduled notification or GitHub
  repository write is introduced by the dashboard.
- Source/feed health is not independent corroboration.
- Local files stay in the browser session.
- The separate Evidence Review Workbench and gated human Evidence-to-PR
  approval flow are unchanged.

CI verifies the snapshot generator and uses Playwright with synthetic
multi-run JSON inputs to check table ordering, cache indicators, source
diagnostics and malicious/mismatched input rejection.
