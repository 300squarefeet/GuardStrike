import pytest

from guardstrike.core.memory import PentestMemory
from guardstrike.core.tool_agent import ToolAgent


class _SpyTool:
    """A registered-tool stand-in that records whether it ran."""

    def __init__(self):
        self.is_available = True
        self.ran = False

    async def execute(self, target, stream_callback=None, **kwargs):
        self.ran = True
        return {
            "success": True,
            "command": f"nmap {target}",
            "parsed": {"p": [80]},
            "raw_output": "open 80",
            "duration": 1.0,
            "exit_code": 0,
        }


def _agent(tmp_path, enabled=True):
    cfg = {
        "cache": {"enabled": enabled, "ttl_hours": 24, "dir": str(tmp_path)},
        "ai": {"provider": "gemini"},
        "logging": {"enabled": False, "level": "ERROR"},
    }
    a = ToolAgent.__new__(ToolAgent)  # bypass BaseAgent.__init__ (no LLM)
    import logging

    from guardstrike.core.tool_cache import ToolCache

    a.config = cfg
    a.logger = logging.getLogger("t")
    a.memory = PentestMemory("example.com")
    a.cache = ToolCache(cfg)
    return a


@pytest.mark.asyncio
async def test_cache_miss_runs_tool_then_hit_skips(tmp_path, monkeypatch):
    a = _agent(tmp_path, enabled=True)
    spy = _SpyTool()
    monkeypatch.setattr(a, "_get_tool", lambda name: spy)
    monkeypatch.setattr("guardstrike.core.tool_agent._discover_plugin_tools", lambda: {"nmap": "x"})

    r1 = await a.execute_tool("nmap", "example.com", ports="80")
    assert r1["success"] and spy.ran is True and not r1.get("cached")

    spy.ran = False
    r2 = await a.execute_tool("nmap", "example.com", ports="80")
    assert r2.get("cached") is True
    assert spy.ran is False  # served from cache, tool NOT run
    assert r2["raw_output"] == "open 80"
    # ToolExecution recorded on BOTH the miss and the hit
    assert len([t for t in a.memory.tool_executions if t.tool == "nmap"]) == 2


@pytest.mark.asyncio
async def test_disabled_never_caches(tmp_path, monkeypatch):
    a = _agent(tmp_path, enabled=False)
    spy = _SpyTool()
    monkeypatch.setattr(a, "_get_tool", lambda name: spy)
    monkeypatch.setattr("guardstrike.core.tool_agent._discover_plugin_tools", lambda: {"nmap": "x"})
    await a.execute_tool("nmap", "example.com", ports="80")
    spy.ran = False
    r2 = await a.execute_tool("nmap", "example.com", ports="80")
    assert spy.ran is True and not r2.get("cached")  # ran again — no caching
    assert list(tmp_path.glob("*.json")) == []
