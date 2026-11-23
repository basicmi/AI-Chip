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


## Evidence provenance and quote traceability audit (PR #129)

The weekly discovery workflow now runs a separate read-only audit after Claim
extraction and evidence-graph construction:

    python3 scripts/audit_intelligence_evidence_quality.py \
      --discovery /tmp/ai-chip-intelligence-discovery.json \
      --claims /tmp/ai-chip-intelligence-claims.json \
      --graph /tmp/ai-chip-intelligence-evidence-graph.json \
      --output /tmp/ai-chip-intelligence-evidence-quality.json \
      --markdown /tmp/ai-chip-intelligence-evidence-quality.md

The report measures operational evidence hygiene, not factual correctness:

- **Quote traceability:** whether the extracted evidence quote can be found in
  the fetched candidate excerpt after the same text normalization used by
  extraction. This does not establish that the quote logically supports the
  interpretation.
- **Provenance completeness:** presence of a source URL, publisher, source
  type, declared independence label, evidence scope and parseable publication
  timestamp.
- **Metadata consistency:** whether source metadata copied onto a Claim still
  matches its originating discovery candidate.
- **Source diversity:** counts of distinct source documents and publishers.
  These are descriptive counts, not independent corroboration.
- **Evidence/assertion classes:** distributions of preprint, vendor, project,
  repository and reporting classes, plus assertion categories such as
  roadmap, marketing, research-result candidate or specification.
- **Reviewer-assigned origins:** counts only explicit origin annotations
  already present in the evidence graph. The audit never infers origin from
  publisher names or matching text.

The audit is deliberately not a single weighted quality score. It does not
rank a research preprint above a vendor primary source in all contexts,
equate media coverage with replication, infer peer-review status, or convert
the declared `independent` label into a verified relationship. Syndicated
articles and documents from the same underlying source may still appear as
different URLs or publishers. Exact-quote presence is necessary traceability,
not semantic entailment.

Every Claim remains `unverified_candidate`. No review state, company profile,
model support record, benchmark result or hardware registry is changed by this
audit. Human source inspection and the separate Evidence-to-PR approval gate
remain mandatory.
