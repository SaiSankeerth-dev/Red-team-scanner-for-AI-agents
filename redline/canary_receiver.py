"""Canary webhook receiver: tripwires for leaked secrets.

Workflow:
  1. ``redline canary new --label prod-docs`` mints a fresh canary token and
     prints a hit URL served by this receiver.
  2. Plant the token (or the URL) anywhere a leak would be catastrophic: a
     system prompt, a retrieved document, a config file.
  3. Run the receiver (``redline canary-watch --port 8787``). If the canary
     ever phones home — someone renders the URL, a scanner exfiltrates it —
     the hit is logged and, if ``CANARY_ALERT_WEBHOOK`` is set, forwarded
     as a JSON alert.

Stdlib only (http.server). Hits append to
``$CANARY_HIT_LOG`` or ``~/.redline-canary-hits.jsonl``.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .canary import generate_canary


def hit_log_path() -> str:
    return os.environ.get(
        "CANARY_HIT_LOG", os.path.expanduser("~/.redline-canary-hits.jsonl")
    )


def mint_canary(label: str = "", public_url: str = "") -> dict:
    token = generate_canary()
    base = (public_url or os.environ.get("CANARY_PUBLIC_URL", "")).rstrip("/")
    return {
        "token": token,
        "label": label,
        "hit_url": f"{base}/c/{token}" if base else f"(set CANARY_PUBLIC_URL) /c/{token}",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _alert(hit: dict) -> None:
    webhook = os.environ.get("CANARY_ALERT_WEBHOOK")
    if not webhook:
        return
    try:
        req = urllib.request.Request(
            webhook,
            data=json.dumps(
                {
                    "text": (
                        f"🚨 canary hit: `{hit['token'][:18]}…` "
                        f"(label: {hit.get('label') or '—'}) "
                        f"from {hit.get('ip')} at {hit['ts']}"
                    )
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:  # alerting must never crash the receiver
        print(f"[canary] alert webhook failed: {e}")


class _Handler(BaseHTTPRequestHandler):
    def _record(self, token: str) -> None:
        hit = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "token": token,
            "label": self.headers.get("X-Canary-Label", ""),
            "ip": self.client_address[0],
            "user_agent": self.headers.get("User-Agent", ""),
            "path": self.path,
        }
        path = hit_log_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(hit) + "\n")
        print(f"[canary] HIT token={token[:18]}… ip={hit['ip']} label={hit['label']!r}")
        _alert(hit)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/c/") and len(parsed.path) > 3:
            self._record(parsed.path[3:])
            body = b"ok"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        token = ""
        try:
            token = json.loads(raw or b"{}").get("token", "")
        except (json.JSONDecodeError, AttributeError):
            pass
        if urlparse(self.path).path == "/canary/hit" and token:
            self._record(token)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args) -> None:  # keep stdout for hits only
        pass


def serve(port: int = 8787) -> None:
    server = HTTPServer(("0.0.0.0", port), _Handler)
    print(f"[canary] listening on :{port} — GET /c/<token>, POST /canary/hit")
    print(f"[canary] hits -> {hit_log_path()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[canary] stopped")


def cmd_canary_new(args) -> int:
    info = mint_canary(label=args.label or "")
    print(f"[redline] canary token : {info['token']}")
    print(f"[redline] label        : {info['label'] or '—'}")
    print(f"[redline] hit URL      : {info['hit_url']}")
    print("[redline] plant the token (or URL) where a leak would be catastrophic;")
    print("[redline] run `redline canary-watch` to listen for hits.")
    return 0


def cmd_canary_watch(args) -> int:
    serve(port=args.port)
    return 0
