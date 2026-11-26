#!/usr/bin/env python3
"""Generate falsifiable, non-executing performance experiment plans from a benchmark record."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diagnose_hardware_performance import diagnose_record

DERIVER = "scripts/build_performance_experiment_plan.py"
SLUG = re.compile(r"[^a-z0-9]+")

MECHANISMS = {
    "roofline": {
        "title": "Roofline evidence acquisition",
        "hypothesis": "A compute-side or memory-side ceiling may constrain performance, but current measurements cannot locate the workload on a comparable roofline.",
        "intervention": "Do not tune compute or memory parameters yet. First collect interval FLOPs, DRAM read/write bytes and precision/sparsity-matched compute and bandwidth peaks.",
        "controls": ["Capture all counters over the same sampling window and scope/entity.", "Record precision, sparsity, cache state and exact workload."],
        "measure": ["Interval compute FLOP count", "DRAM read/write byte totals", "Precision/sparsity-matched theoretical peak FLOP/s", "Same-boundary peak DRAM bandwidth", "SM/Tensor activity over the same interval"],
        "supports": "A complete compatible capture enables a defensible roofline position; further controlled interventions are then needed to test runtime impact.",
        "weakens": "A complete capture places the workload far from both modeled ceilings; investigate other mechanisms without treating this alone as proof.",
        "caveat": "Roofline is a ceiling model; it does not by itself establish a runtime bottleneck."
    },
    "roofline_compute": {
        "title": "Compute-side ceiling / execution efficiency",
        "hypothesis": "A compute-side execution limit materially contributes to the observed performance symptom.",
        "intervention": "Change one compute-relevant factor only (for example, kernel implementation, tile shape or precision) after recording the exact parameter and value.",
        "controls": ["Keep model weights, workload shape, batch/concurrency, hardware, clocks/power policy and software recipe fixed.", "Keep numerical accuracy and output-quality acceptance criteria fixed."],
        "measure": ["Per-kernel achieved FLOP/s and duration", "Precision/sparsity-matched peak definition", "SM and Tensor activity over the same kernel interval", "TTFT, TPOT/ITL and output throughput"],
        "supports": "The treatment changes the targeted compute evidence and improves the predeclared serving metric while memory traffic, communication and workload remain comparable.",
        "weakens": "The targeted compute evidence changes as intended but the serving metric does not, or the apparent gain disappears after matching workload and measurement boundaries.",
        "caveat": "A lower roofline ceiling is a model comparison, not proof that the runtime is compute-bound."
    },
    "roofline_memory": {
        "title": "Memory-side ceiling / data movement",
        "hypothesis": "Memory traffic or data movement materially contributes to the observed performance symptom.",
        "intervention": "Change one data-reuse or memory-layout factor only; specify the exact kernel/configuration parameter before execution.",
        "controls": ["Keep model, workload, batch/concurrency, hardware, clocks/power policy and software recipe fixed.", "Preserve precision, numerical output and cache-state policy."],
        "measure": ["DRAM read/write bytes and achieved bandwidth", "Same-boundary peak bandwidth", "Kernel duration and cache behavior", "TTFT, TPOT/ITL and output throughput"],
        "supports": "The treatment reduces measured bytes or improves effective data reuse and produces a repeatable serving improvement without changing workload or compute semantics.",
        "weakens": "DRAM traffic/bandwidth is unchanged, or the serving metric does not respond despite a verified change in the targeted memory behavior.",
        "caveat": "DRAM activity or a roofline memory ceiling alone does not prove bandwidth saturation."
    },
    "communication_link_utilization": {
        "title": "Interconnect traffic / communication critical path",
        "hypothesis": "Communication contention or exposed communication time materially contributes to the observed performance symptom.",
        "intervention": "Change one communication factor only (for example, parallel decomposition, collective algorithm or placement); record the exact factor and value.",
        "controls": ["Keep model, token lengths, concurrency, total accelerator count and software recipe fixed.", "Keep topology, routing and link measurement scope documented; if one is intentionally changed, treat it as the sole intervention."],
        "measure": ["Per-link directional TX/RX bytes and capacity", "Collective duration and communication wait", "Kernel/communication intervals on a mapped clock", "TTFT, TPOT/ITL and output throughput"],
        "supports": "The treatment reduces exposed communication/wait time and improves the serving metric with comparable compute and workload evidence.",
        "weakens": "Traffic changes without reducing exposed wait or improving serving performance, or observed link utilization is not aligned with critical-path intervals.",
        "caveat": "Link utilization is not itself a critical-path or communication-bottleneck measurement."
    },
    "communication": {
        "title": "Interconnect evidence acquisition",
        "hypothesis": "Communication may contribute to the observed symptom, but current evidence is insufficient to test that hypothesis.",
        "intervention": "Do not tune topology or parallelism yet. First attach per-link directional traffic, matching capacity and request-correlated communication intervals.",
        "controls": ["Use the same workload and system configuration for profiler and serving captures.", "Record physical/logical topology and collective algorithm."],
        "measure": ["Per-link TX/RX bytes and directionality-matched peak", "Collective duration and communication wait", "Clock mapping and request correlation"],
        "supports": "A validated capture establishes compatible link traffic/capacity and exposes communication wait on the request critical path.",
        "weakens": "A complete, aligned capture shows no material communication wait for the investigated workload.",
        "caveat": "Absence of telemetry is not evidence that communication is absent."
    },
    "kv_cache_occupancy": {
        "title": "KV-cache capacity / allocator behavior",
        "hypothesis": "KV-cache capacity or allocator behavior materially contributes to decode latency or request scheduling.",
        "intervention": "Change one KV-cache capacity, block-allocation or eviction-policy parameter only; record the exact value and policy.",
        "controls": ["Keep model, prompt/output lengths, concurrency, scheduler and hardware fixed.", "Keep request mix and cache warm/cold policy identical."],
        "measure": ["KV used/capacity bytes and tokens", "Allocator events, block fragmentation, eviction and preemption", "Request stalls and decode TPOT/ITL", "Throughput and successful-query rate"],
        "supports": "The treatment changes allocator/eviction behavior and produces a repeatable decode or throughput response under the same request mix.",
        "weakens": "Capacity/allocator behavior changes without a corresponding serving response, or the response is explained by a changed request mix.",
        "caveat": "Occupancy alone does not establish eviction, preemption or decode stalls."
    },
    "kv_cache_capacity_pressure": {
        "title": "KV-cache evidence acquisition",
        "hypothesis": "KV-cache pressure is possible but cannot be assessed from the supplied record.",
        "intervention": "Do not change cache policy yet. First capture matched used/capacity bytes or tokens plus allocator, eviction and preemption events.",
        "controls": ["Align telemetry to the same device/process and time window as the serving workload.", "Record request lengths, concurrency and cache policy."],
        "measure": ["KV used and capacity at the same boundary", "Allocator and eviction/preemption counters", "Decode stalls and request-level latency"],
        "supports": "A validated matched capture shows capacity/allocator events correlated with request-level decode stalls.",
        "weakens": "A complete capture shows no capacity or allocator events during the observed symptom.",
        "caveat": "Missing KV-cache telemetry is unknown, not zero."
    },
    "thermal_or_power_throttling": {
        "title": "Thermal / power throttling",
        "hypothesis": "Active thermal or power throttling materially contributes to the observed performance symptom.",
        "intervention": "Only after capturing throttle reasons, change one permitted power/thermal control factor; do not bypass hardware safety limits.",
        "controls": ["Keep workload, software, clocks policy and ambient/cooling conditions fixed or recorded.", "Never exceed vendor operating or safety limits."],
        "measure": ["Throttle-active and reason counters", "GPU clocks, power and temperature over time", "Kernel duration and serving metrics"],
        "supports": "A safe intervention changes the reported throttle reason/activity and yields a repeatable performance response.",
        "weakens": "Throttle counters remain inactive during the symptom, or verified throttle changes do not affect the serving metric.",
        "caveat": "Temperature or power alone does not prove active throttling."
    },
    "runtime_scheduling_or_queueing": {
        "title": "Runtime scheduling / queueing",
        "hypothesis": "Queue wait, batch formation, host dispatch or kernel gaps materially contribute to the observed serving latency.",
        "intervention": "Change one scheduler/batching parameter only after collecting phase-level traces; specify the exact parameter and value.",
        "controls": ["Keep request arrival trace, model, hardware, software recipe and request mix fixed.", "Preserve concurrency semantics and report offered load as well as achieved throughput."],
        "measure": ["Request arrival and queue-wait timestamps", "Batch formation/wait and active batch size by phase", "CPU scheduling, dispatch and synchronization", "Kernel launch gaps and per-kernel active duration", "TTFT, TPOT/ITL and throughput"],
        "supports": "The treatment reduces the targeted queue/dispatch/kernel-gap component and improves the predeclared serving metric at comparable offered load.",
        "weakens": "The targeted component does not change, or serving performance remains unchanged despite a verified reduction in that component.",
        "caveat": "TTFT/TPOT and aggregate GPU utilization do not isolate queueing or scheduler delay."
    }
}


def _slug(value: Any) -> str:
    return SLUG.sub("-", str(value or "unknown").lower()).strip("-")[:48] or "unknown"


def _candidate_key(candidate: dict) -> str:
    mechanism = candidate.get("mechanism", "")
    if mechanism == "roofline":
        return "roofline"
    if mechanism.startswith("roofline_"):
        return "roofline_compute" if "compute" in mechanism else "roofline_memory"
    return mechanism if mechanism in MECHANISMS else "runtime_scheduling_or_queueing"

