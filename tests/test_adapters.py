"""OpenAI-compatible + HTTP target adapters, factory, and runner error handling."""
import json
from unittest.mock import patch

import pytest

from redline import cli as cli_module
from redline.adapters.base import TargetAdapter
from redline.adapters.factory import build_adapter
from redline.adapters.http import HTTPTargetAdapter
from redline.adapters.openai_compat import OpenAICompatAdapter
from redline.runner import CampaignRunner
from redline.store.db import session_scope


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _chat_payload(content="hello", tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def test_openai_send_returns_text():
    with patch("urllib.request.urlopen", return_value=FakeResp(_chat_payload("hi there"))):
        a = OpenAICompatAdapter("https://x/v1", "key", "m")
        assert a.send([{"role": "user", "content": "hi"}]) == "hi there"


def test_openai_captures_tool_calls():
    tc = [{
        "id": "1", "type": "function",
        "function": {"name": "send_email",
                     "arguments": json.dumps({"to": "x@y.z", "body": "secret"})},
    }]
    with patch("urllib.request.urlopen", return_value=FakeResp(_chat_payload("done", tc))):
        a = OpenAICompatAdapter("https://x/v1", "key", "m")
        a.send([{"role": "user", "content": "hi"}])
        assert a.agent.tool_calls == [
            {"tool": "send_email", "to": "x@y.z", "body": "secret"}
        ]


def test_openai_requires_key():
    with pytest.raises(ValueError):
        OpenAICompatAdapter("https://x/v1", "", "m")


def test_openai_bad_shape_raises():
    with patch("urllib.request.urlopen", return_value=FakeResp({"nope": 1})):
        a = OpenAICompatAdapter("https://x/v1", "key", "m")
        with pytest.raises(RuntimeError):
            a.send([{"role": "user", "content": "hi"}])


def test_http_dotted_path():
    with patch("urllib.request.urlopen",
               return_value=FakeResp({"data": {"reply": "yo"}})):
        a = HTTPTargetAdapter("https://x/hook", response_path="data.reply")
        assert a.send([{"role": "user", "content": "hi"}]) == "yo"


def test_http_missing_path_raises():
    with patch("urllib.request.urlopen", return_value=FakeResp({"nope": 1})):
        a = HTTPTargetAdapter("https://x/hook")
        with pytest.raises(RuntimeError):
            a.send([{"role": "user", "content": "hi"}])


def test_factory_local():
    adapter, name = build_adapter("local", {"target": "vulnerable"})
    assert name == "vulnerable"
    assert isinstance(adapter, TargetAdapter)


def test_factory_local_unknown():
    with pytest.raises(ValueError):
        build_adapter("local", {"target": "nope"})


def test_factory_openai_needs_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TARGET_API_KEY", raising=False)
    with pytest.raises(ValueError):
        build_adapter("openai", {})


def test_factory_openai_ok():
    adapter, name = build_adapter("openai", {"api_key": "k", "model": "m"})
    assert name == "openai:m"
    assert isinstance(adapter, OpenAICompatAdapter)


def test_factory_http_needs_url():
    with pytest.raises(ValueError):
        build_adapter("http", {})


def test_runner_records_target_errors():
    class Boom(TargetAdapter):
        agent = None

        def send(self, messages):
            raise RuntimeError("connection reset")

    with session_scope("sqlite:///:memory:") as session:
        result = CampaignRunner(session).run_campaign(
            "t", Boom(), "boom", cli_module.PACKS["basics"][:1]  # direct injection: 3 attempts
        )
        counts = result.verdict_counts()
        assert counts["partial"] == 3
        assert counts["fail"] == 0
        notes = [a.notes for _, attempts in result.by_probe for a in attempts]
        assert all("target error" in n for n in notes)
