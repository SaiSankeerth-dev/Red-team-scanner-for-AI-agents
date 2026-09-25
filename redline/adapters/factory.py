"""Build a target adapter from a kind + config dict (shared by CLI and API)."""
from __future__ import annotations

import os

from .http import HTTPTargetAdapter
from .local import LocalAgentAdapter
from .openai_compat import OpenAICompatAdapter


def build_adapter(kind: str, config: dict):
    """Return ``(adapter, display_name)``. Raises ValueError on bad config.

    kind: "local" | "openai" | "http"
    """
    kind = (kind or "local").lower()
    if kind == "local":
        from redline.demo import DEMO_TARGETS

        name = config.get("target", "vulnerable")
        if name not in DEMO_TARGETS:
            raise ValueError(
                f"unknown local target: {name} (try: {', '.join(DEMO_TARGETS)})"
            )
        return LocalAgentAdapter(DEMO_TARGETS[name]()), name
    if kind == "openai":
        api_key = (
            config.get("api_key")
            or os.environ.get("TARGET_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        if not api_key:
            raise ValueError(
                "openai adapter needs an api_key "
                "(config, --api-key, or OPENAI_API_KEY / TARGET_API_KEY env)"
            )
        model = config.get("model") or "gpt-4o-mini"
        base_url = (
            config.get("base_url")
            or os.environ.get("OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        )
        adapter = OpenAICompatAdapter(
            base_url=base_url,
            api_key=api_key,
            model=model,
            system_prompt=config.get("system_prompt"),
        )
        return adapter, f"openai:{model}"
    if kind == "http":
        url = config.get("url")
        if not url:
            raise ValueError("http adapter needs a url (config or --http-url)")
        adapter = HTTPTargetAdapter(
            url,
            response_path=config.get("response_path", "response"),
            headers=config.get("headers") or {},
        )
        return adapter, url
    raise ValueError(f"unknown adapter kind: {kind} (try: local, openai, http)")
