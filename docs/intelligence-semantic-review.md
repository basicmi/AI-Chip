# Human semantic-support review protocol

This workflow asks whether an original source supports the wording of an
extracted Claim. It does **not** establish whether the source's assertion is
factually true, reproducible, independently verified, or suitable for a
product or benchmark database.

## Outputs

Each weekly Discovery run emits
`ai-chip-intelligence-semantic-review-template.json` alongside the bounded
25-Claim review packet. Every Claim has two blank, independent reviewer
slots. Each human reviewer must open the original source and provide a
distinct reviewer identity, a label, rationale of at least 30 characters,
and a boolean indicating whether the source was checked.

Supported labels:

- `supported_by_source`: the original source actually asserts the extracted
  Claim, at its stated scope. This is **not** truth verification.
- `contradicted_by_source`: original text contradicts the extracted Claim.
- `insufficient_context`: the excerpt/source does not support a
  confident semantic determination, including missing configuration.
- `source_unavailable`: original source could not be accessed (the
  source_checked field must be false).

Use the generator on the same-run review batch:

    python3 scripts/review_intelligence_semantic_support.py \
      --batch ai-chip-intelligence-claim-review-batch.json \
      --output semantic-review.json

After two different humans have completed their independent judgments, run:

    python3 scripts/review_intelligence_semantic_support.py \
      --batch semantic-review.json \
      --evaluate \
      --output semantic-review-evaluation.json \
      --markdown semantic-review-evaluation.md

The evaluation reports coverage of double review, raw exact-label agreement,
pending Claims, label distributions, and conflicting judgments that require
manual adjudication. A single reviewer or incomplete rows never count as an
agreed result. No kappa, quality score, model-calibration metric, precision
estimate or reviewer-accuracy claim is inferred from small nonrandom batches.

There is deliberately **no** automatic import into
`data/intelligence-review-decisions.json`. The semantic review packet is an
additional diagnostic, not a formal review decision. Subsequent evidence
proposals must still pass the explicit human approval and Evidence-to-PR
gates. Agreement does not establish independence of evidence or factual truth.
