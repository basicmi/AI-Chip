# InferenceX ISL / OSL sensitivity analysis

Run from the repository root:

```bash
python3 scripts/analyze_inferencex_sequence_length.py --output /tmp/inferencex-sequence-length-report.json
```

The analyzer uses only published InferenceX registry observations. It creates two
separate series families:

- **ISL sensitivity**: groups records while holding OSL, concurrency, model,
  precision, serving mode, hardware, system boundary, software and stable
  execution configuration fixed. It reports output throughput/GPU, median TTFT
  and P99 TTFT when present.
- **OSL sensitivity**: groups records while holding ISL, concurrency and the
  same system/software context fixed. It reports output throughput/GPU, median
  TPOT, P99 TPOT and P99 ITL when present.

Only the selected sequence-length dimension is removed from the workload key.
A series requires at least two distinct observed lengths, a published recipe
fingerprint and complete stable execution configuration. Each point retains
all record IDs, source URLs and publication dates, plus the minimum, maximum
and median of published values.

Endpoint relative change is a descriptive difference between the lowest and
highest observed sequence lengths. It is not a fitted sensitivity coefficient,
causal estimate or guarantee of monotonic response. Median of published values
is not a pooled request-level percentile. Different metrics may have different
underlying records and must not be joined into synthetic runs.

No interpolation, extrapolation, KV-cache estimate, throughput normalization
beyond the source-published per-GPU metric, cost estimate, saturation threshold
or benchmark execution is performed. Unreported execution context can still
confound the comparison; InferenceX benchmark version may be unreported.
