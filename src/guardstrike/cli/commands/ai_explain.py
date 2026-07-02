"""
guardstrike ai explain - Explain AI decisions
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def explain_command(
    session_id: str = typer.Option(None, "--session", "-s", help="Session ID to explain"),
    last: bool = typer.Option(False, "--last", "-l", help="Explain last AI decision"),
    all: bool = typer.Option(False, "--all", "-a", help="Show all AI decisions"),
    format: str = typer.Option("table", "--format", "-f", help="Output format (table, json)"),
    config_file: str = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Configuration file path"
    ),
):
    """
    Explain AI decisions and reasoning

    Shows the decision-making process of GuardStrike's AI agents,
    including what actions were taken and why.
    """
    console.print("[bold cyan]🤖 AI Decision Explanation[/bold cyan]\n")

    if not session_id and not last:
        console.print("[yellow]Please specify --session <id> or use --last[/yellow]")
        console.print("[dim]Use --last for the most recent session.[/dim]")
        raise typer.Exit(1)

    from guardstrike.utils.helpers import (
        list_session_ids,
        load_config,
        resolve_reports_dir,
        resolve_session_path,
    )

    config = load_config(config_file)

    # Load session data (path from config output.save_path)
    if session_id:
        session_file = resolve_session_path(config, session_id)
    else:
        session_file = _find_latest_session(resolve_reports_dir(config))

    if not session_file or not session_file.exists():
        console.print(f"[red]Session file not found:[/red] {session_file}", soft_wrap=True)
        ids = list_session_ids(config)
        if ids:
            console.print(f"Available sessions: [cyan]{', '.join(ids)}[/cyan]")
        else:
            console.print(
                f"[dim]No sessions in {resolve_reports_dir(config)}. "
                f"Run a workflow first: guardstrike workflow run --name <name> --target <target>[/dim]"
            )
        raise typer.Exit(1)

    # Load and display decisions
    with open(session_file) as f:
        session = json.load(f)

    ai_decisions = session.get("ai_decisions", [])

    if not ai_decisions:
        console.print("[yellow]No AI decisions found in this session[/yellow]")
        return

    if format == "json":
        console.print_json(data=ai_decisions)
    else:
        _display_decisions_table(ai_decisions, all=all)


def _find_latest_session(reports_dir: Path) -> Path | None:
    """Find the most recent session file in the given reports dir."""
    if not reports_dir.is_dir():
        return None
    session_files = list(reports_dir.glob("session_*.json"))
    if not session_files:
        return None
    return max(session_files, key=lambda p: p.stat().st_mtime)


def _display_decisions_table(decisions: list, all: bool = False):
    """Display AI decisions in a rich table"""
    table = Table(title="AI Decisions")
    table.add_column("Agent", style="cyan")
    table.add_column("Decision", style="green")
    table.add_column("Reasoning", style="white")
    table.add_column("Time", style="yellow")

    # Show only last decision or all
    display_decisions = decisions if all else decisions[-1:]

    for d in display_decisions:
        agent = d.get("agent", "Unknown")
        decision = d.get("decision", "")[:50]
        reasoning = d.get("reasoning", "")[:100]
        timestamp = d.get("timestamp", "")[:19]

        table.add_row(agent, decision, reasoning + "...", timestamp)

    console.print(table)

    # Show detailed panel for last decision
    if not all and decisions:
        last_decision = decisions[-1]

        detail = f"""[bold]Agent:[/bold] {last_decision.get('agent')}
[bold]Decision:[/bold] {last_decision.get('decision')}

[bold]Full Reasoning:[/bold]
{last_decision.get('reasoning')}
"""

        console.print(Panel(detail, title="Latest AI Decision", border_style="cyan"))

        if len(decisions) > 1:
            console.print(
                f"\n[dim]Showing 1 of {len(decisions)} decisions. Use --all to see all.[/dim]"
            )
