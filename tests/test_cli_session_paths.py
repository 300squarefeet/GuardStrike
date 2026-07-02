import yaml
from typer.testing import CliRunner

from guardstrike.cli.main import app

runner = CliRunner()


def _cfg(tmp_path, reports_dir):
    p = tmp_path / "guardstrike.yaml"
    p.write_text(yaml.safe_dump({"output": {"save_path": str(reports_dir)}}))
    return p


def test_report_resolves_session_dir_from_config(tmp_path):
    reports = tmp_path / "myreports"
    reports.mkdir()
    cfg = _cfg(tmp_path, reports)
    # Session does NOT exist → the not-found path must reference the config dir, not ./reports.
    result = runner.invoke(app, ["report", "--session", "zzz", "--config", str(cfg)])
    assert result.exit_code != 0
    assert str(reports) in result.output
    assert "./reports/session_zzz.json" not in result.output


def test_report_not_found_lists_available(tmp_path):
    reports = tmp_path / "myreports"
    reports.mkdir()
    (reports / "session_a.json").write_text("{}")
    (reports / "session_b.json").write_text("{}")
    cfg = _cfg(tmp_path, reports)
    result = runner.invoke(app, ["report", "--session", "zzz", "--config", str(cfg)])
    assert result.exit_code != 0
    assert "Available sessions" in result.output
    assert "a" in result.output and "b" in result.output


def test_report_not_found_hints_when_empty(tmp_path):
    reports = tmp_path / "myreports"
    reports.mkdir()
    cfg = _cfg(tmp_path, reports)
    result = runner.invoke(app, ["report", "--session", "zzz", "--config", str(cfg)])
    assert "workflow run" in result.output


def test_ai_explain_resolves_session_dir_from_config(tmp_path):
    reports = tmp_path / "myreports"
    reports.mkdir()
    cfg = _cfg(tmp_path, reports)
    result = runner.invoke(app, ["ai", "--session", "zzz", "--config", str(cfg)])
    assert result.exit_code != 0
    assert str(reports) in result.output
