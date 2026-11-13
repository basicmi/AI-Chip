#!/usr/bin/env python3
"""Local-only by default OTLP/HTTP JSON receiver. No protobuf or gRPC."""
from __future__ import annotations
import argparse
import hmac
import json
import os
import socket
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class TraceStore:
    def __init__(self, directory, storage_limit=1073741824, file_limit=10000):
        self.path = Path(directory)
        if self.path.is_symlink():
            raise ValueError("capture directory cannot be a symlink")
        self.path.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.path, 0o700)
        self.lock = threading.Lock()
        self.storage_limit, self.file_limit = storage_limit, file_limit

    def save(self, body):
        with self.lock:
            files = list(self.path.glob("otlp-*.json"))
            if len(files) >= self.file_limit or sum(f.stat().st_size for f in files) + len(body) > self.storage_limit:
                raise OverflowError("storage quota reached")
            name = "otlp-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-") + uuid.uuid4().hex
            temporary, final = self.path / (name + ".part"), self.path / (name + ".json")
            try:
                fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(body)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, final)
                if hasattr(os, "O_DIRECTORY"):
                    dfd = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(dfd)
                    finally:
                        os.close(dfd)
            finally:
                temporary.unlink(missing_ok=True)
            return final


def create_server(host="127.0.0.1", port=4318, directory=".ai-chip-captures", *,
                  max_body=8388608, storage_limit=1073741824, file_limit=10000,
                  token=None, allow_remote=False):
    if not 0 <= port <= 65535 or min(max_body, storage_limit, file_limit) <= 0:
        raise ValueError("invalid port or quota")
    try:
        loopback = all(info[4][0] in ("127.0.0.1", "::1")
                       for info in socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP))
    except socket.gaierror:
        loopback = False
    if not loopback and (not allow_remote or not token):
        raise ValueError("non-loopback requires --allow-remote and a bearer token")
    if allow_remote and not token:
        raise ValueError("--allow-remote requires a bearer token")
    store = TraceStore(directory, storage_limit, file_limit)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "AIChipOTLP/1.0"

        def log_message(self, fmt, *args):
            sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

        def reply(self, status, result):
            body = json.dumps(result, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def do_GET(self):
            self.reply(200, {"status": "ok"}) if self.path == "/healthz" else self.reply(404, {"error": "not_found"})

        def do_POST(self):
            if self.path != "/v1/traces":
                return self.reply(404, {"error": "not_found"})
            if token and not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + token):
                return self.reply(401, {"error": "unauthorized"})
            if self.headers.get("Transfer-Encoding"):
                return self.reply(411, {"error": "content_length_required"})
            if self.headers.get("Content-Encoding", "identity").lower() != "identity":
                return self.reply(415, {"error": "unsupported_encoding"})
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                return self.reply(415, {"error": "expected_json"})
            length = self.headers.get("Content-Length", "")
            if not length.isascii() or not length.isdecimal():
                return self.reply(411, {"error": "content_length_required"})
            n = int(length)
            if n <= 0:
                return self.reply(400, {"error": "empty_request"})
            if n > max_body:
                return self.reply(413, {"error": "too_large"})
            body = self.rfile.read(n)
            if len(body) != n:
                return self.reply(400, {"error": "incomplete_request"})
            try:
                obj = json.loads(body.decode("utf-8"))
            except (ValueError, UnicodeError):
                return self.reply(400, {"error": "invalid_json"})
            if not isinstance(obj, dict) or not isinstance(obj.get("resourceSpans"), list):
                return self.reply(400, {"error": "expected_resourceSpans"})
            try:
                store.save(body)
            except OverflowError:
                return self.reply(507, {"error": "storage_quota_exceeded"})
            except OSError:
                return self.reply(503, {"error": "storage_unavailable"})
            self.reply(200, {"partialSuccess": {}})

    class Server(ThreadingHTTPServer):
        daemon_threads = True
    return Server((host, port), Handler)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=4318)
    p.add_argument("--capture-dir", type=Path, default=Path(".ai-chip-captures"))
    p.add_argument("--max-body", type=int, default=8388608)
    p.add_argument("--storage-limit", type=int, default=1073741824)
    p.add_argument("--file-limit", type=int, default=10000)
    p.add_argument("--token-env")
    p.add_argument("--allow-remote", action="store_true")
    args = p.parse_args()
    token = os.environ.get(args.token_env) if args.token_env else None
    if args.token_env and not token:
        p.error("--token-env is missing or empty")
    try:
        server = create_server(args.host, args.port, args.capture_dir, max_body=args.max_body,
                               storage_limit=args.storage_limit, file_limit=args.file_limit,
                               token=token, allow_remote=args.allow_remote)
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    print("OTLP JSON receiver on http://%s:%s/v1/traces" % (args.host, server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
