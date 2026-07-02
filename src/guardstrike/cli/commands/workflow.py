"""
guardstrike workflow - Run predefined workflows
"""

import asyncio
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from guardstrike.core.workflow import WorkflowEngine
from guardstrike.utils.helpers import load_config

console = Console()


def workflow_command(
    action: str = typer.Argument(..., help="Action: 'run' or 'list'"),
    name: str = typer.Option(
        None, "--name", "-n", help="Workflow name (recon, web, network, autonomous)"
    ),
    target: str = typer.Option(None, "--target", "-t", help="Target for the workflow"),
    config_file: Path = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Configuration file path"
    ),
    model: str = typer.Option(None, "--model", "-m", help="Override AI model"),
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Override AI provider (gemini, openai, claude, openrouter, requesty)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip per-tool confirmation prompts (for unattended/CI runs).",
    ),
    resume: str = typer.Option(
        None,
        "--resume",
        "-r",
        help="Resume from a saved session ID (skips already-completed steps).",
    ),
    token_budget: int = typer.Option(
        None, "--token-budget", help="Hard cap on cumulative tokens for this run (abort at 100%)."
    ),
    max_cost_usd: float = typer.Option(
        None, "--max-cost-usd", help="Hard cap on estimated USD cost for this run."
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Disable the tool-result cache for this run."
    ),
):
    """
    Run or list penetration testing workflows

    Available workflows:
    - recon: Reconnaissance workflow
    - web: Web application pentest
    - network: Network infrastructure pentest
    - autonomous: AI-driven autonomous testing
    """
    if action == "list":
        _list_workflows()
        return

    if action == "run":
        if not name:
            console.print("[bold red]Error:[/bold red] --name is required for 'run' action")
            raise typer.Exit(1)

        if not target and not resume:
            console.print(
                "[bold red]Error:[/bold red] --target is required for 'run' action "
                "(unless --resume is used)"
            )
            raise typer.Exit(1)

        _run_workflow(
            name,
            target,
            config_file,
            model,
            provider,
            assume_yes=yes,
            resume=resume,
            token_budget=token_budget,
            max_cost_usd=max_cost_usd,
            no_cache=no_cache,
        )
    else:
        console.print(f"[bold red]Error:[/bold red] Unknown action: {action}")
        raise typer.Exit(1)


def _list_workflows():
    """List available workflows from YAML files"""
    from guardstrike.utils.resources import iter_workflow_files

    workflow_files = sorted(iter_workflow_files(), key=lambda p: p.stem)

    table = Table(title="Available Workflows")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Steps", style="yellow")

    if not workflow_files:
        console.print("[bold red]Error:[/bold red] No workflows found")
        raise typer.Exit(1)

    for workflow_file in workflow_files:
        try:
            with open(workflow_file, encoding="utf-8") as f:
                workflow_data = yaml.safe_load(f)

            name = workflow_file.stem  # Filename without extension
            description = workflow_data.get("description", "No description available")
            steps_count = len(workflow_data.get("steps", []))

            table.add_row(name, description, str(steps_count))

        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load {workflow_file.name}: {e}[/yellow]")

    console.print(table)


def _run_workflow(
    name: str,
    target: str,
    config_file: Path,
    model: str | None = None,
    provider: str | None = None,
    assume_yes: bool = False,
    resume: str | None = None,
    token_budget: int | None = None,
    max_cost_usd: float | None = None,
    no_cache: bool = False,
):
    """Run a workflow"""
    console.print(f"[bold cyan]🚀 Running {name} workflow on {target}[/bold cyan]\n")

    config = load_config(str(config_file))

    # Override provider if provided
    if provider:
        valid_providers = ["gemini", "openai", "claude", "openrouter", "requesty"]
        if provider not in valid_providers:
            console.print(
                f"[bold red]Error:[/bold red] Invalid provider '{provider}'. Must be one of: {', '.join(valid_providers)}"
            )
            raise typer.Exit(1)
        if "ai" not in config:
            config["ai"] = {}
        config["ai"]["provider"] = provider
        console.print(f"[dim]Using provider override: {provider}[/dim]")

    # Override model if provided
    if model:
        if "ai" not in config:
            config["ai"] = {}
        config["ai"]["model"] = model
        console.print(f"[dim]Using model override: {model}[/dim]")

    # Inject CLI budget overrides (CLI wins over config file)
    if token_budget is not None:
        config.setdefault("ai", {})["token_budget"] = token_budget
    if max_cost_usd is not None:
        config.setdefault("ai", {})["max_cost_usd"] = max_cost_usd
    if no_cache:
        config.setdefault("cache", {})["enabled"] = False

    try:
        engine = WorkflowEngine(config, target or "", assume_yes=assume_yes)
        engine.set_console(console)

        if resume:
            if not engine.resume_session(resume):
                console.print(f"[bold red]Error:[/bold red] Cannot resume session '{resume}'")
                raise typer.Exit(1)
            console.print(f"[dim]Resumed session: {resume}[/dim]")

        if name == "autonomous":
            results = asyncio.run(engine.run_autonomous())
        else:
            results = asyncio.run(engine.run_workflow(name))

        if results.get("status") == "stopped_budget":
            console.print(
                f"[yellow]Budget reached — workflow stopped.[/yellow] "
                f"{results.get('reason', '')} "
                f"({results.get('findings', 0)} findings saved; "
                f"re-run `guardstrike report --session {results.get('session_id')}`)"
            )
        else:
            console.print("\n[bold green]✓ Workflow completed![/bold green]")
            console.print(f"Findings: [cyan]{results['findings']}[/cyan]")
            console.print(f"Session: [cyan]{results['session_id']}[/cyan]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)
