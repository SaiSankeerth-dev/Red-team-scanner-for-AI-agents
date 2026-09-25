"""Generic HTTP target adapter.

POSTs {"messages": [...]} to any endpoint and extracts the agent's reply from
the JSON response via a dotted path (default: "response"). List indices work
too, e.g. "choices.0.message.content".
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from .base import TargetAdapter, ToolCallLog


def extract_path(obj, path: str):
    """Pull a value out of nested dicts/lists via a dotted path."""
    cur = obj
    for part in path.split("."):
        try:
            if isinstance(cur, list):
                cur = cur[int(part)]
            elif isinstance(cur, dict):
                cur = cur[part]
            else:
                raise KeyError(part)
        except (KeyError, IndexError, ValueError) as e:
            raise KeyError(f"path '{path}' not found in target response") from e
    return cur


class HTTPTargetAdapter(TargetAdapter):
    def __init__(
        self,
        url: str,
        response_path: str = "response",
        headers: dict | None = None,
        timeout: int = 60,
    ) -> None:
        self.url = url
        self.response_path = response_path
        self.headers = headers or {}
        self.timeout = timeout
        # No structured tool calls over generic HTTP; probes fall back to text.
        self.agent = ToolCallLog()

    def send(self, messages: list[dict[str, str]]) -> str:
        body = {"messages": messages}
        headers = {"Content-Type": "application/json", **self.headers}
        req = urllib.request.Request(
            self.url, data=json.dumps(body).encode(), headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise RuntimeError(f"target HTTP error {e.code}: {detail}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"target unreachable: {e.reason}")

        try:
            value = extract_path(payload, self.response_path)
        except KeyError as e:
            raise RuntimeError(str(e))
        return value if isinstance(value, str) else json.dumps(value)
