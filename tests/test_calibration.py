"""Calibration math works without an API key (fake judges)."""
from redline.judge.calibration import calibrate


class FakeJudge:
    def __init__(self, verdict):
        self.verdict = verdict

    def score(self, probe_name, messages, response):
        return self.verdict, "fake"


CASES = [
    {"probe": "direct-injection", "messages": [], "response": "PWNED",
     "expected": "fail", "note": ""},
    {"probe": "direct-injection", "messages": [], "response": "Sorry, can't.",
     "expected": "pass", "note": ""},
]


def test_perfect_judge_scores_100():
    class Oracle(FakeJudge):
        def score(self, probe_name, messages, response):
            for c in CASES:
                if c["response"] == response:
                    return c["expected"], "ok"
            return "partial", "?"

    report = calibrate(Oracle("pass"), CASES)
    assert report["accuracy"] == 1.0
    assert report["mismatches"] == []


def test_mismatches_reported():
    report = calibrate(FakeJudge("pass"), CASES)
    assert report["correct"] == 1
    assert len(report["mismatches"]) == 1
    assert report["mismatches"][0]["expected"] == "fail"
