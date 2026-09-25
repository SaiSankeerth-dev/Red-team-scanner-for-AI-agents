"""Calibration harness: score the LLM judge against labeled cases.

v1 labels come from deterministic verdicts on the demo targets (unambiguous
cases) plus a few hand-labeled ambiguous ones. This measures judge *agreement*;
real calibration later needs human-labeled gray-area cases from live targets.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load_cases(path: str | None = None) -> list[dict]:
    with open(path or os.path.join(HERE, "fixtures", "labeled.json")) as f:
        return json.load(f)


def calibrate(judge, cases: list[dict]) -> dict:
    correct = 0
    mismatches = []
    for c in cases:
        verdict, _ = judge.score(c["probe"], c["messages"], c["response"])
        if verdict == c["expected"]:
            correct += 1
        else:
            mismatches.append(
                {
                    "probe": c["probe"],
                    "expected": c["expected"],
                    "got": verdict,
                    "response": c["response"],
                    "note": c.get("note", ""),
                }
            )
    total = len(cases)
    return {
        "total": total,
        "correct": correct,
        "accuracy": (correct / total) if total else 0.0,
        "mismatches": mismatches,
    }
