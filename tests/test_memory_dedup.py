from dataclasses import asdict

from guardstrike.core.memory import Finding, PentestMemory


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


def test_merged_from_defaults_empty_and_duplicate_count_one():
    f = _f()
    assert f.merged_from == []
    assert f.duplicate_count == 1


def test_duplicate_count_tracks_merged_from():
    f = _f(merged_from=["nuclei:nuclei_1", "nikto:nikto_2"])
    assert f.duplicate_count == 3


def test_finding_roundtrips_via_asdict_and_kwargs():
    f = _f(merged_from=["nuclei:nuclei_1"])
    d = asdict(f)
    assert d["merged_from"] == ["nuclei:nuclei_1"]
    assert "duplicate_count" not in d  # property, not a field
    f2 = Finding(**d)
    assert f2.merged_from == ["nuclei:nuclei_1"]


def test_old_session_dict_without_merged_from_loads():
    d = asdict(_f())
    d.pop("merged_from")  # simulate a pre-SP4a session file
    f = Finding(**d)
    assert f.merged_from == []


def _mf(**kw):
    from guardstrike.core.memory import Finding

    base = dict(
        id="x",
        severity="high",
        title="SQL Injection",
        description="d",
        evidence="e",
        tool="sqlmap",
        target="example.com",
        timestamp="now",
    )
    base.update(kw)
    return Finding(**base)


def test_add_finding_merges_duplicate():
    m = PentestMemory("example.com")
    m.add_finding(_mf(tool="sqlmap", execution_id="sqlmap_1", severity="high"))
    m.add_finding(_mf(tool="nuclei", execution_id="nuclei_2", severity="critical"))
    assert len(m.findings) == 1
    f = m.findings[0]
    assert f.duplicate_count == 2
    assert f.severity == "critical"
    assert f.merged_from == ["nuclei:nuclei_2"]
    assert f.execution_id == "sqlmap_1"  # first-seen primary keeps its link


def test_add_finding_keeps_distinct_findings():
    m = PentestMemory("example.com")
    m.add_finding(_mf(title="SQL Injection"))
    m.add_finding(_mf(title="XSS"))
    m.add_finding(_mf(title="SQL Injection", target="other.com"))
    assert len(m.findings) == 3


def test_session_roundtrip_preserves_merged_from(tmp_path):
    m = PentestMemory("example.com")
    m.add_finding(_mf(tool="a", execution_id="a1"))
    m.add_finding(_mf(tool="b", execution_id="b2"))
    path = tmp_path / "session.json"
    m.save_state(path)
    m2 = PentestMemory("placeholder")
    assert m2.load_state(path) is True
    assert len(m2.findings) == 1
    assert m2.findings[0].merged_from == ["b:b2"]
