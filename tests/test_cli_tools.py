from typer.testing import CliRunner

from guardstrike.cli.commands.tools import tools_app

runner = CliRunner()


def test_tools_list_shows_registered_tools():
    result = runner.invoke(tools_app, ["list"])
    assert result.exit_code == 0
    assert "nmap" in result.output
    assert "Risk" in result.output or "risk" in result.output


def test_tools_info_known():
    result = runner.invoke(tools_app, ["info", "nmap"])
    assert result.exit_code == 0
    assert "Network port" in result.output  # from TOOL_META description
    assert "active" in result.output  # risk class


def test_tools_info_unknown_errors():
    result = runner.invoke(tools_app, ["info", "bogus-xyz"])
    assert result.exit_code != 0
    assert "bogus-xyz" in result.output
