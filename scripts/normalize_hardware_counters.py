#!/usr/bin/env python3
"""Normalize a JSON counter export using the versioned hardware mapping catalog."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from hardware_counter_mapping import load_catalog, normalize_payload
from validate_benchmark_results import validate_hardware_evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Raw JSON export wrapper with collector, scope, sampling, provenance and counters")
    parser.add_argument("--output", required=True, type=Path, help="Destination JSON file; input is never overwritten")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        normalized = normalize_payload(payload, load_catalog())
        evidence = normalized["hardware_evidence"]
        errors = validate_hardware_evidence({"hardware_evidence": evidence}, "hardware_evidence")
        if errors:
            raise ValueError("; ".join(errors))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        f"PASS: normalized {len(evidence['metrics'])} counters; "
        f"{len(normalized['unmapped_counters'])} remain unmapped. "
        f"Wrote {args.output}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
