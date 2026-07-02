import yaml
from typer.testing import CliRunner

from guardstrike.cli.commands.config_cmd import config_app
from guardstrike.cli.main import app

runner = CliRunner()


def _cfg(tmp_path, data):
    p = tmp_path / "guardstrike.yaml"
    p.write_text(yaml.safe_dump(data))
    return p


def test_config_show_masks_secret(tmp_path):
    cfg = _cfg(tmp_path, {"ai": {"api_key": "sk-SECRET"}, "output": {"save_path": "./reports"}})
    result = runner.invoke(config_app, ["show", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "***" in result.output
    assert "sk-SECRET" not in result.output
    assert "save_path" in result.output


def test_completion_flag_in_help():
    result = runner.invoke(app, ["--help"])
    assert "--install-completion" in result.output


def test_new_subapps_no_banner():
    for args in (["tools", "--help"], ["config", "show", "--help"]):
        result = runner.invoke(app, args)
        assert "zakirkun/guardstrike" not in result.output


def test_config_show_does_not_crash_on_bracket_values(tmp_path):
    # A config value containing rich-markup-like brackets must not crash config show.
    cfg = _cfg(tmp_path, {"pentest": {"note": "[bold]run[/bold] carefully"}})
    result = runner.invoke(config_app, ["show", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "carefully" in result.output
