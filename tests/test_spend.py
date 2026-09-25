"""Spend tracking: cost logging, monthly totals, budget cap."""
import json
import os

import pytest

from redline.judge.spend import (
    BudgetExceeded,
    check_budget,
    estimate_cost_usd,
    log_spend,
    month_spent_usd,
)


@pytest.fixture
def spend_env(tmp_path, monkeypatch):
    p = tmp_path / "spend.jsonl"
    monkeypatch.setenv("REDLINE_SPEND_FILE", str(p))
    monkeypatch.setenv("REDLINE_MONTHLY_BUDGET_USD", "10")
    return p


def test_estimate_cost_math():
    # gpt-4o-mini: $0.15 / $0.60 per 1M
    cost = estimate_cost_usd("gpt-4o-mini", 1_000_000, 1_000_000)
    assert cost == pytest.approx(0.75)


def test_log_and_month_total(spend_env):
    log_spend("gpt-4o-mini", "direct-injection", "x" * 4000, "y" * 400,
              usage={"prompt_tokens": 1000, "completion_tokens": 100})
    log_spend("gpt-4o-mini", "jailbreak", "x" * 4000, "y" * 400,
              usage={"prompt_tokens": 1000, "completion_tokens": 100})
    total = month_spent_usd()
    assert total == pytest.approx(2 * (1000 / 1e6 * 0.15 + 100 / 1e6 * 0.60))
    # records are valid JSONL with a month key
    lines = spend_env.read_text().strip().split("\n")
    assert len(lines) == 2
    assert all(json.loads(line)["month"] for line in lines)


def test_log_spend_estimates_without_usage(spend_env):
    rec = log_spend("some-unknown-model", "p", "abcd" * 100, "wxyz")
    assert rec["estimated"] is True
    assert rec["prompt_tokens"] == 100  # 400 chars / 4


def test_budget_blocks_when_exceeded(spend_env, monkeypatch):
    monkeypatch.setenv("REDLINE_MONTHLY_BUDGET_USD", "0.000001")
    log_spend("gpt-4o", "p", "x", "y", usage={"prompt_tokens": 10_000_000,
                                              "completion_tokens": 1_000_000})
    with pytest.raises(BudgetExceeded):
        check_budget()


def test_budget_ok_when_under(spend_env):
    check_budget()  # should not raise
