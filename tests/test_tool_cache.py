import json
import time

from guardstrike.core.tool_cache import ToolCache


def _cfg(tmp_path, enabled=True, ttl_hours=24):
    return {"cache": {"enabled": enabled, "ttl_hours": ttl_hours, "dir": str(tmp_path)}}


def test_put_get_roundtrip(tmp_path):
    c = ToolCache(_cfg(tmp_path))
    result = {"success": True, "raw_output": "open 80", "parsed": {"ports": [80]}}
    c.put("nmap", "example.com", {"ports": "80"}, result)
    got = c.get("nmap", "example.com", {"ports": "80"})
    assert got == result


def test_key_is_param_order_independent(tmp_path):
    c = ToolCache(_cfg(tmp_path))
    c.put("nmap", "t", {"a": 1, "b": 2}, {"success": True, "raw_output": "x"})
    assert c.get("nmap", "t", {"b": 2, "a": 1}) == {"success": True, "raw_output": "x"}


def test_miss_returns_none(tmp_path):
    assert ToolCache(_cfg(tmp_path)).get("nmap", "nope", {}) is None


def test_ttl_expiry(tmp_path):
    c = ToolCache(_cfg(tmp_path, ttl_hours=1))
    c.put("nmap", "t", {}, {"success": True, "raw_output": "x"})
    # rewrite stored_at to 2 hours ago
    f = next(tmp_path.glob("*.json"))
    payload = json.loads(f.read_text())
    payload["stored_at"] = time.time() - 2 * 3600
    f.write_text(json.dumps(payload))
    assert c.get("nmap", "t", {}) is None


def test_disabled_get_none_and_put_noop(tmp_path):
    c = ToolCache(_cfg(tmp_path, enabled=False))
    c.put("nmap", "t", {}, {"success": True, "raw_output": "x"})
    assert list(tmp_path.glob("*.json")) == []  # nothing written
    assert c.get("nmap", "t", {}) is None


def test_clear_and_count(tmp_path):
    c = ToolCache(_cfg(tmp_path))
    c.put("nmap", "t1", {}, {"success": True, "raw_output": "a"})
    c.put("httpx", "t2", {}, {"success": True, "raw_output": "b"})
    assert c.count() == 2
    assert c.clear() == 2
    assert c.count() == 0


def test_get_survives_corrupt_file(tmp_path):
    c = ToolCache(_cfg(tmp_path))
    c.put("nmap", "t", {}, {"success": True, "raw_output": "x"})
    next(tmp_path.glob("*.json")).write_text("{not json")
    assert c.get("nmap", "t", {}) is None  # best-effort, no raise
