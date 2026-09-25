"""OpenAI-compatible chat-completions target adapter.

Works with OpenAI and any OpenAI-compatible endpoint (vLLM, Ollama, Together,
etc.). Tool calls returned by the API are captured on ``adapter.agent.tool_calls``
(normalized to {"tool": name, **args}) so probes 7/8 can inspect them
deterministically, exactly like the local sandbox tools.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from .base import TargetAdapter, ToolCallLog


class OpenAICompatAdapter(TargetAdapter):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        timeout: int = 60,
    ) -> None:
        if not api_key:
            raise ValueError(
                "api_key is required (pass --api-key or set OPENAI_API_KEY / TARGET_API_KEY)"
            )
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.timeout = timeout
        self.agent = ToolCallLog()

    def send(self, messages: list[dict[str, str]]) -> str:
        msgs = list(messages)
        if self.system_prompt:
            msgs = [{"role": "system", "content": self.system_prompt}] + msgs
        body = {"model": self.model, "messages": msgs, "temperature": self.temperature}
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        last_error: Exception | None = None
        for attempt_no in range(2):  # one retry on transient failures
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = json.loads(resp.read().decode())
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:500]
                if e.code < 500 or attempt_no == 1:
                    raise RuntimeError(f"target API error {e.code}: {detail}")
                last_error = RuntimeError(f"target API error {e.code}: {detail}")
            except urllib.error.URLError as e:
                if attempt_no == 1:
                    raise RuntimeError(f"target unreachable: {e.reason}")
                last_error = RuntimeError(f"target unreachable: {e.reason}")
            time.sleep(1 + attempt_no)
        else:
            raise last_error or RuntimeError("target request failed")

        try:
            message = payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"unexpected API response shape: {str(payload)[:300]}")

        for tc in message.get("tool_calls") or []:
            fn = tc.get("function", {})
            name = fn.get("name", "unknown")
            raw_args = fn.get("arguments", "")
            try:
                args = json.loads(raw_args) if raw_args else {}
            except json.JSONDecodeError:
                args = {}
            call: dict = {"tool": name}
            if isinstance(args, dict):
                call.update(args)
            else:
                call["arguments"] = raw_args
            self.agent.tool_calls.append(call)

        return message.get("content") or ""
