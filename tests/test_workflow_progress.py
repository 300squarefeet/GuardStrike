from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from rich.console import Console

from guardstrike.core.workflow.engine import _progress_line


def test_progress_line_yaml_group():
    assert _progress_line(3, 12, phase="scanning", group=(2, 5)) == (
        "▸ group 2/5 · 3/12 steps · scanning"
    )


def test_progress_line_autonomous():
    assert _progress_line(4, 20, phase="analysis") == "▸ step 4/20 · analysis"


def test_progress_line_no_phase():
    assert _progress_line(1, 3, group=(1, 2)) == "▸ group 1/2 · 1/3 steps"
    assert _progress_line(1, 3) == "▸ step 1/3"


def _engine(base_config: dict[str, Any], save_path: Path):
    cfg = dict(base_config)
    cfg["output"] = {"save_path": str(save_path), "format": "markdown"}
    cfg["pentest"] = {"safe_mode": True, "require_confirmation": False}
    cfg["ai"] = {}
    with (
        patch("guardstrike.core.workflow.GeminiClient") as gem,
        patch("guardstrike.core.planner.PlannerAgent.__init__", return_value=None),
        patch("guardstrike.core.tool_agent.ToolAgent.__init__", return_value=None),
        patch("guardstrike.core.analyst_agent.AnalystAgent.__init__", return_value=None),
        patch("guardstrike.core.reporter_agent.ReporterAgent.__init__", return_value=None),
    ):
        gem.return_value = MagicMock()
        from guardstrike.core.workflow import WorkflowEngine

        return WorkflowEngine(cfg, "example.com")


def test_run_workflow_emits_progress_lines(base_config, tmp_path):
    engine = _engine(base_config, tmp_path)
    rec = Console(file=io.StringIO(), force_terminal=False, width=200)
    engine.set_console(rec)

    compiled = MagicMock()
    compiled.name = "x"
    compiled.steps = {"a": {}, "b": {}, "c": {}}
    compiled.levels = [["a", "b"], ["c"]]

    engine.loader.load_doc = MagicMock(return_value={})
    engine.scope_validator.validate_target = MagicMock(return_value=(True, ""))
    engine._execute_compiled_step = AsyncMock(return_value={})
    engine.planner.analyze_results = AsyncMock(return_value={})

    with patch("guardstrike.core.workflow_schema.compile_workflow", return_value=compiled):
        result = asyncio.run(engine.run_workflow("x"))

    out = rec.file.getvalue()
    assert "group 1/2 · 0/3 steps" in out
    assert "group 2/2 · 2/3 steps" in out
    assert "workflow complete" in out and "3 steps" in out
    assert result["status"] == "completed"


def test_run_autonomous_emits_progress_lines(base_config, tmp_path):
    engine = _engine(base_config, tmp_path)
    engine.max_steps = 3
    rec = Console(file=io.StringIO(), force_terminal=False, width=200)
    engine.set_console(rec)

    engine.scope_validator.validate_target = MagicMock(return_value=(True, ""))
    # One actionable decision, then "done".
    engine.planner.decide_next_action = AsyncMock(
        side_effect=[{"next_action": "scan"}, {"next_action": "done"}]
    )
    engine._runner.execute_ai_decision = AsyncMock(return_value=None)
    engine.planner.analyze_results = AsyncMock(return_value={})

    result = asyncio.run(engine.run_autonomous())

    out = rec.file.getvalue()
    assert "step 1/3" in out  # emitted before the executed step, not the "done" iteration
    assert "autonomous run complete" in out and "1 steps" in out
    assert result["status"] == "completed"
