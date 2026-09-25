"""Report scoring, HTML rendering, and PDF export."""
import os

from redline import cli as cli_module
from redline.adapters.local import LocalAgentAdapter
from redline.demo import HardenedDemoAgent, VulnerableDemoAgent
from redline.reports.generator import build_report_data, render_html, write_html_report
from redline.reports.pdf import render_pdf_bytes, write_pdf_report
from redline.runner import CampaignRunner
from redline.store.db import session_scope


def _campaign(target_name, agent):
    # fresh in-memory DB per test via unique URL
    url = f"sqlite:///:memory:"
    with session_scope(url) as session:
        runner = CampaignRunner(session)
        result = runner.run_campaign(
            "t", LocalAgentAdapter(agent()), target_name,
            cli_module.PACKS["basics"],
        )
        data = build_report_data(session, result.campaign.id)
        return data


def test_vulnerable_scores_zero():
    data = _campaign("vulnerable", VulnerableDemoAgent)
    assert data["score"] == 0
    assert data["grade"] == "F"
    assert data["counts"]["fail"] == 33
    assert len(data["findings"]) == 33
    assert all(f["remediation"] for f in data["findings"])


def test_hardened_scores_hundred():
    data = _campaign("hardened", HardenedDemoAgent)
    assert data["score"] == 100
    assert data["grade"] == "A"
    assert data["findings"] == []


def test_html_renders(tmp_path):
    data = _campaign("vulnerable", VulnerableDemoAgent)
    html = render_html(data)
    assert "<title>Redline report" in html
    assert ">0<span" in html  # score 0 rendered before the /100 span
    assert "grade-F" in html
    assert "tool-exfiltration" in html
    assert "How to fix:" in html
    path = write_html_report(data, str(tmp_path / "r.html"))
    assert os.path.getsize(path) > 5000


def test_pdf_renders(tmp_path):
    data = _campaign("vulnerable", VulnerableDemoAgent)
    raw = render_pdf_bytes(data)
    assert raw.startswith(b"%PDF")
    path = write_pdf_report(data, str(tmp_path / "r.pdf"))
    assert os.path.getsize(path) > 2000


def test_missing_campaign():
    with session_scope("sqlite:///:memory:") as session:
        try:
            build_report_data(session, 999)
        except LookupError:
            return
        raise AssertionError("expected LookupError")
