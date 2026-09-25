"""Adapters for third-party CTF / challenge targets.

These targets explicitly invite security testing (prompt-injection games and
CTFs), but only within their intended challenge behavior: chat-based attack
prompts at a human-like rate. This module provides:

- ``RateLimitedAdapter``: wraps any adapter and enforces a minimum delay
  between sends, so automated campaigns stay close to manual play.
- ``GandalfAdapter``: Lakera Gandalf (gandalf.lakera.ai) via its public
  message API. Stateless per request — the latest user message is sent.
- ``PromptAirlinesAdapter``: Wiz promptairlines.com CTF via its chat
  endpoint (session cookie + JSON POST, HTML stripped from replies).
"""
from __future__ import annotations

import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request

from .base import TargetAdapter, ToolCallLog

#: Default pause between attack prompts: ~one human player thinking + typing.
HUMAN_CADENCE_SECONDS = 4.0

_BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class RateLimitedAdapter(TargetAdapter):
    """Wrap another adapter; sleep between sends to mimic human cadence."""

    def __init__(
        self, inner: TargetAdapter, delay: float = HUMAN_CADENCE_SECONDS
    ) -> None:
        self.inner = inner
        self.delay = delay
        self._last_send = 0.0
        # Expose the inner adapter's agent (tool-call log) if it has one,
        # so probes that inspect tool calls keep working.
        self.agent = getattr(inner, "agent", None)

    def send(self, messages: list[dict[str, str]]) -> str:
        wait = self.delay - (time.monotonic() - self._last_send)
        if wait > 0:
            time.sleep(wait)
        try:
            return self.inner.send(messages)
        finally:
            self._last_send = time.monotonic()


class GandalfAdapter(TargetAdapter):
    """Lakera Gandalf prompt-injection game.

    POSTs form-encoded ``defender=<level>&prompt=<message>`` to the public
    game API and returns the ``answer`` field. The game is stateless per
    request, so only the latest user message is sent.
    """

    API_URL = "https://gandalf-api.lakera.ai/api/send-message"
    LEVELS = (
        "baseline",
        "do-not-tell",
        "do-not-tell-and-block",
        "gpt-is-password-encoded",
        "word-blacklist",
        "gpt-blacklist",
        "gandalf",
        "gandalf-the-white",
        "adventure-1",
        "adventure-2",
    )

    def __init__(self, level: str = "baseline", timeout: int = 60) -> None:
        if level not in self.LEVELS:
            raise ValueError(f"unknown gandalf level: {level}")
        self.level = level
        self.timeout = timeout
        self.agent = ToolCallLog()

    def send(self, messages: list[dict[str, str]]) -> str:
        prompt = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        body = urllib.parse.urlencode(
            {"defender": self.level, "prompt": prompt}
        ).encode()
        req = urllib.request.Request(
            self.API_URL, data=body, headers={"User-Agent": _BROWSER_UA}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode())
        answer = payload.get("answer")
        if not isinstance(answer, str):
            raise RuntimeError(f"unexpected gandalf response: {payload!r}"[:300])
        return answer


class PromptAirlinesAdapter(TargetAdapter):
    """Wiz Prompt Airlines CTF chatbot.

    Holds a session cookie (from GET /) and POSTs ``{"prompt": ...}`` to
    ``/chat``. The reply's ``content`` field is HTML — tags are stripped.
    """

    BASE_URL = "https://promptairlines.com"

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.agent = ToolCallLog()
        jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(jar)
        )
        # Establish the session cookie first.
        self._opener.open(
            urllib.request.Request(
                self.BASE_URL + "/", headers={"User-Agent": _BROWSER_UA}
            ),
            timeout=self.timeout,
        )

    @staticmethod
    def _strip_html(html: str) -> str:
        text = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", text).strip()

    def send(self, messages: list[dict[str, str]]) -> str:
        prompt = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        req = urllib.request.Request(
            self.BASE_URL + "/chat",
            data=json.dumps({"prompt": prompt}).encode(),
            headers={"Content-Type": "application/json", "User-Agent": _BROWSER_UA},
        )
        with self._opener.open(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode())
        content = payload.get("content")
        if not isinstance(content, str):
            raise RuntimeError(f"unexpected promptairlines response: {payload!r}"[:300])
        return self._strip_html(content)
