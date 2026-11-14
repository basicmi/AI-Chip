# Evidence Graph and Cross-source Review (PR #91)

This module is a read-only review aid layered on top of Claim Extraction (PR #90).

## Default behavior: exact-text clustering only

    python3 scripts/build_intelligence_evidence_graph.py \
      --input /tmp/ai-chip-claims.json \
      --output /tmp/ai-chip-evidence-graph.json \
      --summary-path /tmp/ai-chip-evidence-review.md

Identical normalized statements create candidate duplicate clusters and
Claim -> Source Document graph edges. Text duplicates are never considered
independent corroboration. No product name, version, subject identity,
workload, precision, sparsity or metric scope is inferred automatically.

Every candidate stays unverified. The output is a review graph, not a product
database, scientific conclusion or independent measurement.

## Optional reviewer-supplied comparison annotations

Cross-source comparison requires all of the following explicit keys. These
are assigned by a reviewer who has inspected the original source and
measurement conditions, not derived from approximate title similarity:

    {
      "schema_version": "1.0",
      "claims": {
        "claim-REAL_ID_1": {
          "subject_key": "nvidia:b200-sxm",
          "metric_key": "hbm-capacity",
          "context_key": "hgx-b200:per-chip:specification",
          "comparison_kind": "specification",
          "evidence_origin_key": "nvidia-hgx-b200-datasheet"
        },
        "claim-REAL_ID_2": {
          "subject_key": "nvidia:b200-sxm",
          "metric_key": "hbm-capacity",
          "context_key": "hgx-b200:per-chip:specification",
          "comparison_kind": "specification",
          "evidence_origin_key": "same-nvidia-datasheet-if-reprinted"
        }
      }
    }

Pass --annotations /path/to/reviewed-annotations.json to enable scoped
comparisons. Subject, metric, context and comparison kind must match exactly.

- The evidence_origin_key is the underlying source family: articles that
  reproduce the same press release must share one origin key.
- Different origin keys mean the reviewer distinguished origins; they do NOT
  prove editorial independence.
- Identical numerical values and units yield only
  numerical_agreement_candidate.
- Different numbers in explicitly matched specification contexts yield
  possible_specification_conflict, requiring manual review.
- Different measurement values are not contradictory specifications;
  differences may be due to batch size, precision, framework, driver,
  concurrency, hardware revision or methodology.
- Different units or qualifiers never trigger automatic numerical conflicts.
- Qualitative claims such as "supports FP8" cannot be verified by string
  agreement. They remain non-numeric, unverified comparison candidates.

## Data outputs and limitations

The JSON graph contains typed nodes, typed edges, duplicate clusters,
explicitly scoped comparisons, warnings and zero independently verified claims.
The associated Markdown report lists potential conflicts and review steps.

The weekly workflow generates the graph without reviewer annotations. That
means the scheduled default only clusters exact normalized statements and
records Claim -> Source links; it cannot automatically claim cross-source
technical verification. Annotation-driven checks may run locally for reviewed
candidate files.

The workflow never edits published model, accelerator, company or benchmark
registries and never opens or merges data update PRs.
