import asyncio
import logging

import pytest

from guardstrike.core.memory import Finding, PentestMemory
from guardstrike.core.workflow.step_runner import StepRunner


def _runner(config):
    mem = PentestMemory("example.com")
    return StepRunner(
        config,
        "example.com",
        mem,
        tool_agent=None,
        analyst=None,
        reporter=None,
        scope_validator=None,
        logger=logging.getLogger("t"),
        assume_yes=True,
        console=None,
        gemini_client=None,
    )


def test_confirm_tool_blocks_destructive_in_safe_mode():
    r = _runner({"pentest": {"safe_mode": True}})
    # impacket-secretsdump is classed destructive; safe_mode blocks it.
    assert r._confirm_tool("impacket-secretsdump", {"name": "x", "parameters": {}}) is False


def test_validate_discovered_hosts_no_crash_on_empty():
    r = _runner({"scope": {"blacklist": []}})
    r._validate_discovered_hosts("subfinder", {})  # must not raise


class _StubToolAgent:
    """Returns a successful tool result without touching the network."""

    async def execute_tool(self, tool_name, target, stream_callback=None, **kwargs):
        return {
            "success": True,
            "command": f"{tool_name} {target}",
            "raw_output": "port 80 open",
            "exit_code": 0,
            "duration": 0.01,
            "parsed": {},
        }


class _CapturingAnalyst:
    """Records the execution_id it is handed and emits a linked Finding."""

    def __init__(self, memory):
        self.memory = memory
        self.seen_execution_id = None

    async def interpret_output(self, tool, target, command, output, execution_id=None):
        self.seen_execution_id = execution_id
        finding = Finding(
            id="f1",
            severity="low",
            title="t",
            description="d",
            evidence="e",
            tool=tool,
            target=target,
            timestamp="now",
            execution_id=execution_id,
        )
        self.memory.findings.append(finding)
        return {"findings": [finding], "reasoning": ""}


@pytest.mark.asyncio
async def test_execution_id_links_finding_to_toolexecution():
    """The evidence-traceability invariant: the id minted for a tool step is
    recorded on the ToolExecution AND handed to the analyst AND carried on the
    resulting Finding — all three must be the same value. This is the contract
    the workflow.py split had to preserve; assert it directly so a future
    refactor that drops the link fails loudly."""
    mem = PentestMemory("example.com")
    analyst = _CapturingAnalyst(mem)
    runner = StepRunner(
        {"pentest": {"safe_mode": False}},
        "example.com",
        mem,
        tool_agent=_StubToolAgent(),
        analyst=analyst,
        reporter=None,
        scope_validator=None,
        logger=logging.getLogger("t"),
        assume_yes=True,
        console=None,
        gemini_client=None,
    )

    await runner.execute_step({"name": "scan", "type": "tool", "tool": "httpx", "parameters": {}})

    assert len(mem.tool_executions) == 1
    exec_id = mem.tool_executions[0].id
    assert exec_id is not None
    # the analyst was handed the same id that was recorded on the ToolExecution
    assert analyst.seen_execution_id == exec_id
    # and the emitted Finding carries it -> evidence trail intact end to end
    assert len(mem.findings) == 1
    assert mem.findings[0].execution_id == exec_id


class _InterleavingToolAgent:
    """execute_tool whose result is keyed by tool name; the 'slow' tool yields
    so a concurrent sibling runs in between — surfacing any shared-state clobber."""

    async def execute_tool(self, tool_name, target, stream_callback=None, **kwargs):
        if tool_name == "amass":
            await asyncio.sleep(0.02)  # let the fast sibling interleave
        return {
            "success": True,
            "command": f"{tool_name} {target}",
            "raw_output": f"output-of-{tool_name}",
            "exit_code": 0,
            "duration": 0.01,
            "parsed": {"who": tool_name},
        }


def _tool_runner(mem):
    return StepRunner(
        {"pentest": {"safe_mode": False}},
        "example.com",
        mem,
        tool_agent=_InterleavingToolAgent(),
        analyst=_CapturingAnalyst(mem),
        reporter=None,
        scope_validator=None,
        logger=logging.getLogger("t"),
        assume_yes=True,
        console=None,
        gemini_client=None,
    )


@pytest.mark.asyncio
async def test_execute_step_returns_its_own_tool_result():
    """execute_step must RETURN the step's result so the engine builds the
    Jinja context from the return value, not shared mutable state."""
    mem = PentestMemory("example.com")
    result = await _tool_runner(mem).execute_step(
        {"name": "s", "type": "tool", "tool": "httpx", "parameters": {}}
    )
    assert result is not None
    assert result["success"] is True
    assert result["command"] == "httpx example.com"
    assert result["parsed"] == {"who": "httpx"}


@pytest.mark.asyncio
async def test_concurrent_execute_step_results_do_not_clobber():
    """Two steps in one generation run concurrently (asyncio.gather). Each call
    must return its OWN result — the bug this guards against is a sibling step
    overwriting shared `last_step_result` / reading `tool_executions[-1]`."""
    mem = PentestMemory("example.com")
    runner = _tool_runner(mem)
    slow, fast = await asyncio.gather(
        runner.execute_step({"name": "slow", "type": "tool", "tool": "amass", "parameters": {}}),
        runner.execute_step({"name": "fast", "type": "tool", "tool": "httpx", "parameters": {}}),
    )
    assert slow["command"] == "amass example.com"
    assert slow["parsed"] == {"who": "amass"}
    assert fast["command"] == "httpx example.com"
    assert fast["parsed"] == {"who": "httpx"}
