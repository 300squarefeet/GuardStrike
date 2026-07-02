from guardstrike.core.chains import detect_chains, render_attack_chains
from guardstrike.core.memory import Finding


def _f(**kw):
    base = dict(
        id="1",
        severity="high",
        title="",
        description="",
        evidence="e",
        tool="t",
        target="example.com",
        timestamp="now",
    )
    base.update(kw)
    return Finding(**base)


def test_ssrf_fires_by_keyword_and_by_cwe():
    by_kw = detect_chains([_f(id="a", title="SSRF in image proxy")])
    assert any(c.name == "SSRF → Cloud Metadata" for c in by_kw)
    by_cwe = detect_chains([_f(id="b", title="Blind request forwarding", cwe="CWE-918")])
    assert any(c.name == "SSRF → Cloud Metadata" for c in by_cwe)


def test_no_match_returns_empty():
    assert detect_chains([_f(title="Missing security header")]) == []


def test_multi_component_and_requires_both():
    idor_only = detect_chains([_f(id="i", title="IDOR on /orders")])
    assert not any(c.name.startswith("IDOR") for c in idor_only)
    both = detect_chains(
        [
            _f(id="i", title="IDOR on /orders"),
            _f(id="j", title="Broken access control on admin panel"),
        ]
    )
    chain = next(c for c in both if c.name.startswith("IDOR"))
    assert chain.finding_ids == ["i", "j"]  # order preserved (union order), not just membership


def test_per_target_scoping():
    chains = detect_chains(
        [
            _f(id="i", title="IDOR on /orders", target="a.com"),
            _f(id="j", title="Broken access control", target="b.com"),
        ]
    )
    assert not any(c.name.startswith("IDOR") for c in chains)  # split across targets


def test_dedup_and_sorted_by_severity():
    findings = [_f(id="s", title="SSRF here"), _f(id="x", title="Reflected XSS")]
    chains = detect_chains(findings)
    names = [c.name for c in chains]
    assert names == sorted(set(names), key=lambda n: names.index(n))  # no dup
    # critical SSRF sorts before high XSS
    assert chains[0].name == "SSRF → Cloud Metadata"


def test_render_empty_and_nonempty():
    assert render_attack_chains([_f(title="nothing")]) == ""
    md = render_attack_chains([_f(id="s", title="SSRF in proxy")])
    assert "## Attack Chains" in md
    assert "SSRF → Cloud Metadata" in md and "Cloud credential theft" in md
