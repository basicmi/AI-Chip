# Performance hypothesis comparison

Compare several competing explanations against one validated diagnosis report.
The engine preserves the diagnosis engine's undetermined verdict and does not
rank hypotheses or infer causality.

## Example

```bash
python3 scripts/diagnose_hardware_performance.py \
  --input benchmark-record.json --output diagnosis.json

python3 scripts/retrieve_performance_knowledge.py \
  --catalog data/performance-knowledge.json \
  --query "decode TPOT queueing communication" \
  --target target-context.json --output retrieval.json

python3 scripts/compare_performance_hypotheses.py \
  --diagnosis diagnosis.json \
  --hypotheses data/performance-hypothesis-catalog.json \
  --retrieval retrieval.json \
  --output hypothesis-comparison.json
```

## Evidence states

- `supporting_signal_observed`: a diagnostic observation associated with the
  mechanism exists. It is not causal attribution.
- `not_observed_in_sampled_window`: a specific diagnostic channel reported no
  event in its supplied window. It does not exclude out-of-window or unmeasured
  effects.
- `insufficient_or_unattributed`: a channel exists but is incomplete or not
  attributed.
- `no_direct_diagnostic_evidence`: no mapped diagnostic channel was supplied.

The default catalog includes compute ceiling, memory ceiling, communication
critical path, KV-cache pressure, runtime queueing and thermal/power throttling.
Each hypothesis lists discriminating measurements, observations that would
support it and observations that would weaken it. These are investigation
protocols, not an automatic test result.

Optional retrieved knowledge is attached as historical context only. A
Supported/Refuted historical claim does not vote on the current hypothesis.
Applicability tier, evidence references and limitations remain visible.

No numeric confidence score, automatic ordering, causal verdict, configuration
recommendation, experiment execution or knowledge promotion is performed.
Choose the next discriminating measurement through human review and retain
competing explanations until the evidence separates them.
