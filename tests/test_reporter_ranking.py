from guardstrike.core.chains import detect_chains
from guardstrike.core.memory import Finding, PentestMemory
from guardstrike.core.ranking import render_prioritized_findings
from guardstrike.core.reporter_agent import ReporterAgent


def _f(**kw):
    base = dict(
        id="1",
        severity="high",
        title="T",
        description="d",
        evidence="e",
        tool="t",
        target="example.com",
        timestamp="now",
    )
    base.update(kw)
    return Finding(**base)


def _reporter(findings):
    r = ReporterAgent.__new__(ReporterAgent)
    r.memory = PentestMemory("example.com")
    for f in findings:
        r.memory.add_finding(f)
    return r


def test_markdown_includes_prioritized_section_when_present():
    r = _reporter([_f(id="a", severity="critical", title="SQLi")])
    chains = detect_chains(r.memory.findings)
    body = r._assemble_markdown_report(
        exec_summary="s",
        technical="t",
        remediation="rem",
        ai_trace="a",
        prioritized_findings=render_prioritized_findings(r.memory.findings, chains),
    )
    assert "## Prioritized Findings" in body
    assert "SQLi" in body


def test_markdown_omits_prioritized_section_when_no_findings():
    r = _reporter([])
    body = r._assemble_markdown_report(
        exec_summary="s",
        technical="t",
        remediation="rem",
        ai_trace="a",
        prioritized_findings=render_prioritized_findings(r.memory.findings, []),
    )
    assert "## Prioritized Findings" not in body


def test_format_findings_detailed_is_worst_first():
    # Added low-first, critical-last; formatted output must list critical before low.
    r = _reporter(
        [
            _f(id="a", severity="low", title="LOWFIND"),
            _f(id="b", severity="critical", title="CRITFIND"),
        ]
    )
    text = r._format_findings_detailed()
    assert text.index("CRITFIND") < text.index("LOWFIND")
