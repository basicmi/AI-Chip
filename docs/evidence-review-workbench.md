# Evidence Review Workbench (PR #95)

The Evidence Review Workbench is a static Jekyll page at
/evidence-review/. It is deliberately **local-only**: browser File inputs
load the JSON files downloaded from a GitHub Actions artifact. It makes no
network request for those artifacts and does not store information on a server
or persist it in browser local storage.

## How to use

1. Visit the [Weekly AI Chip intelligence discovery Actions workflow]
   (https://github.com/basicmi/AI-Chip/actions/workflows/model-catalog-audit.yml).
2. Download one run's ai-chip-intelligence-discovery artifact.
3. Open /evidence-review/ and choose its ai-chip-intelligence-claims.json file.
4. Optionally choose the same run's ai-chip-intelligence-evidence-graph.json.
5. Search by source, topic, statement and exact-text duplicates. When a
   reviewer has supplied explicit comparison annotations before graph
   generation, possible conflicts appear separately.

The page validates schema version, claim counts, unique claim IDs, source
URLs, unverified statuses and graph membership. Invalid files fail closed.
It displays up to 250 matching cards at once; filters/search still process
all loaded claims (max 10,000; each input is limited to 12 MiB).

## Truth and review boundary

All cards remain unverified. The page does not approve any claim, record
independent corroboration, create review manifests, change the production
database or auto-open PRs. Duplicate text is not independent verification;
numerical disagreements are review leads, not established contradictions.
Loading a JSON file with a synthetic record does not make that record true.

For actual evidence attachments, follow docs/evidence-to-pr.md and the
gated reviewer-controlled process. PR #95 does not modify that workflow.

## Tests

Browser smoke tests load synthetic, unverified Claim and Graph files via
Playwright setInputFiles; they verify filtering, provenance, duplicate and
conflict counters, invalid status rejection and state reset without any
external API or background workflow.
