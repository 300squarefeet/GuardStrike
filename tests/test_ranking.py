from guardstrike.core.chains import AttackChain
from guardstrike.core.memory import Finding
from guardstrike.core.ranking import (
    finding_priority_key,
    priority_rationale,
    rank_findings,
    render_prioritized_findings,
)


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


def _chain(ids, name="SSRF → Cloud Metadata"):
    return AttackChain(
        name=name, technique="x", severity="critical", finding_ids=list(ids), rationale="r"
    )


def test_severity_dominates():
    hi = _f(id="a", severity="high")
    lo = _f(id="b", severity="low", cvss_score=9.9)  # high CVSS must not beat severity
    assert rank_findings([lo, hi], [])[0].id == "a"


def test_chain_membership_breaks_ties_within_severity():
    a = _f(id="a", severity="high")
    b = _f(id="b", severity="high")
    ranked = rank_findings([a, b], [_chain(["b"])])
    assert ranked[0].id == "b"  # b is in a chain, a is not


def test_cvss_breaks_ties():
    a = _f(id="a", severity="high", cvss_score=5.0)
    b = _f(id="b", severity="high", cvss_score=8.0)
    assert rank_findings([a, b], [])[0].id == "b"


def test_corroboration_breaks_ties():
    a = _f(id="a", severity="high", cvss_score=7.0)
    b = _f(id="b", severity="high", cvss_score=7.0, merged_from=["nmap:1"])  # dup_count=2
    assert rank_findings([a, b], [])[0].id == "b"


def test_stable_on_full_tie():
    a = _f(id="a", severity="medium")
    b = _f(id="b", severity="medium")
    ranked = rank_findings([a, b], [])
    assert [x.id for x in ranked] == ["a", "b"]  # input order preserved


def test_rank_findings_does_not_mutate_input():
    a = _f(id="a", severity="low")
    b = _f(id="b", severity="critical")
    original = [a, b]
    rank_findings(original, [])
    assert [x.id for x in original] == ["a", "b"]  # untouched


def test_priority_rationale_content():
    f = _f(id="a", severity="critical", merged_from=["nmap:1"])  # dup_count=2
    lookup = {"a": ["SSRF → Cloud Metadata"]}
    r = priority_rationale(f, lookup)
    assert "critical" in r
    assert "SSRF → Cloud Metadata" in r
    assert "corroborated by 2" in r
    # non-chain, single-tool finding: only severity
    plain = priority_rationale(_f(id="z", severity="low"), {})
    assert plain == "low"


def test_render_empty_and_table():
    assert render_prioritized_findings([], []) == ""
    md = render_prioritized_findings([_f(id="a", severity="critical", title="SQLi | bypass")], [])
    assert "## Prioritized Findings" in md
    assert "| # | Finding | Severity | Why prioritized |" in md
    assert "| 1 |" in md
    assert "SQLi \\| bypass" in md  # pipe escaped


def test_key_shape():
    k = finding_priority_key(_f(id="a", severity="high", cvss_score=7.5), {"a"})
    assert k == (3, 1, 7.5, 1)
