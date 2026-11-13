#!/usr/bin/env python3
"""Combine saved OTLP batches before importing into the AI-Chip runtime analyzer."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from import_otel_traces import import_otlp_json
from decompose_runtime_phases import decompose_database


def assemble_captures(directory, *, source_url, service_name=None, root_span_name=None, category_map=None):
    files = sorted(Path(directory).glob("otlp-*.json"))
    if not files:
        raise ValueError("no captured otlp-*.json batches found")
    groups, manifest = [], []
    for file in files:
        if file.is_symlink() or not file.is_file():
            raise ValueError("capture path must be a regular file")
        raw = file.read_bytes()
        batch = json.loads(raw)
        if not isinstance(batch, dict) or not isinstance(batch.get("resourceSpans"), list):
            raise ValueError("invalid OTLP batch: " + file.name)
        groups.extend(batch["resourceSpans"])
        manifest.append({"file": file.name, "size_bytes": len(raw),
                         "sha256": hashlib.sha256(raw).hexdigest()})
    report = import_otlp_json({"resourceSpans": groups}, source_url=source_url,
                              service_name=service_name, root_span_name=root_span_name,
                              category_map=category_map)
    report["capture_manifest"] = manifest
    report["capture_batch_count"] = len(manifest)
    return report


def write_json(path, value, overwrite=False):
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError("output exists: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / ("." + path.name + "." + uuid.uuid4().hex + ".part")
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--capture-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--report", type=Path)
    p.add_argument("--source-url", required=True)
    p.add_argument("--service-name")
    p.add_argument("--root-span-name")
    p.add_argument("--category-map", type=Path)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    try:
        if args.report and args.report.resolve() == args.output.resolve():
            raise ValueError("output and report must differ")
        mapping = json.loads(args.category_map.read_text()) if args.category_map else None
        if mapping is not None and not isinstance(mapping, dict):
            raise ValueError("category map must be a JSON object")
        result = assemble_captures(args.capture_dir, source_url=args.source_url,
                                   service_name=args.service_name, root_span_name=args.root_span_name,
                                   category_map=mapping)
        if not args.overwrite and (args.output.exists() or (args.report and args.report.exists())):
            raise FileExistsError("output already exists; use --overwrite")
        if args.report:
            write_json(args.report, decompose_database({"records": result["records"]}), args.overwrite)
        write_json(args.output, result, args.overwrite)
    except (OSError, ValueError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    print("PASS: %s batches, %s normalized request records" % (result["capture_batch_count"], len(result["records"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
