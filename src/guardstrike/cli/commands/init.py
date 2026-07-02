"""
guardstrike init - Initialize GuardStrike configuration
"""

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def init_command(
    config_dir: Path = typer.Option(
        Path.home() / ".guardstrike", "--config-dir", "-c", help="Configuration directory"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing configuration"),
):
    """
    Initialize GuardStrike configuration

    Creates configuration files and sets up the environment.
    """
    console.print("[bold cyan]🔧 Initializing GuardStrike...[/bold cyan]\n")

    # Create config directory
    config_dir.mkdir(parents=True, exist_ok=True)

    # Copy default config
    config_file = config_dir / "guardstrike.yaml"
    env_file = config_dir / ".env"

    if config_file.exists() and not force:
        if not Confirm.ask(f"Config file already exists at {config_file}. Overwrite?"):
            console.print("[yellow]Skipping configuration file[/yellow]")
        else:
            _copy_default_config(config_file)
    else:
        _copy_default_config(config_file)

    # Create .env file
    if not env_file.exists() or force:
        console.print("\n[bold]API Key Setup[/bold]")
        api_key = Prompt.ask("Enter your Google Gemini API key", password=True)

        with open(env_file, "w") as f:
            f.write(f"GOOGLE_API_KEY={api_key}\n")

        console.print(f"[green]✓[/green] Created environment file at {env_file}")

    # Create reports directory
    reports_dir = Path("./reports")
    reports_dir.mkdir(exist_ok=True)
    console.print(f"[green]✓[/green] Created reports directory at {reports_dir}")

    # Create logs directory
    logs_dir = Path("./logs")
    logs_dir.mkdir(exist_ok=True)
    console.print(f"[green]✓[/green] Created logs directory at {logs_dir}")

    console.print("\n[bold green]✓ GuardStrike initialized successfully![/bold green]")
    console.print(f"\nConfiguration directory: [cyan]{config_dir}[/cyan]")
    console.print("Next steps:")
    console.print(f"  1. Edit {config_file} to customize settings")
    console.print("  2. Run 'guardstrike scan --target example.com' to start scanning")


def _copy_default_config(dest: Path):
    """Copy default configuration file"""
    from guardstrike.utils.resources import default_config_path

    template_config = default_config_path()
    if template_config.exists():
        shutil.copy2(template_config, dest)
        console.print(f"[green]✓[/green] Created configuration file at {dest}")
    else:
        console.print(
            f"[yellow]⚠[/yellow] Template config not found at {template_config}, using fallback"
        )
        default_config = """# GuardStrike Configuration
ai:
  provider: gemini
  model: gemini-2.5-pro
  temperature: 0.2

pentest:
  safe_mode: true
  require_confirmation: true
  max_parallel_tools: 3

output:
  format: markdown
  save_path: ./reports
  verbosity: normal

scope:
  blacklist:
    - 127.0.0.0/8
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16
"""

        with open(dest, "w") as f:
            f.write(default_config)

        console.print(f"[green]✓[/green] Created configuration file at {dest}")
