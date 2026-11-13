#!/usr/bin/env python3
"""Offline orchestration of OTLP, Nsight Systems and DCGM capture artifacts."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from align_runtime_hardware_traces import align_record
from decompose_runtime_phases import decompose_database
from import_dcgm_telemetry import import_dcgm
from import_nsys_sqlite import import_nsys
from import_otel_traces import import_otlp_json
from process_otel_captures import assemble_captures
from reconcile_gpu_identities import reconcile_gpu_identities

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

def http_url(value, label):
    if not isinstance(value, str) or not re.match(r"^https?://\S+$", value):
        raise ValueError(label + " must be an actual HTTP(S) source URL")
    return value

def regular_file(path, label):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(label + " must be a regular non-symlink file")
    return path

def input_manifest(path, source_url, source_format):
    path = regular_file(path, source_format + " input")
    raw = path.read_bytes()
    return {"artifact": path.name, "source_format": source_format,
            "source_url": http_url(source_url, source_format + " source URL"),
            "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def pair_alignment(run_id, layer, traces, devices, max_pairs, identity_reconciled=False):
    candidate_count = len(traces) * len(devices)
    if candidate_count > max_pairs:
        raise ValueError(f"{layer} x DCGM alignment would create {candidate_count} candidate pairs (limit {max_pairs})")
    pairs, skipped_identity_pairs = [], 0
    for trace_record in traces:
        for device_record in devices:
            canonical_id = device_record.get("canonical_device_id")
            if identity_reconciled and canonical_id not in trace_record.get("canonical_device_ids", []):
                skipped_identity_pairs += 1
                continue
            pair_id = f"{run_id}:{layer}:{trace_record['id']}:{device_record['id']}"
            result = align_record({"id": pair_id, "runtime_trace": trace_record["runtime_trace"],
                                   "hardware_evidence": device_record["hardware_evidence"]})
            pairs.append({"pair_id": pair_id, "trace_record_id": trace_record["id"],
                          "device_record_id": device_record["id"],
                          "device_identity": canonical_id or device_record.get("device_identity"),
                          "pairing_basis": "operator_attested_gpu_identity_mapping" if identity_reconciled else "co-supplied_in_one_capture_bundle_only",
                          "alignment": result})
    return {
        "schema_version": "1.0", "generated_by": "scripts/run_capture_harness.py",
        "run_id": run_id, "comparison": layer + "_versus_dcgm",
        "candidate_pair_count": candidate_count, "pair_count": len(pairs),
        "skipped_unmatched_identity_pair_count": skipped_identity_pairs,
        "identity_reconciled": identity_reconciled,
        "records_with_overlapping_capture_windows": sum(p["alignment"]["status"] == "overlapping_capture_windows" for p in pairs),
        "eligible_metric_phase_join_count": sum(p["alignment"]["eligible_metric_phase_join_count"] for p in pairs),
        "pairs": pairs,
        "limitations": [
            "A shared run_id is an operator grouping, not proof of host, process, GPU or request identity.",
            "When enabled, device matching uses the operator-attested identity manifest bound to exact Nsight and DCGM artifact hashes.",
            "Capture-window overlap is descriptive and does not assign a metric to a request or kernel.",
            "DCGM observations have no metric-specific sample window; phase-level metric joins are ineligible.",
            "No counter interpolation, causal attribution, critical path or bottleneck verdict is generated.",
        ],
    }

def build_capture_bundle(*, run_id, otel_json=None, otel_capture_dir=None, otel_source_url=None,
                         service_name=None, root_span_name=None, category_map=None,
                         nsys_sqlite=None, nsys_source_url=None, clock_anchors=None,
                         dcgm_capture=None, dcgm_source_url=None, device_model=None,
                         gpu_identity_map=None, gpu_identity_map_sha256=None,
                         max_alignment_pairs=500):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", run_id):
        raise ValueError("run_id must be 1..96 safe ASCII letters, digits, dot, underscore or hyphen")
    if otel_json and otel_capture_dir:
        raise ValueError("choose either OTLP JSON or OTLP capture directory")
    if not any((otel_json, otel_capture_dir, nsys_sqlite, dcgm_capture)):
        raise ValueError("provide at least one OTLP, Nsight or DCGM input")
    if not 1 <= max_alignment_pairs <= 10000:
        raise ValueError("max_alignment_pairs must be in 1..10000")
    outputs, inputs, layers, warnings = {}, [], [], []
    otel_records, nsys_records, dcgm_records, nsys_result = [], [], [], None
    if otel_json or otel_capture_dir:
        http_url(otel_source_url, "OTLP source URL")
        if otel_json:
            path = regular_file(otel_json, "OTLP JSON input")
            raw = path.read_bytes()
            otel_result = import_otlp_json(json.loads(raw.decode("utf-8")), source_url=otel_source_url,
                artifact_sha256=hashlib.sha256(raw).hexdigest(), service_name=service_name,
                root_span_name=root_span_name, category_map=category_map)
            inputs.append({"artifact": path.name, "source_format": "opentelemetry_otlp_json",
                "source_url": otel_source_url, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        else:
            directory = Path(otel_capture_dir)
            if directory.is_symlink() or not directory.is_dir():
                raise ValueError("OTLP capture directory must be a real directory")
            otel_result = assemble_captures(directory, source_url=otel_source_url,
                service_name=service_name, root_span_name=root_span_name, category_map=category_map)
            inputs.append({"artifact": directory.name, "source_format": "opentelemetry_otlp_json_batches",
                           "source_url": otel_source_url, "capture_manifest": otel_result["capture_manifest"]})
        otel_records = otel_result["records"]
        outputs["runtime-traces.json"] = otel_result
        phases = decompose_database({"records": otel_records})
        outputs["runtime-phases.json"] = phases
        layers.append("opentelemetry_runtime")
        if phases["requests_with_ttft"] == 0:
            warnings.append("Trace-derived TTFT unavailable: explicit token_emit events are required.")
        if phases["requests_with_tpot"] == 0:
            warnings.append("Trace-derived TPOT unavailable: at least two explicit token_emit events per request are required.")
    if nsys_sqlite:
        http_url(nsys_source_url, "Nsight source URL")
        path = regular_file(nsys_sqlite, "Nsight SQLite input")
        nsys_result = import_nsys(path, source_url=nsys_source_url, anchors=clock_anchors)
        inputs.append(input_manifest(path, nsys_source_url, "nsight_systems_sqlite"))
        nsys_records = nsys_result.get("records", [])
        outputs["nsight-profiler.json"] = nsys_result
        layers.append("nsight_systems")
        if not nsys_records:
            warnings.append("Nsight events remain in session-relative time; UTC alignment is skipped without verified clock anchors.")
    if dcgm_capture:
        http_url(dcgm_source_url, "DCGM source URL")
        path = regular_file(dcgm_capture, "DCGM capture input")
        raw = path.read_bytes()
        dcgm_result = import_dcgm(json.loads(raw.decode("utf-8")), source_url=dcgm_source_url,
            artifact_sha256=hashlib.sha256(raw).hexdigest(), device_model=device_model)
        inputs.append({"artifact": path.name, "source_format": "dcgm_exporter_prometheus_text",
            "source_url": dcgm_source_url, "size_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        dcgm_records = dcgm_result["records"]
        outputs["dcgm-hardware-evidence.json"] = dcgm_result
        layers.append("nvidia_dcgm")
    identity_reconciled = False
    if gpu_identity_map is not None:
        if nsys_result is None or dcgm_result is None:
            raise ValueError("--gpu-identity-map requires both Nsight SQLite and DCGM capture inputs")
        nsys_records, dcgm_records, identity_report = reconcile_gpu_identities(
            nsys_result, dcgm_result, gpu_identity_map)
        if gpu_identity_map_sha256:
            identity_report["manifest_sha256"] = gpu_identity_map_sha256
        outputs["gpu-identity-reconciliation.json"] = identity_report
        inputs.append({"artifact": "gpu-identity-map.json",
                       "source_format": "operator_attested_gpu_identity_manifest",
                       "sha256": gpu_identity_map_sha256 or hashlib.sha256(
                           json.dumps(gpu_identity_map, sort_keys=True, separators=(",", ":")).encode("utf-8")
                       ).hexdigest()})
        identity_reconciled = True
    if otel_records and dcgm_records:
        outputs["runtime-dcgm-alignment.json"] = pair_alignment(
            run_id, "opentelemetry_runtime", otel_records, dcgm_records, max_alignment_pairs)
    if nsys_records and dcgm_records:
        outputs["nsight-dcgm-alignment.json"] = pair_alignment(
            run_id, "nsight_systems", nsys_records, dcgm_records, max_alignment_pairs,
            identity_reconciled=identity_reconciled)
    if len(layers) < 2:
        warnings.append("Only one telemetry layer is present; this is a single-layer validation, not cross-layer analysis.")
    if dcgm_records:
        warnings.extend(["DCGM DRAM activity is not HBM bandwidth.",
                         "DCGM scrape receipt timestamps are not exact GPU sample boundaries or time-weighted averages."])
    if nsys_result and dcgm_result and not identity_reconciled:
        warnings.append("Nsight gpuN indices are session-local; per-GPU Nsight/DCGM identity matching is disabled without an explicit artifact-bound GPU identity manifest.")
    warnings.append("Nsight CUPTI correlation IDs are candidate launch associations, not request/kernel completion dependencies.")
    report = {
        "schema_version": "1.0", "generated_by": "scripts/run_capture_harness.py",
        "run_id": run_id, "generated_at": utc_now(),
        "status": "complete" if len(layers) >= 2 else "partial_single_layer",
        "layers_available": layers, "inputs": inputs, "outputs": sorted(outputs),
        "summary": {
            "otel_request_records": len(otel_records),
            "nsys_events": len(nsys_result["events"]) if nsys_result else 0,
            "nsys_utc_trace_records": len(nsys_records), "dcgm_gpu_records": len(dcgm_records),
            "gpu_identity_mapped_devices": outputs.get("gpu-identity-reconciliation.json", {}).get("mapped_device_count", 0),
            "runtime_dcgm_pairs": outputs.get("runtime-dcgm-alignment.json", {}).get("pair_count", 0),
            "nsys_dcgm_pairs": outputs.get("nsight-dcgm-alignment.json", {}).get("pair_count", 0),
        },
        "warnings": list(dict.fromkeys(warnings)),
        "global_limitations": [
            "Offline artifact processing only; this harness does not launch workloads or collectors.",
            "A user-assigned run_id does not prove that collectors observed the same host or process.",
            "Nsight timestamps are translated to UTC only with independently verified, in-range clock anchors.",
            "No Nsight kernel is assigned to an OTel request without explicit validated cross-collector correlation evidence.",
            "GPU UUIDs are not inferred from local Nsight gpuN indices or OTel spans; an optional explicit inventory manifest is required.",
            "Temporal overlap is not causal attribution; no bottleneck verdict is emitted.",
        ],
    }
    return outputs, report

def write_bundle(output_dir, outputs, report, *, overwrite=False):
    directory = Path(output_dir)
    if directory.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    names = list(outputs) + ["capture-report.json"]
    if len(names) != len(set(names)):
        raise ValueError("duplicate output names")
    if not overwrite:
        existing = [name for name in names if (directory / name).exists()]
        if existing:
            raise FileExistsError("output exists; use --overwrite: " + ", ".join(existing))
    manifest = []
    for name, value in outputs.items():
        if Path(name).name != name:
            raise ValueError("output artifact name must be a basename")
        data = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        target = directory / name
        temporary = directory / ("." + name + "." + uuid.uuid4().hex + ".part")
        try:
            fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        manifest.append({"file": name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    final = dict(report)
    final["artifacts"] = manifest
    data = (json.dumps(final, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    target = directory / "capture-report.json"
    temporary = directory / (".capture-report." + uuid.uuid4().hex + ".part")
    try:
        fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return final

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", required=True)
    group = p.add_mutually_exclusive_group()
    group.add_argument("--otel-json", type=Path)
    group.add_argument("--otel-capture-dir", type=Path)
    p.add_argument("--otel-source-url")
    p.add_argument("--service-name")
    p.add_argument("--root-span-name")
    p.add_argument("--category-map", type=Path)
    p.add_argument("--nsys-sqlite", type=Path)
    p.add_argument("--nsys-source-url")
    p.add_argument("--clock-anchors", type=Path)
    p.add_argument("--dcgm-capture", type=Path)
    p.add_argument("--dcgm-source-url")
    p.add_argument("--device-model")
    p.add_argument("--gpu-identity-map", type=Path, help="Operator-attested GPU UUID / PCI / Nsight index mapping JSON")
    p.add_argument("--max-alignment-pairs", type=int, default=500)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    try:
        category_map = json.loads(regular_file(args.category_map, "category map").read_text(encoding="utf-8")) if args.category_map else None
        anchors = json.loads(regular_file(args.clock_anchors, "clock anchors").read_text(encoding="utf-8")) if args.clock_anchors else None
        identity_map_path = regular_file(args.gpu_identity_map, "GPU identity map") if args.gpu_identity_map else None
        identity_map_raw = identity_map_path.read_bytes() if identity_map_path else None
        identity_map = json.loads(identity_map_raw.decode("utf-8")) if identity_map_raw else None
        if category_map is not None and not isinstance(category_map, dict):
            raise ValueError("category map must be a JSON object")
        if anchors is not None and not isinstance(anchors, dict):
            raise ValueError("clock anchors must be a JSON object")
        if identity_map is not None and not isinstance(identity_map, dict):
            raise ValueError("GPU identity map must be a JSON object")
        if args.otel_capture_dir and args.output_dir.resolve() == args.otel_capture_dir.resolve():
            raise ValueError("output directory cannot be the OTLP capture directory")
        outputs, report = build_capture_bundle(
            run_id=args.run_id, otel_json=args.otel_json, otel_capture_dir=args.otel_capture_dir,
            otel_source_url=args.otel_source_url, service_name=args.service_name,
            root_span_name=args.root_span_name, category_map=category_map,
            nsys_sqlite=args.nsys_sqlite, nsys_source_url=args.nsys_source_url,
            clock_anchors=anchors, dcgm_capture=args.dcgm_capture,
            dcgm_source_url=args.dcgm_source_url, device_model=args.device_model,
            gpu_identity_map=identity_map,
            gpu_identity_map_sha256=hashlib.sha256(identity_map_raw).hexdigest() if identity_map_raw else None,
            max_alignment_pairs=args.max_alignment_pairs)
        write_bundle(args.output_dir, outputs, report, overwrite=args.overwrite)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, FileExistsError) as error:
        print("FAIL: " + str(error), file=sys.stderr)
        return 1
    print("PASS: run %s; layers=%s; outputs=%s; runtime/DCGM pairs=%s; Nsight/DCGM pairs=%s" % (
        args.run_id, ",".join(report["layers_available"]), len(outputs) + 1,
        report["summary"]["runtime_dcgm_pairs"], report["summary"]["nsys_dcgm_pairs"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
