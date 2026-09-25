"""Probe 1 acceptance test: flags the vulnerable agent, clears the hardened one."""
from redline.adapters.local import LocalAgentAdapter
from redline.demo import HardenedDemoAgent, VulnerableDemoAgent
from redline.probes.direct_injection import DirectInjectionProbe


def _run_all(agent) -> set[str]:
    probe = DirectInjectionProbe()
    target = LocalAgentAdapter(agent)
    return {probe.run(target, a).verdict for a in probe.generate_attempts()}


def test_flags_vulnerable_agent():
    assert _run_all(VulnerableDemoAgent()) == {"fail"}


def test_does_not_flag_hardened_agent():
    assert _run_all(HardenedDemoAgent()) == {"pass"}
