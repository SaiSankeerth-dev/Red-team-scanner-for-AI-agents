"""Target adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod


class TargetAdapter(ABC):
    """Anything Redline can attack: a local agent, an HTTP endpoint, etc."""

    @abstractmethod
    def send(self, messages: list[dict[str, str]]) -> str:
        """Send a conversation to the target agent; return its reply text."""
        ...


class ToolCallLog:
    """Stand-in ``agent`` for remote targets: exposes ``.tool_calls`` so the
    probe layer can inspect structured tool calls captured from API responses."""

    def __init__(self) -> None:
        self.tool_calls: list[dict] = []
