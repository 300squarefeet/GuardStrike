import textwrap

from typer.testing import CliRunner

from guardstrike.cli.main import app

runner = CliRunner()


def test_cache_status_and_clear(tmp_path):
    cfg_file = tmp_path / "guardstrike.yaml"
    cfg_file.write_text(textwrap.dedent(f"""\
            cache:
              enabled: true
              dir: {tmp_path / "cache"}
            """))
    result = runner.invoke(app, ["cache", "status", "--config", str(cfg_file)])
    assert result.exit_code == 0
    assert "cache" in result.output.lower()


def test_cache_clear_runs(tmp_path):
    cfg_file = tmp_path / "guardstrike.yaml"
    cfg_file.write_text(textwrap.dedent(f"""\
            cache:
              enabled: true
              dir: {tmp_path / "cache"}
            """))
    result = runner.invoke(app, ["cache", "clear", "--config", str(cfg_file)])
    assert result.exit_code == 0


def test_workflow_run_help_lists_no_cache():
    result = runner.invoke(app, ["workflow", "run", "--help"])
    assert result.exit_code == 0
    assert "no-cache" in result.output
