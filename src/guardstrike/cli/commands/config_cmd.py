"""`guardstrike config` — inspect resolved configuration."""

from __future__ import annotations

import typer
import yaml
from rich.console import Console

from guardstrike.utils.helpers import load_config, mask_secrets

console = Console()
config_app = typer.Typer(help="Inspect configuration.")


@config_app.callback()
def _config_main() -> None:
    """Inspect configuration."""


@config_app.command("show")
def show(
    config: str = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Configuration file path."
    ),
) -> None:
    """Print the resolved configuration with secrets masked."""
    data = mask_secrets(load_config(config))
    # markup/highlight off: config values may contain brackets that rich would
    # otherwise treat as markup (crash) or silently restyle (misrepresent).
    console.print(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        markup=False,
        highlight=False,
    )
