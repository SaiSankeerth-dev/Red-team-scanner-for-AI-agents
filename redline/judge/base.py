"""Judge interface: LLM-as-judge with per-probe rubrics + deterministic checks."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

Verdict = Literal["pass", "partial", "fail"]


class Judge(ABC):
    """Scores a single attempt. Deterministic checks (e.g. canary matching)
    should run before/around the LLM call in concrete implementations."""

    @abstractmethod
    def score(
        self,
        probe_name: str,
        messages: list[dict[str, str]],
        response: str,
    ) -> tuple[Verdict, str]:
        """Return (verdict, rationale)."""
        ...
