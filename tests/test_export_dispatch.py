import json

import pytest

from guardstrike.core.exporters import defectdojo, dispatch
from guardstrike.core.memory import Finding, PentestMemory


def _mem():
    m = PentestMemory("example.com")
    m.add_finding(
        Finding(
            id="a",
            severity="high",
            title="SQLi",
            description="d",
            evidence="e",
            tool="sqlmap",
            target="example.com",
            timestamp="now",
        )
    )
    return m


def test_defectdojo_configured_posts(monkeypatch, tmp_path):
    monkeypatch.setenv("DEFECTDOJO_API_TOKEN", "tok")
    calls = {}
    monkeypatch.setattr(
        defectdojo,
        "post",
        lambda base, token, eng, doc, **kw: calls.update(args=(base, token, eng)) or 201,
    )
    cfg = {
        "integrations": {
            "defectdojo": {"enabled": True, "base_url": "https://dd/", "engagement_id": 7}
        }
    }
    lines = dispatch.run_exports(_mem(), tmp_path, "sid", {"defectdojo"}, config=cfg)
    assert calls["args"] == ("https://dd/", "tok", 7)
    assert (tmp_path / "report_sid.defectdojo.json").exists()
    assert any("HTTP 201" in ln for ln in lines)


def test_defectdojo_unconfigured_writes_json_only(monkeypatch, tmp_path):
    monkeypatch.delenv("DEFECTDOJO_API_TOKEN", raising=False)
    called = {"n": 0}
    monkeypatch.setattr(
        defectdojo, "post", lambda *a, **k: called.__setitem__("n", called["n"] + 1)
    )
    lines = dispatch.run_exports(_mem(), tmp_path, "sid", {"defectdojo"}, config={})
    assert called["n"] == 0
    assert (tmp_path / "report_sid.defectdojo.json").exists()
    assert any("set integrations.defectdojo" in ln for ln in lines)


def test_flags_override_config(monkeypatch, tmp_path):
    monkeypatch.setenv("DEFECTDOJO_API_TOKEN", "tok")
    calls = {}
    monkeypatch.setattr(
        defectdojo,
        "post",
        lambda base, token, eng, doc, **kw: calls.setdefault("args", (base, token, eng)) or 201,
    )
    cfg = {"integrations": {"defectdojo": {"base_url": None, "engagement_id": None}}}
    dispatch.run_exports(
        _mem(),
        tmp_path,
        "sid",
        {"defectdojo"},
        config=cfg,
        defectdojo_url="https://flag/",
        defectdojo_engagement=9,
    )
    assert calls["args"] == ("https://flag/", "tok", 9)


def test_sarif_writes_file(tmp_path):
    dispatch.run_exports(_mem(), tmp_path, "sid", {"sarif"}, config={})
    p = tmp_path / "report_sid.sarif"
    assert p.exists()
    doc = json.loads(p.read_text())
    assert doc["version"] == "2.1.0"


def test_slack_without_webhook_raises(tmp_path):
    with pytest.raises(ValueError):
        dispatch.run_exports(_mem(), tmp_path, "sid", {"slack"}, config={}, slack_webhook=None)


def test_defectdojo_post_error_does_not_raise(monkeypatch, tmp_path):
    monkeypatch.setenv("DEFECTDOJO_API_TOKEN", "tok")

    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(defectdojo, "post", boom)
    cfg = {
        "integrations": {
            "defectdojo": {"enabled": True, "base_url": "https://dd/", "engagement_id": 7}
        }
    }
    lines = dispatch.run_exports(_mem(), tmp_path, "sid", {"defectdojo"}, config=cfg)
    assert any("POST gagal" in ln for ln in lines)
    assert (tmp_path / "report_sid.defectdojo.json").exists()


def test_defectdojo_enabled_false_skips_post(monkeypatch, tmp_path):
    # enabled:false must block POST even with base_url+engagement+token present.
    monkeypatch.setenv("DEFECTDOJO_API_TOKEN", "tok")
    called = {"n": 0}
    monkeypatch.setattr(
        defectdojo, "post", lambda *a, **k: called.__setitem__("n", called["n"] + 1)
    )
    cfg = {
        "integrations": {
            "defectdojo": {"enabled": False, "base_url": "https://dd/", "engagement_id": 7}
        }
    }
    lines = dispatch.run_exports(_mem(), tmp_path, "sid", {"defectdojo"}, config=cfg)
    assert called["n"] == 0
    assert (tmp_path / "report_sid.defectdojo.json").exists()
    assert any("set integrations.defectdojo" in ln for ln in lines)


def test_config_without_integrations_block_is_safe(monkeypatch, tmp_path):
    # No integrations key at all → no POST, JSON still written, no crash.
    monkeypatch.delenv("DEFECTDOJO_API_TOKEN", raising=False)
    lines = dispatch.run_exports(_mem(), tmp_path, "sid", {"defectdojo"}, config={})
    assert (tmp_path / "report_sid.defectdojo.json").exists()
    assert any("set integrations.defectdojo" in ln for ln in lines)
