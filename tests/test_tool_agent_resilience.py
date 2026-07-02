import asyncio
import logging

import pytest

from guardstrike.core.memory import PentestMemory
from guardstrike.core.tool_agent import ToolAgent
from guardstrike.core.tool_cache import ToolCache


class _ScriptedTool:
    """Returns queued results in order; records the kwargs of each call."""

    def __init__(self, results):
        self.is_available = True
        self._results = list(results)
        self.calls = []

    async def execute(self, target, stream_callback=None, **kwargs):
        self.calls.append(dict(kwargs))
        return self._results.pop(0)


def _agent(resilience=True, max_retries=2):
    cfg = {
        "cache": {"enabled": False, "dir": "/tmp/gs-sp10"},
        "tools": {
            "resilience": {
                "enabled": resilience,
                "max_retries": max_retries,
                "backoff_base": 2.0,
                "backoff_cap": 30.0,
            }
        },
        "ai": {"provider": "gemini"},
        "logging": {"enabled": False, "level": "ERROR"},
    }
    a = ToolAgent.__new__(ToolAgent)
    a.config = cfg
    a.logger = logging.getLogger("t")
    a.memory = PentestMemory("example.com")
    a.cache = ToolCache(cfg)
    return a


def _wire(monkeypatch, agent, tool):
    monkeypatch.setattr(agent, "_get_tool", lambda name: tool)
    monkeypatch.setattr("guardstrike.core.tool_agent._discover_plugin_tools", lambda: {"nmap": "x"})

    async def _nosleep(*a, **k):
        return None

    monkeypatch.setattr(asyncio, "sleep", _nosleep)


_FAIL_TIMEOUT = {
    "success": False,
    "exit_code": 124,
    "raw_output": "timed out",
    "error": "timed out",
}
_OK = {"success": True, "command": "nmap x", "parsed": {}, "raw_output": "ok", "exit_code": 0}


@pytest.mark.asyncio
async def test_recovers_after_transient_failure(monkeypatch):
    a = _agent()
    tool = _ScriptedTool([dict(_FAIL_TIMEOUT), dict(_OK)])
    _wire(monkeypatch, a, tool)
    r = await a.execute_tool("nmap", "example.com")
    assert r["success"] is True and r["recovered"] is True and r["attempts"] == 2
    assert len([t for t in a.memory.tool_executions if t.tool == "nmap"]) == 1


@pytest.mark.asyncio
async def test_non_retriable_no_retry(monkeypatch):
    a = _agent()
    tool = _ScriptedTool([{"success": False, "exit_code": 126, "raw_output": "permission denied"}])
    _wire(monkeypatch, a, tool)
    r = await a.execute_tool("nmap", "example.com")
    assert r["success"] is False and r["attempts"] == 1 and r["error_type"] == "permission"
    assert len(tool.calls) == 1


@pytest.mark.asyncio
async def test_exhausts_retries(monkeypatch):
    a = _agent(max_retries=2)
    tool = _ScriptedTool([dict(_FAIL_TIMEOUT) for _ in range(3)])
    _wire(monkeypatch, a, tool)
    r = await a.execute_tool("nmap", "example.com")
    assert r["success"] is False and r["attempts"] == 3 and r["error_type"] == "timeout"
    assert len(tool.calls) == 3
    assert [t for t in a.memory.tool_executions if t.tool == "nmap"] == []


@pytest.mark.asyncio
async def test_param_downshift_on_retry(monkeypatch):
    a = _agent()
    rl = {"success": False, "exit_code": 1, "raw_output": "429 Too Many Requests"}
    tool = _ScriptedTool([rl, dict(_OK)])
    _wire(monkeypatch, a, tool)
    await a.execute_tool("nmap", "example.com", threads=10)
    assert tool.calls[0]["threads"] == 10  # first attempt: as given
    assert tool.calls[1]["threads"] == 5  # retry: halved
    assert tool.calls[1].get("delay", 0) >= 1


@pytest.mark.asyncio
async def test_disabled_single_attempt(monkeypatch):
    a = _agent(resilience=False)
    tool = _ScriptedTool([dict(_FAIL_TIMEOUT)])
    _wire(monkeypatch, a, tool)
    r = await a.execute_tool("nmap", "example.com")
    assert r["success"] is False and r["attempts"] == 1
    assert len(tool.calls) == 1
