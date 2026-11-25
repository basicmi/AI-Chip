# InferenceX concurrency sweep intelligence

This report analyzes published observations only. It does not execute benchmark
experiments or claim measured performance of untested configurations.

Run from the repository root:

```bash
python3 scripts/analyze_inferencex_concurrency.py --output /tmp/inferencex-concurrency-report.json
```

The engine uses the existing comparability protocol and removes only concurrency
from its workload key. Hardware name, system boundary, model, ISL/OSL, precision,
serving and speculative mode, software metadata, stable execution configuration
and source evidence class must match. A published recipe fingerprint is mandatory.
Transient workflow identifiers do not split the stable execution configuration.
Unknown fingerprints or incomplete configuration are excluded.

Seven source-normalized metric series are supported: output throughput per GPU,
median interactivity, median/P99 TTFT, median/P99 TPOT and P99 ITL. Each series
requires exact metric units, family and direction, finite nonnegative values and
at least two distinct positive integer concurrency levels. Each point retains
all contributing record IDs, source links and publication dates, plus the
minimum, maximum and median of published values. That median is not a pooled
request-level percentile. Different metric series may contain different records;
their point medians must not be combined into a synthetic run.

The output is an auditable JSON artifact generated during CI. Exclusion reason
counts are diagnostic events, not mutually exclusive record counts. A sweep is
a set of observed matching-context points, not proof that concurrency caused
the differences; unreported execution context and benchmark-version changes may
still matter. There is no interpolation, extrapolation, automated saturation
threshold, GPU scaling or cost inference in this version.

The public Results UI remains unchanged in this PR. A subsequent UI iteration
can expose these observations as scatter plots with individual record links
and repeated-observation ranges.
