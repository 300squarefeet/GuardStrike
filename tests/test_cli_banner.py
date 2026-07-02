from typer.testing import CliRunner

from guardstrike.cli.main import app

runner = CliRunner()

BANNER_MARK = "zakirkun/guardstrike"


def test_help_has_no_banner():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert BANNER_MARK not in result.output
    assert "Commands" in result.output or "Usage" in result.output


def test_bare_invocation_shows_banner_and_hint():
    result = runner.invoke(app, [])
    assert BANNER_MARK in result.output
    assert "guardstrike --help" in result.output


def test_version_command_has_no_banner():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert BANNER_MARK not in result.output
    assert "guardstrike" in result.output  # prints "guardstrike <version>"


def test_subcommand_help_has_no_banner():
    # A subcommand's --help must not trigger the group banner.
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert BANNER_MARK not in result.output
