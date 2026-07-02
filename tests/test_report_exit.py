from unittest.mock import AsyncMock, MagicMock

import yaml
from typer.testing import CliRunner

from guardstrike.cli.main import app
from guardstrike.core.memory import PentestMemory

runner = CliRunner()


def test_slack_without_webhook_exits_cleanly(tmp_path, monkeypatch):
    reports = tmp_path / "r"
    reports.mkdir()
    PentestMemory("example.com").save_state(reports / "session_s1.json")
    cfg = tmp_path / "guardstrike.yaml"
    cfg.write_text(yaml.safe_dump({"output": {"save_path": str(reports)}}))

    # Avoid the LLM: fake the AI client + reporter so we reach the export dispatch.
    monkeypatch.setattr("guardstrike.ai.gemini_client.GeminiClient", lambda *a, **k: MagicMock())

    class _Reporter:
        def __init__(self, *a, **k):
            pass

        execute = AsyncMock(return_value={"content": "# report"})

    monkeypatch.setattr("guardstrike.core.reporter_agent.ReporterAgent", _Reporter)

    result = runner.invoke(
        app, ["report", "--session", "s1", "--config", str(cfg), "--export", "slack"]
    )
    assert result.exit_code == 1
    assert "Error generating report: 1" not in result.output  # no spurious re-print
    assert "webhook" in result.output.lower()  # the real slack message
