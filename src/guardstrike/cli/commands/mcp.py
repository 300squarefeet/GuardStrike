"""`guardstrike mcp` — start the MCP stdio server (optional `mcp` dependency)."""

from __future__ import annotations

import typer
from rich.console import Console

from guardstrike.utils.helpers import load_config

console = Console()


def _load_server():
    """Lazy import so `guardstrike --help` never imports the optional `mcp` pkg."""
    from guardstrike.mcp import server

    return server


def serve_command(
    config: str = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Config file path."
    ),
    provider: str = typer.Option(
        None, "--provider", "-p", help="Override ai.provider (e.g. ollama)."
    ),
) -> None:
    """Start the GuardStrike MCP server (stdio) so MCP clients (Claude Desktop/Code)
    can list/run workflows, fetch reports, and query the knowledge base."""
    try:
        server = _load_server()
    except ImportError:
        console.print(
            "[red]The MCP server needs the optional 'mcp' dependency.[/red]\n"
            r"Install it with:  [bold]pip install guardstrike\[mcp][/bold]"
        )
        raise typer.Exit(1)

    cfg = load_config(config)
    if provider:
        cfg.setdefault("ai", {})["provider"] = provider
    server.serve(cfg)
