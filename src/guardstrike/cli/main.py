"""
GuardStrike CLI - Main entry point
AI-Powered Penetration Testing Automation Tool
"""

import sys

import typer
from rich.console import Console

# Import command groups
from guardstrike.cli.commands import (
    ai_explain,
    analyze,
    init,
    mcp,
    models,
    recon,
    report,
    scan,
    workflow,
)
from guardstrike.cli.commands.cache import cache_app
from guardstrike.cli.commands.config_cmd import config_app
from guardstrike.cli.commands.kb import kb_app
from guardstrike.cli.commands.telemetry import telemetry_app
from guardstrike.cli.commands.tools import tools_app


def _get_version() -> str:
    """Resolve installed version from package metadata.

    Single source of truth — pyproject.toml. Avoids the previous
    banner/pyproject mismatch where the banner said "v2.0" while the
    package shipped as "0.1.0".
    """
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("guardstrike")
        except PackageNotFoundError:
            return "0.0.0+local"
    except Exception:
        return "unknown"


_VERSION = _get_version()

banner = (
    r"""
[bold red]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣠⣤⣤⣤⣤⣤⣤⠀⠀⠀[/bold red]
[bold red]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣶⡄⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣠⣾⣿⣿⣶⣦⣄⡀[/bold red]
[bold red]⠀⠀⠀⠀⠀⠀⠀⣀⣴⣾⣿⣿⣿⣿⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣤⡀[/bold red]
[bold red]⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠟⠋⠉[/bold red]     [bold cyan]  ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗ █████╗ ███╗   ██╗[/bold cyan]
[bold red]⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠟⠛⢉⣉⣉⣉⣉⣉⡉⠙⠛⠻⠿⣿⠟⠋⠀⠀⠀⠀[/bold red]    [bold cyan] ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║[/bold cyan]
[bold red]⠀⠀⢀⣤⣌⣻⣿⣿⣿⣿⣿⣿⠟⢉⣠⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⠄⠀⠀⠀⠀⠀⠀⠀[/bold red]    [bold cyan] ██║  ███╗██║   ██║███████║██████╔╝██║  ██║██║███████║██╔██╗ ██║[/bold cyan]
[bold red]⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⠟⢁⣴⠿⠛⠋⣉⣁⣀⣀⣀⣉⡉⠛⠻⢿⡿⠃⠀⠀⠀⠀⠀⠀⠀⠀[/bold red]    [bold cyan] ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║██║██╔══██║██║╚██╗██║[/bold cyan]
[bold red]⠀⢰⣿⣿⣿⣿⣿⣿⣿⠃⡴⠋⣁⣴⣾⣿⣿⣿⣿⣿⣿⣿⣿⣦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/bold red]     [bold cyan] ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝██║██║  ██║██║ ╚████║[/bold cyan]
[bold red]⠀⣼⣿⣿⣿⣿⣿⣿⠃⠜⢠⣾⣿⣿⣿⣿⣿⡿⠿⠿⠛⠛⠛⠿⠿⢿⣆⠀⠀⠀⠀⠀⠀⠀⠀[/bold red]     [bold cyan]  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝[/bold cyan]
[bold red]⠀⣿⣿⣿⣿⣿⣿⡟⠀⢰⣿⣿⣿⡿⠛⢋⣁⣤⣤⣴⣶⣶⣶⣶⣶⣤⣤⣀⣴⣾⠀⠀⠀⠀⠀⠀[/bold red]               [bold green]v"""
    + _VERSION
    + """[/bold green] [dim]- AI-Powered Penetration Testing Framework[/dim]
[bold red]⠀⢿⣿⣿⣿⣿⣿⠇⠀⣿⣿⣿⣿⠃⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀[/bold red]
[bold red]⠀⣶⣿⣿⣿⣿⣿⠀⢰⣿⣿⣿⡏⢰⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀[/bold red]    [dim]AI Providers:[/dim]
[bold red]⠀⣿⣿⣿⣿⣿⠇⠀⢸⣿⣿⣿⢀⣿⣿⣿⣿⣿⡿⠛⠋⠉⠉⠉⠛⢿⣿⣿⣿⠀⠀⠀⠀⠀⠀[/bold red]        • OpenAI GPT-4o  • Claude 3.5 Sonnet
[bold red]⠀⣿⣿⣿⣿⠏⠀⠀⢸⣿⣿⣷⣄⡙⢿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠈⢿⣿⣿⠀⠀⠀⠀⠀⠀[/bold red]        • Google Gemini 2.5 Pro  • OpenRouter
[bold red]⣸⣿⡿⠟⠁⠀⠀⠀⢸⣿⣿⣿⣿⣿⣄⠙⢿⣿⣿⣿⣿⣷⣶⣤⡄⠀⢸⣿⣿⠀⠀⠀⠀⠀⠀[/bold red]
[bold red]⠉⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣧⠈⢻⣿⣿⣿⣿⣿⣿⡇⠀⢸⣿⣿⠀⠀⠀⠀⠀⠀[/bold red]      [dim]Features:[/dim]
[bold red]⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⢿⣿⣿⣿⣿⣿⣿⡀⠀⠙⠿⠀⠀⠀⠀⠀⠀[/bold red]        • 19 Security Tools     • Smart Workflows
[bold red]⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⡀⢸⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀[/bold red]        • Evidence Capture    • Multi-Agent System
[bold red]⠀⠀⠀⠀⠀⠀⠙⠻⠿⣿⣿⣿⣿⣿⡿⠿⠛⠁⠀⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀[/bold red]
[bold red]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀[/bold red]      [italic dim]github.com/zakirkun/guardstrike[/italic dim]
[bold red]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⢿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠃⠀⠀⠀⠀⠀[/bold red]
[bold red]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠙⠛⠛⠛⠋⠉⠁⠀⠀⠀⠀⠀⠀⠀[/bold red]
"""
)

# Initialize Typer app
app = typer.Typer(
    name="guardstrike",
    help="🔐 GuardStrike - AI-Powered Penetration Testing CLI Tool",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()

# Register command groups
app.command(name="init")(init.init_command)
app.command(name="scan")(scan.scan_command)
app.command(name="recon")(recon.recon_command)
app.command(name="analyze")(analyze.analyze_command)
app.command(name="report")(report.report_command)
app.command(name="workflow")(workflow.workflow_command)
app.command(name="ai")(ai_explain.explain_command)
app.command(name="models")(models.list_models_command)
app.command(name="mcp")(mcp.serve_command)
app.add_typer(cache_app, name="cache", help="Tool-result cache maintenance.")
app.add_typer(kb_app, name="kb", help="Knowledge base maintenance.")
app.add_typer(telemetry_app, name="telemetry", help="Tool-selection telemetry (opt-in).")
app.add_typer(tools_app, name="tools", help="Discover available security tools.")
app.add_typer(config_app, name="config", help="Inspect configuration.")


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    GuardStrike - AI-Powered Penetration Testing CLI Tool

    Leverage Google Gemini AI to orchestrate intelligent penetration testing workflows.
    """
    # Banner only on the bare landing invocation — never on a subcommand.
    # `--help`/`--version` are eager options that exit before this callback runs,
    # so `invoked_subcommand is None` is the sufficient (and CliRunner-safe) gate.
    if ctx.invoked_subcommand is None:
        console.print(banner)
        console.print()
        console.print("Run [cyan]guardstrike --help[/cyan] to get started.")


def version_callback(value: bool):
    """Print version and exit"""
    if value:
        print(f"guardstrike {_VERSION}")
        raise typer.Exit()


@app.command()
def version(
    show: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    )
):
    """Show GuardStrike version"""
    print(f"guardstrike {_VERSION}")


def main():
    """Main entry point"""
    try:
        app()
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
