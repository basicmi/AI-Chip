# Cross-source lineage review

This is a conservative, **human-only** review of possible shared evidence
origins. Different websites reporting the same text are not multiple
independent measurements.

## Weekly worksheet

The weekly Discovery workflow emits
`ai-chip-intelligence-source-lineage-review-template.json`.
It selects up to 25 exact normalized statement duplicate clusters that span
two or more source documents. Selection is deterministic: largest
multi-document clusters first, then cluster ID. Same-document duplicates
are excluded; paraphrases may be missed. Claims without matching exact text
do not enter this queue.

The worksheet includes original source URLs, publisher metadata and
declared independence fields for context only. Each source is assigned
blank human-review fields:

- `origin_key`: human-assigned underlying primary material, such as
  a specific vendor press release or a particular test campaign. Reprints
  of the same material must share the same key.
- `relationship`: `original_material`, `syndicated_reprint`,
  `secondary_analysis`, `independent_measurement_claim` or `unknown`.
- `reviewer`, `rationale` (at least 30 characters) and `source_checked`.

A reviewer must open and inspect the original source before assigning
a definitive relationship; `unknown` may be used if the source cannot
be examined. The reviewer must not infer experimental independence merely
from different domains, companies or author names.

## Commands

Generate a blank, bounded worksheet:

    python3 scripts/review_intelligence_source_lineage.py \
      --graph ai-chip-intelligence-evidence-graph.json \
      --max-clusters 25 \
      --output ai-chip-intelligence-source-lineage-review-template.json

After humans have filled the worksheet, score the completeness of annotations:

    python3 scripts/review_intelligence_source_lineage.py \
      --graph annotated-lineage.json \
      --evaluate \
      --output lineage-evaluation.json \
      --markdown lineage-evaluation.md

The evaluator reports fully reviewed clusters, pending clusters, the
number sharing a single reviewer-assigned origin key, the number with
multiple keys, and relationship-label counts. Distinct keys remain
**reviewer assertions**, not independent replication or corroboration.
The evaluator never writes back to the Claim ledger, source catalog,
Evidence Graph, or formal company/model/benchmark records.

## Limitations

No semantic matching, model judgment or hidden heuristics are used to group
sources. Exact shared wording offers one narrow lead for syndication; it does
not establish shared origin. Human labels can be wrong. An independent
measurement *claim* is not a reproducible measurement. All original
Claim candidates remain unverified until separate governance checks.
