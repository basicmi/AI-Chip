#!/usr/bin/env python3
"""Serve a Jekyll project site under its GitHub Pages baseurl."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1] / "_site"
BASE = "/AI-Chip"

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean == BASE:
            clean = "/"
        elif clean.startswith(BASE + "/"):
            clean = clean[len(BASE):]
        return str(ROOT / clean.lstrip("/"))

if __name__ == "__main__":
    os.chdir(ROOT)
    ThreadingHTTPServer(("0.0.0.0", 4173), Handler).serve_forever()
