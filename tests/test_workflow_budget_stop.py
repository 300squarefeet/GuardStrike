"""Tests that run_workflow / run_autonomous return stopped_budget on budget exhaustion."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from guardstrike.ai.budget import CostBudgetExceeded, TokenBudgetExceeded
from guardstrike.core.workflow.engine import WorkflowEngine


def _make_engine(tmp_path):
    """Construct a WorkflowEngine with all AI deps patched out."""
    cfg = {
        "scope": {"blacklist": [], "max_targets": 100},
        "pentest": {"safe_mode": True},
        "logging": {"enabled": False, "level": "ERROR"},
        "output": {"save_path": str(tmp_path), "format": "markdown"},
    }
    with (
        patch("guardstrike.core.workflow.GeminiClient") as gem,
        patch("guardstrike.core.planner.PlannerAgent.__init__", return_value=None),
        patch("guardstrike.core.tool_agent.ToolAgent.__init__", return_value=None),
        patch("guardstrike.core.analyst_agent.AnalystAgent.__init__", return_value=None),
        patch("guardstrike.core.reporter_agent.ReporterAgent.__init__", return_value=None),
    ):
        gem.return_value = MagicMock()
        return WorkflowEngine(cfg, "example.com")


@pytest.mark.asyncio
async def test_run_workflow_returns_stopped_budget_token(tmp_path):
    """TokenBudgetExceeded raised inside run_workflow yields stopped_budget dict."""
    engine = _make_engine(tmp_path)

    # Inject a budget error at loader.load_doc — first call inside the try block.
    def _raise_budget(name):
        raise TokenBudgetExceeded("Token budget exhausted")

    engine.loader.load_doc = _raise_budget

    result = await engine.run_workflow("recon")

    assert result["status"] == "stopped_budget"
    assert "budget" in result["reason"].lower()
    assert "findings" in result
    assert "session_id" in result
    # Session file should have been saved.
    assert (tmp_path / f"session_{engine.memory.session_id}.json").exists()


@pytest.mark.asyncio
async def test_run_workflow_returns_stopped_budget_cost(tmp_path):
    """CostBudgetExceeded raised inside run_workflow also yields stopped_budget dict."""
    engine = _make_engine(tmp_path)

    def _raise_cost(name):
        raise CostBudgetExceeded("Cost budget exhausted at $5.00")

    engine.loader.load_doc = _raise_cost

    result = await engine.run_workflow("recon")

    assert result["status"] == "stopped_budget"
    assert "cost" in result["reason"].lower() or "budget" in result["reason"].lower()
    assert isinstance(result["findings"], int)


@pytest.mark.asyncio
async def test_run_autonomous_returns_stopped_budget(tmp_path):
    """TokenBudgetExceeded raised inside run_autonomous yields stopped_budget dict."""
    engine = _make_engine(tmp_path)

    # planner.decide_next_action is the first await inside run_autonomous's try block.
    async def _raise_budget():
        raise TokenBudgetExceeded("Token budget exhausted")

    engine.planner.decide_next_action = _raise_budget

    result = await engine.run_autonomous()

    assert result["status"] == "stopped_budget"
    assert "budget" in result["reason"].lower()
    assert "findings" in result
    assert "session_id" in result
