"""Scaffold smoke test: the Probe/TargetAdapter contract works end to end."""
from redline.adapters.base import TargetAdapter
from redline.probes.base import Attempt, Probe


class DummyProbe(Probe):
    name = "dummy"
    description = "scaffold check"

    def generate_attempts(self) -> list[Attempt]:
        return [
            Attempt(
                probe_name=self.name,
                messages=[{"role": "user", "content": "hi"}],
            )
        ]

    def detect_success(self, attempt: Attempt):
        return "pass"


class EchoTarget(TargetAdapter):
    def send(self, messages: list[dict[str, str]]) -> str:
        return "echo"


def test_probe_run_marks_verdict():
    probe = DummyProbe()
    attempt = probe.generate_attempts()[0]
    out = probe.run(EchoTarget(), attempt)
    assert out.verdict == "pass"
    assert out.response == "echo"
