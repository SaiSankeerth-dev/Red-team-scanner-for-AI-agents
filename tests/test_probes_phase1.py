"""Phase 1 acceptance: all probes flag the vulnerable agent, clear the hardened one."""
from redline.adapters.local import LocalAgentAdapter
from redline.demo import HardenedDemoAgent, VulnerableDemoAgent
from redline.probes.canary_leak import CanaryLeakProbe
from redline.probes.direct_injection import DirectInjectionProbe
from redline.probes.excessive_agency import ExcessiveAgencyProbe
from redline.probes.indirect_injection import IndirectInjectionProbe
from redline.probes.jailbreak import JailbreakProbe
from redline.probes.prompt_extraction import PromptExtractionProbe
from redline.probes.refusal_consistency import RefusalConsistencyProbe
from redline.probes.tool_exfiltration import ToolExfiltrationProbe

PROBES = [
    DirectInjectionProbe,
    PromptExtractionProbe,
    CanaryLeakProbe,
    JailbreakProbe,
    RefusalConsistencyProbe,
    IndirectInjectionProbe,
    ToolExfiltrationProbe,
    ExcessiveAgencyProbe,
]


def _verdicts(agent, probe_cls) -> set[str]:
    probe = probe_cls()
    target = LocalAgentAdapter(agent)
    return {probe.run(target, a).verdict for a in probe.generate_attempts()}


def test_all_probes_flag_vulnerable():
    for cls in PROBES:
        assert _verdicts(VulnerableDemoAgent(), cls) == {"fail"}, cls.name


def test_all_probes_clear_hardened():
    for cls in PROBES:
        assert _verdicts(HardenedDemoAgent(), cls) == {"pass"}, cls.name
