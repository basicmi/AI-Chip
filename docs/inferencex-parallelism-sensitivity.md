# InferenceX parallelism sensitivity

Run `python3 scripts/analyze_inferencex_parallelism.py --output /tmp/parallelism.json`
from the repository root.

Four independent axes are supported: prefill TP, prefill EP, decode TP and decode
EP. Each comparison varies one positive integer degree while holding the
recorded workload, hardware, GPU role counts, topology, software and all other
stable configuration fields fixed. At least two levels are required.

Strict series require the same nonempty recipe fingerprint; they report
individual observations and observed min/max/median by degree. TTFT is associated
with prefill and TPOT/ITL/output throughput with decode, but these are published
serving metrics, not isolated phase timing or throughput measurements.

A fingerprint can itself encode TP/EP settings. Groups with differing or absent
fingerprints are therefore retained separately as review candidates, with
original values, source links, fingerprints and explicit review reasons. These
are not validated comparisons: no aggregate, relative speedup or ranking is
computed for candidates. A strict subgroup can coexist with a review candidate;
counts are metric-level and not mutually exclusive.

The analyzer does not infer missing settings, change the benchmark registry,
execute benchmarks or estimate causal effects. Other unrecorded settings may
differ even within strict groups. A future review workflow should inspect source
recipes before considering any additional equivalence rules.
