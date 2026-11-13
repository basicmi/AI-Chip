# AI Chip Intelligence Discovery

This is a read-only discovery and change-detection layer. It is not a source
of truth and does not write to formal company, product, model-support or
benchmark registries.

## Sources

data/intelligence-sources.json is the curated registry of official project
repositories. Each active GitHub Releases source is polled over a bounded
lookback window. The existing Hugging Face model catalog audit is reused to
check curated model repositories and discover unreviewed publisher candidates.

## Change detection

- Release candidates have stable IDs derived from repository and tag.
- Content fingerprints cover tag, title, notes, publication date, URL and
  prerelease status. A changed fingerprint becomes an updated candidate.
- Model repository candidates use Hugging Face repository SHA and modified
  metadata.
- The workflow restores a state file from GitHub Actions cache to classify
  new/updated/unchanged items across weekly runs.
- Cache eviction or a first run can cause candidates to appear new again.

## Review policy

Every candidate is an investigation lead, not an approved fact. Release notes
and model repository metadata do not prove product specifications, model
quality, hardware compatibility or benchmark performance. The pipeline does
not auto-edit production registries or auto-merge PRs.

Future phases can add official vendor announcement feeds, standards and
research sources, evidence extraction, confidence scoring and a PR generator
for narrowly scoped data changes with citations.

## Run locally

    python3 scripts/validate_intelligence_sources.py
    python3 scripts/run_intelligence_discovery.py --output /tmp/ai-chip-intelligence.json
