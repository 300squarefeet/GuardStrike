"""`guardstrike tools` — discover the available security tools."""

from __future__ import annotations

import shutil

import typer
from rich.console import Console
from rich.table import Table

console = Console()
tools_app = typer.Typer(help="Discover available security tools.")


def _registry() -> dict[str, str]:
    from guardstrike.core.tool_agent import get_tool_registry

    return get_tool_registry()


def _risk(name: str) -> str:
    from guardstrike.core.tool_agent import TOOL_RISK_CLASS

    return TOOL_RISK_CLASS.get(name, "active")


@tools_app.command("list")
def list_tools() -> None:
    """List all registered security tools (category, install status, risk)."""
    from guardstrike.core.tool_meta import tool_summary

    reg = _registry()
    table = Table(title="Registered Security Tools")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Installed", justify="center")
    table.add_column("Risk", style="yellow")

    installed = 0
    for name in sorted(reg):
        present = shutil.which(name) is not None
        installed += present
        mark = "[green]✓[/green]" if present else "[red]✗[/red]"
        table.add_row(name, tool_summary(name)["category"], mark, _risk(name))

    console.print(table)
    console.print(f"[dim]{len(reg)} tools registered, {installed} installed on PATH.[/dim]")


@tools_app.command("info")
def tool_info(name: str = typer.Argument(..., help="Tool name (see `tools list`).")) -> None:
    """Show details for a single tool."""
    from guardstrike.core.tool_meta import tool_summary

    reg = _registry()
    if name not in reg:
        console.print(f"[red]Unknown tool:[/red] {name}")
        sample = ", ".join(sorted(reg)[:12])
        console.print(
            f"[dim]Known tools include: {sample}, … (see `guardstrike tools list`).[/dim]"
        )
        raise typer.Exit(1)

    summary = tool_summary(name)
    path = shutil.which(name)
    console.print(f"[bold cyan]{name}[/bold cyan]")
    console.print(f"  Description : {summary['description'] or '(none)'}")
    console.print(f"  Category    : {summary['category']}")
    console.print(f"  Risk class  : {_risk(name)}")
    console.print(f"  Installed   : {'yes — ' + path if path else 'no (not on PATH)'}")
    console.print(f"  Registry    : {reg[name]}")
