from typer.testing import CliRunner

from guardstrike.cli.main import app

runner = CliRunner()


def test_mcp_missing_dependency_message(monkeypatch):
    # Simulate `mcp` not installed: make importing the server raise ImportError.
    import guardstrike.cli.commands.mcp as mcp_cmd

    def _boom(*a, **k):
        raise ImportError("No module named 'mcp'")

    monkeypatch.setattr(mcp_cmd, "_load_server", _boom)
    result = runner.invoke(app, ["mcp"])
    assert result.exit_code == 1
    assert "guardstrike[mcp]" in result.output


def test_mcp_help_works():
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "MCP" in result.output or "mcp" in result.output
