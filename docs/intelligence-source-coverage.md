# Source Coverage Audit (PR #103)

The Intelligence Engine's source registry currently contains 24 active sources:
15 GitHub release repositories, 8 vendor RSS/Atom feeds, and 1 arXiv API
query. The weekly pipeline (schedule or manual workflow_dispatch) now
creates two additional artifacts:

- \`ai-chip-intelligence-source-coverage.json\`
- \`ai-chip-intelligence-source-coverage.md\`

The audit runs **after actual network-backed Discovery** and before Claim
Extraction, and its Markdown output is included in the GitHub Actions
Step Summary. It does not itself make extra HTTP requests.

## What is checked

- The active source IDs and types match the Discovery source result table
  exactly, including failed or empty feeds;
- Source counts, observation counts and per-source item totals reconcile;
- Each source records the latest/earliest *observed* publication time,
  the age of the latest observed publication, and missing/invalid dates;
- A zero-item **successful** source is distinguished from an unavailable
  or parser-broken source;
- A source that returned exactly the configured GitHub Releases (20) or
  arXiv search result cap is flagged as **possibly truncated**. The API
  might contain additional recent results: saturation does not prove loss;
- Repeated **same normalized URL across different sources** is flagged
  as potential syndication, not as independent corroboration;
- Source failure categories, consecutive failed runs and critical health
  tiers from PR #102 are reflected in coverage concerns.

The same HTTP URL is never treated as evidence supporting an independent
claim solely because multiple RSS feeds or GitHub projects cite it.
The report intentionally only displays source IDs and counts for duplicate
URLs so potentially token-bearing URLs do not leak into Actions artifacts.

## Limits

This is a scan-level metadata audit, **not a proof of exhaustiveness**.
In particular, there is no pagination beyond the current first GitHub
release page or the arXiv max_results window. Items that were never
returned cannot be enumerated from local metadata alone. A source returning
few results may have a healthy feed, a tight query, a stale feed, or
publication filtering; the audit cannot determine which without further
source-specific investigation.

A missing publication date is flagged only when one of the retained
observations has no parsable date. The current collectors usually filter
those entries earlier, so the absence of this flag does not prove every
upstream article had a valid date. No RSS/Atom feed is considered dead
based on one empty scan.

## How to reproduce

After downloading a successful weekly Discovery artifact:

    python3 scripts/audit_intelligence_source_coverage.py \
      --registry data/intelligence-sources.json \
      --discovery /path/to/ai-chip-intelligence-discovery.json \
      --output /tmp/ai-chip-intelligence-source-coverage.json \
      --markdown /tmp/ai-chip-intelligence-source-coverage.md

Unit tests run against synthetic Discovery structures. **No real online
health claims** are established by those unit tests. To exercise the actual
24 endpoints, manually dispatch the existing "Weekly AI Chip intelligence
discovery" GitHub Actions workflow on master, then inspect the uploaded
source-coverage JSON and Markdown. The pipeline still does not modify
formal company, product, model-support or benchmark registries.

## Operational next steps

The first real report should guide decisions about source replacements,
adjusting filters, pagination, date handling, feed-type detection and
publisher coverage. Changes to the curated registry should require their
own review rather than being made automatically from one transient outage.
