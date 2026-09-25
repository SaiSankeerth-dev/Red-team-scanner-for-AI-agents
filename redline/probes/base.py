"""Probe interface: the contract every attack module implements."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

Verdict = Literal["pass", "partial", "fail"]
# pass    -> target blocked the attack
# partial -> target leaked something minor / refused inconsistently
# fail    -> attack succeeded

SEVERITIES = ("low", "medium", "high", "critical")


@dataclass
class Attempt:
    """One attack attempt against a target."""

    probe_name: str
    messages: list[dict[str, str]]  # conversation sent to the target
    response: str = ""
    verdict: Verdict | None = None
    notes: str = ""
    metadata: dict = field(default_factory=dict)


class Probe(ABC):
    """Base class for all attack probes."""

    name: str = "base"
    description: str = ""
    severity: str = "medium"  # one of SEVERITIES

    @abstractmethod
    def generate_attempts(self) -> list[Attempt]:
        """Build the attack conversation(s) for this probe."""
        ...

    def run(self, target, attempt: Attempt) -> Attempt:
        """Execute one attempt against a target adapter and score it."""
        attempt.response = target.send(attempt.messages)
        attempt.verdict = self.detect_success(attempt)
        return attempt

    @abstractmethod
    def detect_success(self, attempt: Attempt) -> Verdict:
        """Decide whether the attack worked, from the target's response."""
        ...
