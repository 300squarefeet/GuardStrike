from guardstrike.core.chains import render_attack_chains
from guardstrike.core.memory import Finding


def _f(**kw):
    base = dict(
        id="1",
        severity="critical",
        title="SSRF in proxy",
        description="d",
        evidence="e",
        tool="t",
        target="example.com",
        timestamp="now",
    )
    base.update(kw)
    return Finding(**base)


def test_reporter_markdown_includes_chain_section_when_present():
    # The reporter's markdown assembly must include the rendered chains block.
    from guardstrike.core.reporter_agent import ReporterAgent

    section = render_attack_chains([_f()])
    assert "## Attack Chains" in section

    # Assemble a report body directly via the helper and assert the section is embedded.
    r = ReporterAgent.__new__(ReporterAgent)
    from guardstrike.core.memory import PentestMemory

    r.memory = PentestMemory("example.com")
    r.memory.add_finding(_f())
    body = r._assemble_markdown_report(
        exec_summary="s",
        technical="t",
        remediation="r",
        ai_trace="a",
        attack_chains=render_attack_chains(r.memory.findings),
    )
    assert "## Attack Chains" in body and "SSRF → Cloud Metadata" in body


def test_reporter_markdown_omits_chain_section_when_absent():
    from guardstrike.core.memory import PentestMemory
    from guardstrike.core.reporter_agent import ReporterAgent

    r = ReporterAgent.__new__(ReporterAgent)
    r.memory = PentestMemory("example.com")
    r.memory.add_finding(_f(title="Missing header", severity="low"))
    body = r._assemble_markdown_report(
        exec_summary="s",
        technical="t",
        remediation="r",
        ai_trace="a",
        attack_chains=render_attack_chains(r.memory.findings),
    )
    assert "## Attack Chains" not in body
