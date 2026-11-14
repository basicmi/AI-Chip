# Intelligence Review Queue Triage (PR #97)

The weekly discovery workflow now produces ai-chip-intelligence-triage.json
and ai-chip-intelligence-triage.md after the Claim and Evidence Graph stages.

## Deterministic prioritization

Scores are **review urgency, not truth or evidence confidence**. Documented
signals include source recency, new/changed source status, high-impact
hardware topics, numeric specifications, contextual risk and provenance.
Possible conflicts from an explicitly reviewer-scoped Evidence Graph get
extra review priority, never automatic verification.

Only identical normalized claim statements are collapsed into a review group.
Each group retains the IDs of **all** original Claim records. Collapsing exact
text does not imply independent corroboration; separate sources may syndicate
one vendor announcement. Different statements, products, precisions, units
or configurations are never automatically equated as facts.

Old or undated original-source records receive explicit flags. Age is based
on the source publication date, not how recently a scanner checked it.
No assumption is made about how long a claim has been awaiting a reviewer
because per-claim review state is not yet persisted between runs.

## Running locally

    python3 scripts/triage_intelligence_claims.py \
      --discovery /tmp/ai-chip-intelligence-discovery.json \
      --claims /tmp/ai-chip-intelligence-claims.json \
      --graph /tmp/ai-chip-intelligence-evidence-graph.json \
      --output /tmp/ai-chip-intelligence-triage.json \
      --markdown /tmp/ai-chip-intelligence-triage.md

The JSON artifact is designed to be consumed by a future Workbench priority
view. The existing Claim JSON and Evidence Graph remain unchanged. Human
approval and reviewed Evidence-to-PR manifests are still separate gates.

## Safety

Inputs must agree on Claim count and Claim ID membership. Every Claim must
remain unverified, and the Evidence Graph must claim zero verified results.
Review urgency is not a recommendation to overwrite production data.
