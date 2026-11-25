# InferenceX prefill/decode GPU-count sensitivity

Run from the repository root:

```bash
python3 scripts/analyze_inferencex_prefill_decode_scaling.py --output /tmp/inferencex-prefill-decode-scaling.json
```

The analyzer separates phase-specific GPU-count observations.

- **Prefill** varies `physical_prefill_gpus`, while holding decode GPU count,
  workload, hardware, topology, software recipe and stable configuration fixed.
  It reports median and P99 TTFT where published.
- **Decode** varies `physical_decode_gpus`, while holding prefill GPU count and
  the same recorded context fixed. It reports median/P99 TPOT, P99 ITL and
  source-published output throughput/GPU where available.

A series requires at least two distinct positive GPU counts. Zero-prefill
systems are not prefill scaling points. The disaggregation/serving-mode field
is retained in the exact workload protocol; prefill and decode GPU counts are
never added together or treated as interchangeable.

For each point, the report retains source observations and provides min, median
of published values and max. It also reports the descriptive percentage change
from the smallest observed GPU count. This is not a scaling-efficiency score:
latency and throughput move in different desirable directions, and no
aggregate throughput is synthesized.

TP/EP and other stable configuration fields are held fixed. The report does not
measure scaling strategies that change parallelism with GPU count, attribute
effects to interconnects, or infer causal relationships. Unreported runtime and
topology details can remain confounders. No interpolation, extrapolation,
cost/power inference or benchmark execution is performed.
