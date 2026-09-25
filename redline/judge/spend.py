"""Spend tracking for the LLM judge: per-call cost log + monthly budget cap.

The judge is the only Redline component that spends money. Every call is
logged (JSONL, one line per call) with an *estimated* cost, and
``check_budget()`` refuses new calls once the monthly cap is hit.

Env:
  REDLINE_MONTHLY_BUDGET_USD  monthly cap in USD (default 10)
  REDLINE_SPEND_FILE          where the log lives (default ~/.redline-spend.jsonl)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

# USD per 1M tokens: (input, output). Rough public pricing; estimates only.
PRICES_PER_1M = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "o4-mini": (1.10, 4.40),
}
DEFAULT_PRICE = (1.00, 4.00)  # fallback for unknown models


class BudgetExceeded(RuntimeError):
    pass


def spend_file() -> str:
    return os.environ.get(
        "REDLINE_SPEND_FILE", os.path.expanduser("~/.redline-spend.jsonl")
    )


def monthly_budget_usd() -> float:
    try:
        return float(os.environ.get("REDLINE_MONTHLY_BUDGET_USD", "10"))
    except ValueError:
        return 10.0


def _price(model: str) -> tuple[float, float]:
    return PRICES_PER_1M.get(model, DEFAULT_PRICE)


def estimate_cost_usd(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    pin, pout = _price(model)
    return prompt_tokens / 1e6 * pin + completion_tokens / 1e6 * pout


def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


def _month_key(now: datetime) -> str:
    return now.strftime("%Y-%m")


def month_spent_usd(now: datetime | None = None) -> float:
    """Total logged spend for the current calendar month."""
    now = now or datetime.now(timezone.utc)
    key = _month_key(now)
    path = spend_file()
    if not os.path.exists(path):
        return 0.0
    total = 0.0
    with open(path) as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("month") == key:
                total += float(entry.get("cost_usd", 0))
    return total


def check_budget() -> None:
    spent = month_spent_usd()
    cap = monthly_budget_usd()
    if spent >= cap:
        raise BudgetExceeded(
            f"monthly judge budget reached: ${spent:.4f} / ${cap:.2f} "
            "(raise REDLINE_MONTHLY_BUDGET_USD to continue)"
        )


def log_spend(
    model: str,
    probe_name: str,
    prompt_text: str,
    completion_text: str,
    usage: dict | None = None,
) -> dict:
    """Append one spend record; returns the record."""
    if usage and usage.get("prompt_tokens"):
        pt, ct = int(usage["prompt_tokens"]), int(usage.get("completion_tokens", 0))
        estimated = False
    else:
        pt, ct = estimate_tokens(prompt_text), estimate_tokens(completion_text)
        estimated = True
    now = datetime.now(timezone.utc)
    record = {
        "ts": now.isoformat(),
        "month": _month_key(now),
        "model": model,
        "probe": probe_name,
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "cost_usd": round(estimate_cost_usd(model, pt, ct), 6),
        "estimated": estimated,
    }
    path = spend_file()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")
    return record
