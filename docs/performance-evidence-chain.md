# Performance evidence chain

Review externally reported runs against an immutable experiment-plan snapshot.
This is an offline information-review tool, not a hardware experiment runner.

```bash
python3 scripts/review_performance_experiment_evidence.py --record record.json --plan plan.json --submission submission.json --output review.json
```

Submission version 1.0 requires plan_id, experiment_id, record_sha256, plan_sha256,
protocol and runs. Compute hashes using the script's digest() function
(canonical sorted compact UTF-8 JSON, SHA-256). The protocol declares parameter,
baseline_value, treatment_value, fixed_context, primary_metric (key, unit,
direction), practical_effect_percent and protocol_source_url. Each run supplies
a unique run_id, condition (baseline/treatment), status (valid/failed/invalid)
and source_url. Valid runs also supply parameter_value, fixed_context,
metric_key, unit and numeric value. Failed/invalid runs supply reason.

See tests/test_performance_evidence_review.py for a complete synthetic example.
It is not production benchmark evidence.

A review binds the exact record, plan and submission hashes. It rejects
mismatched identities, declared contexts, metrics or intervention values.
It preserves failed runs and reports medians and observed ranges. Insufficient
valid repetitions, failed/invalid runs or unavailable relative change block
threshold interpretation. Positive improvement is direction-aware.

The practical effect threshold is submitter-defined, not statistical
significance. The reviewer does not verify that it was registered before
execution, that sources exist, that all runs were submitted, or that declared
controls match physical reality. Mechanism-specific counters, baseline
reproduction and time alignment require human review. No approval, causal
attribution or registry mutation is automatic. The hypothesis verdict remains
undetermined; the output is a review packet rather than a persisted decision.
