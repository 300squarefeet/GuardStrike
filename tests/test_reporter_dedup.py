"""Tests for the corroboration_line helper in reporter_agent."""

from guardstrike.core.memory import Finding
from guardstrike.core.reporter_agent import corroboration_line


def _f(**kw):
    base = dict(
        id="1",
        severity="high",
        title="SQLi",
        description="d",
        evidence="e",
        tool="sqlmap",
        target="example.com",
        timestamp="now",
    )
    base.update(kw)
    return Finding(**base)


def test_no_line_for_single_finding():
    assert corroboration_line(_f()) == ""


def test_line_for_merged_finding():
    line = corroboration_line(_f(merged_from=["nuclei:nuclei_2", "nikto:nikto_3"]))
    assert "3 tool executions" in line
    assert "nuclei:nuclei_2" in line and "nikto:nikto_3" in line
