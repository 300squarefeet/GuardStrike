"""
guardstrike recon - Reconnaissance command
"""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from guardstrike.core.workflow import WorkflowEngine
from guardstrike.utils.helpers import is_valid_domain, is_valid_url, load_config

console = Console()


def recon_command(
    target: str = typer.Option(
        None,
        "--target",
        "-t",
        help="Target domain/host for reconnaissance",
    ),
    domain: str = typer.Option(
        None,
        "--domain",
        "-d",
        help="[DEPRECATED] Use --target instead. Retained for backwards compatibility.",
        hidden=True,
    ),
    config_file: Path = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Configuration file path"
    ),
    save_results: bool = typer.Option(True, "--save/--no-save", help="Save results to file"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Override AI model (e.g. gemini-3-pro, gemini-3-flash, claude-sonnet-4-5)",
    ),
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Override AI provider (gemini, openai, claude, openrouter, requesty)",
    ),
):
    """
    Run reconnaissance workflow on a target domain

    Performs:
    - Subdomain enumeration
    - Port scanning
    - Service detection
    - Technology fingerprinting
    """
    # Resolve --target / --domain (legacy). --domain still works but emits a
    # deprecation note. One of the two MUST be supplied.
    if domain and not target:
        console.print("[yellow]Note:[/yellow] --domain is deprecated; please use --target instead.")
        target = domain
    if not target:
        console.print("[bold red]Error:[/bold red] --target is required")
        raise typer.Exit(1)

    console.print(f"[bold cyan]🔍 Starting Reconnaissance: {target}[/bold cyan]\n")

    # Validate target
    if not is_valid_domain(target) and not is_valid_url(target):
        console.print(f"[bold red]Error:[/bold red] Invalid domain: {target}")
        raise typer.Exit(1)

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No actual scanning will occur[/yellow]\n")
        _show_recon_plan(target)
        return

    # Load configuration
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

    # Run workflow
    try:
        # Run async workflow (engine prints determinate progress lines).
        results = asyncio.run(_run_recon_workflow(config, target))

        # Display results
        _display_results(results)

        console.print("\n[bold green]✓ Reconnaissance completed![/bold green]")
        console.print(f"Session ID: [cyan]{results['session_id']}[/cyan]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


async def _run_recon_workflow(config: dict, domain: str) -> dict:
    """Run the reconnaissance workflow"""
    engine = WorkflowEngine(config, domain)
    engine.set_console(console)
    results = await engine.run_workflow("recon")
    return results


def _show_recon_plan(domain: str):
    """Show what the recon workflow would do"""
    table = Table(title="Reconnaissance Plan")
    table.add_column("Step", style="cyan")
    table.add_column("Tool", style="green")
    table.add_column("Description", style="white")

    table.add_row("1", "Subfinder", f"Enumerate subdomains of {domain}")
    table.add_row("2", "Nmap", "Scan discovered assets for open ports")
    table.add_row("3", "httpx", "Probe HTTP services and detect technologies")
    table.add_row("4", "AI Analysis", "Analyze findings and correlate results")

    console.print(table)


def _display_results(results: dict):
    """Display reconnaissance results"""
    console.print("\n[bold]📊 Results Summary[/bold]\n")

    findings = results.get("findings", 0)
    console.print(f"Total Findings: [cyan]{findings}[/cyan]")

    if "analysis" in results:
        console.print("\n[bold]🤖 AI Analysis:[/bold]")
        console.print(results["analysis"].get("response", "No analysis available"))
