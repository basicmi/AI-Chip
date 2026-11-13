# AI Chip Intelligence Discovery

The intelligence pipeline is a read-only discovery and evidence triage layer.
It does not write to formal company, product, model-support or benchmark
registries.

## Source classes

- GitHub Releases: curated official software and benchmark repositories.
- RSS/Atom: official vendor announcements and technical blogs (NVIDIA, AMD,
  Google and AWS in the initial expansion).
- arXiv API: recent preprints in computer architecture, distributed systems,
  machine learning, programming languages and related systems areas.
- Hugging Face: the existing model catalog audit is reused for model repository
  metadata and publisher candidates.

Each source is explicit in data/intelligence-sources.json. The registry
validator enforces source-kind-specific fields and HTTPS endpoints.

## Evidence normalization

Every item receives a stable candidate ID, content fingerprint, source
identity, publication timestamp, canonical link, excerpt, topic tags and
review actions. New/updated/unchanged classification is persisted in the
GitHub Actions cache. Feed items without dates or usable links are skipped.
One unavailable feed does not suppress other sources.

arXiv results are explicitly marked as preprints; an arXiv record is not
evidence of peer review. Vendor feed content is vendor-reported, not an
independent measurement.

## Evidence-to-PR workflow

The generated Evidence Review Packet is an investigation queue, not an
automated data patch. Reviewers should:
1. Open and verify the original source.
2. Extract atomic claims and preserve units, scope and lifecycle status.
3. Seek independent corroboration for performance, availability and
   compatibility claims.
4. Map approved claims to existing registry fields and schemas.
5. Create a narrow data PR with source links and tests.

No company/product/model-support/benchmark registry is modified automatically.
No PR is auto-created or auto-merged by the scheduled discovery workflow.

## Run locally

    python3 scripts/validate_intelligence_sources.py
    python3 -m unittest discover -s tests -p "test_intelligence_feeds.py"
    python3 scripts/run_intelligence_discovery.py \
      --output /tmp/ai-chip-intelligence.json \
      --summary-path /tmp/ai-chip-intelligence-review.md
