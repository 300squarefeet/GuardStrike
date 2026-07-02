"""`guardstrike cache` — inspect/clear the on-disk tool-result cache."""

from __future__ import annotations

import typer
from rich.console import Console

from guardstrike.core.tool_cache import ToolCache
from guardstrike.utils.helpers import load_config

console = Console()
cache_app = typer.Typer(help="Inspect and clear the on-disk tool-result cache.")


@cache_app.command("status")
def status(
    config: str = typer.Option("config/guardstrike.yaml", "--config", "-c", help="Config file."),
) -> None:
    """Show whether caching is enabled, its directory, and entry count."""
    c = ToolCache(load_config(config))
    console.print(
        f"tool cache: enabled={c.enabled}  ttl_hours={c.ttl_seconds / 3600:.0f}  "
        f"dir={c.dir}  entries={c.count()}"
    )


@cache_app.command("clear")
def clear(
    config: str = typer.Option("config/guardstrike.yaml", "--config", "-c", help="Config file."),
) -> None:
    """Delete all cached tool results."""
    n = ToolCache(load_config(config)).clear()
    console.print(f"Cleared {n} cache entr{'y' if n == 1 else 'ies'}.")
