"""Campaign runner persists campaigns + attempts to the DB."""
from redline.adapters.local import LocalAgentAdapter
from redline.demo import HardenedDemoAgent, VulnerableDemoAgent
from redline.probes.direct_injection import DirectInjectionProbe
from redline.runner import CampaignRunner
from redline.store.db import session_scope
from redline.store.models import AttemptRecord, Campaign


def test_runner_persists_campaign():
    with session_scope("sqlite:///:memory:") as session:
        runner = CampaignRunner(session)
        result = runner.run_campaign(
            "t", LocalAgentAdapter(VulnerableDemoAgent()), "vulnerable",
            [DirectInjectionProbe],
        )
        assert result.campaign.id is not None
        rows = session.query(AttemptRecord).filter_by(campaign_id=result.campaign.id).all()
        assert len(rows) == 3
        assert {r.verdict for r in rows} == {"fail"}
        assert all(r.response and r.messages for r in rows)
        assert session.query(Campaign).count() == 1


def test_runner_verdict_counts():
    with session_scope("sqlite:///:memory:") as session:
        runner = CampaignRunner(session)
        result = runner.run_campaign(
            "t", LocalAgentAdapter(HardenedDemoAgent()), "hardened",
            [DirectInjectionProbe],
        )
        assert result.verdict_counts()["pass"] == 3


def test_judge_adjudicates_partials_only():
    class Judge:
        def __init__(self):
            self.calls = 0

        def score(self, probe_name, messages, response):
            self.calls += 1
            return "pass", "judge says no"

    with session_scope("sqlite:///:memory:") as session:
        runner = CampaignRunner(session, judge=Judge())
        # deterministic verdicts are fail/pass (not partial) -> judge never called
        runner.run_campaign(
            "t", LocalAgentAdapter(VulnerableDemoAgent()), "vulnerable",
            [DirectInjectionProbe],
        )
        assert runner.judge.calls == 0
