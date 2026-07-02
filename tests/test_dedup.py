from guardstrike.core.dedup import (
    finding_dedup_key,
    merge_findings,
    normalize_title,
    severity_rank,
)
from guardstrike.core.memory import Finding


def _f(**kw):
    base = dict(
        id="1",
        severity="high",
        title="SQL Injection",
        description="d",
        evidence="e",
        tool="sqlmap",
        target="Example.com",
        timestamp="now",
    )
    base.update(kw)
    return Finding(**base)


def test_normalize_title_collapses_case_and_whitespace():
    assert normalize_title("  SQL   Injection\n") == "sql injection"


def test_severity_rank_order():
    assert severity_rank("critical") > severity_rank("high") > severity_rank("medium")
    assert severity_rank("low") > severity_rank("info")
    assert severity_rank("weird") == 0


def test_dedup_key_cve_tier_ignores_title():
    a = _f(cve="CVE-2021-44228", title="Log4Shell")
    b = _f(cve="cve-2021-44228", title="totally different title")
    assert finding_dedup_key(a) == finding_dedup_key(b)


def test_dedup_key_cwe_tier_uses_title():
    a = _f(cwe="CWE-89", title="SQL Injection")
    b = _f(cwe="CWE-89", title="sql   injection")
    c = _f(cwe="CWE-89", title="XSS")
    assert finding_dedup_key(a) == finding_dedup_key(b)
    assert finding_dedup_key(a) != finding_dedup_key(c)


def test_dedup_key_title_tier_and_target_scoping():
    a = _f(title="Open Redirect")
    b = _f(title="open redirect")
    d = _f(title="Open Redirect", target="other.com")
    assert finding_dedup_key(a) == finding_dedup_key(b)
    assert finding_dedup_key(a) != finding_dedup_key(d)


def test_merge_keeps_highest_severity_and_records_contributor():
    primary = _f(severity="medium", tool="nikto", execution_id="nikto_1", cwe=None)
    dup = _f(
        severity="critical", tool="nuclei", execution_id="nuclei_2", cwe="CWE-89", cvss_score=9.8
    )
    out = merge_findings(primary, dup)
    assert out is primary
    assert out.severity == "critical"  # adopted higher severity
    assert out.cvss_score == 9.8
    assert out.cwe == "CWE-89"  # filled empty metadata
    assert out.merged_from == ["nuclei:nuclei_2"]
    assert out.execution_id == "nikto_1"  # primary's own link untouched
    assert out.duplicate_count == 2


def test_merge_does_not_overwrite_existing_metadata_or_lower_severity():
    primary = _f(severity="critical", remediation="patch it", tool="a", execution_id="a1")
    dup = _f(severity="low", remediation="different", tool="b", execution_id="b2")
    out = merge_findings(primary, dup)
    assert out.severity == "critical"  # not lowered
    assert out.remediation == "patch it"  # not overwritten
    assert out.merged_from == ["b:b2"]
