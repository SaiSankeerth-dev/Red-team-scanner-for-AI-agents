"""Local adapter: attack an in-process agent object (anything with .respond())."""
from __future__ import annotations

from .base import TargetAdapter


class LocalAgentAdapter(TargetAdapter):
    def __init__(self, agent) -> None:
        self.agent = agent

    def send(self, messages: list[dict[str, str]]) -> str:
        return self.agent.respond(messages)
