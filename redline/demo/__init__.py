"""Bundled demo victims: try Redline with zero setup, no API key needed."""

from .almost_hardened import AlmostHardenedAgent
from .eager_assistant import EagerAssistantAgent
from .hardened import HardenedDemoAgent
from .naive_rag import NaiveRAGAgent
from .vulnerable import VulnerableDemoAgent

DEMO_TARGETS = {
    "vulnerable": VulnerableDemoAgent,       # 0/100 — fails everything
    "hardened": HardenedDemoAgent,           # 100/100 — blocks everything
    "naive-rag": NaiveRAGAgent,              # ~0/100 — trusts retrieved docs
    "eager-assistant": EagerAssistantAgent,  # ~55/100 — good hygiene, leaks secrets
    "almost-hardened": AlmostHardenedAgent,  # ~85/100 — one config-file edge case
}

__all__ = [
    "DEMO_TARGETS",
    "AlmostHardenedAgent",
    "EagerAssistantAgent",
    "HardenedDemoAgent",
    "NaiveRAGAgent",
    "VulnerableDemoAgent",
]
