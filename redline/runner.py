"""Campaign runner: executes a probe pack against a target and persists everything.

Deterministic detectors score first; the LLM judge is only consulted for
ambiguous ('partial') verdicts, which keeps API costs near zero on clean runs.
"""
from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field

from .probes.base import Attempt, Probe
from .store.models import AttemptRecord, Campaign


@dataclass
class CampaignResult:
    campaign: Campaign
    by_probe: list[tuple[Probe, list[Attempt]]] = field(default_factory=list)

    def verdict_counts(self) -> Counter:
        counts: Counter = Counter()
        for _, attempts in self.by_probe:
            counts.update(a.verdict or "partial" for a in attempts)
        return counts


class CampaignRunner:
    def __init__(self, session, judge=None) -> None:
        self.session = session
        self.judge = judge
        self.judge_calls = 0
        try:
            self.judge_max_calls = int(
                os.environ.get("REDLINE_JUDGE_MAX_CALLS_PER_CAMPAIGN", "50")
            )
        except ValueError:
            self.judge_max_calls = 50

    def run_campaign(
        self,
        name: str,
        target,
        target_name: str,
        probe_classes: list[type[Probe]],
        pack_name: str = "basics",
    ) -> CampaignResult:
        campaign = Campaign(name=name, target=target_name, pack=pack_name)
        self.session.add(campaign)
        self.session.flush()  # assign campaign.id
        self.judge_calls = 0

        result = CampaignResult(campaign=campaign)
        for cls in probe_classes:
            probe = cls()
            attempts: list[Attempt] = []
            for attempt in probe.generate_attempts():
                try:
                    out = probe.run(target, attempt)
                except Exception as e:  # target blew up — record it, don't kill the campaign
                    out = Attempt(
                        probe_name=probe.name,
                        messages=attempt.messages,
                        response="",
                        verdict="partial",
                        notes=f"target error: {e}",
                    )
                if out.verdict == "partial" and self.judge is not None:
                    from .judge.spend import BudgetExceeded

                    if self.judge_calls >= self.judge_max_calls:
                        out.notes = (
                            (out.notes + " " if out.notes else "")
                            + "[judge skipped: per-campaign call budget reached]"
                        )
                    else:
                        try:
                            verdict, rationale = self.judge.score(
                                probe.name, out.messages, out.response
                            )
                        except BudgetExceeded:
                            out.notes = (
                                (out.notes + " " if out.notes else "")
                                + "[judge skipped: monthly budget reached]"
                            )
                        else:
                            self.judge_calls += 1
                            out.verdict = verdict
                            out.notes = (
                                (out.notes + " ") if out.notes else ""
                            ) + f"[judge] {rationale}"
                attempts.append(out)
                self.session.add(
                    AttemptRecord(
                        campaign_id=campaign.id,
                        probe_name=out.probe_name,
                        messages=out.messages,
                        response=out.response,
                        verdict=out.verdict or "partial",
                        notes=out.notes,
                    )
                )
            result.by_probe.append((probe, attempts))
        self.session.flush()
        return result
