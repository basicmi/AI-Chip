# Live OTLP/HTTP JSON Collector

PR #82 adds a local-first HTTP JSON receiver and capture assembler. It is not
an OTLP/gRPC or protobuf receiver, and does not instrument vLLM by itself.

## Run the receiver

    python3 scripts/collect_otel_http.py \
      --capture-dir ~/.local/share/ai-chip/otel-captures

The default endpoint is http://127.0.0.1:4318/v1/traces. POST application/json
OTLP payloads with resourceSpans[] are stored verbatim in private otlp-*.json
files. A 200 response with partialSuccess is sent only after an atomic durable
write. GET /healthz provides a basic liveness check.

Many vLLM / OpenTelemetry SDK exporters default to OTLP/HTTP protobuf, NOT JSON.
Protobuf requests receive 415. Configure an OTLP/HTTP JSON exporter or use an
OpenTelemetry Collector with JSON export support to forward to this receiver.
Refer to https://opentelemetry.io/docs/specs/otlp/#otlphttp and
https://docs.vllm.ai/en/latest/examples/observability/opentelemetry/.

## Security

Receiver is restricted to loopback by default. Non-loopback listening
requires both --allow-remote and --token-env ENV_VAR (a non-empty bearer token).
Plain HTTP is not encrypted: terminate TLS in a secure proxy if used remotely.
The default body limit is 8 MiB, total storage 1 GiB, files 10,000.
Quota exhaustion returns HTTP 507 instead of deleting previously saved batches.
Capture directory and files use POSIX modes 0700 and 0600 respectively.

Traces may contain sensitive inputs and prompts. Do not publish them in the
website's data registry or commit them to Git. Archive older batches manually
after verification; no automated data retention or deletion is implemented.

## Offline batch assembly and analysis

Request-related spans can arrive in separate OTLP batches. Combine ALL captured
resourceSpans before calling the existing importer:

    python3 scripts/process_otel_captures.py \
      --capture-dir ~/.local/share/ai-chip/otel-captures \
      --output /tmp/ai-chip-records.json \
      --report /tmp/ai-chip-phases.json \
      --source-url https://YOUR-TRACE-SYSTEM.example/export \
      --service-name vllm

Replace the URL placeholder with the actual source URL; do not publish a
fictitious URL. Output includes SHA-256 and size for each capture batch.
No synthetic per-token timestamps or dependency graph edges are generated.
Without actual token_emit span events, trace-derived TTFT/TPOT are unavailable.

Limitations: only OTLP/HTTP JSON with Content-Length, no protobuf, chunked, gzip
or gRPC. This is a development/debugging receiver, not a hardened public service.
