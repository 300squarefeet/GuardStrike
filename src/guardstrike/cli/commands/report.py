"""
guardstrike report - Generate reports
"""

from pathlib import Path

import typer
from rich.console import Console

console = Console()


_VALID_EXPORTS = {"sarif", "defectdojo", "slack"}


def report_command(
    session_id: str = typer.Option(
        ..., "--session", "-s", help="Session ID to generate report for"
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Report format (markdown, html, json)"
    ),
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
    config_file: Path = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Configuration file path"
    ),
    export: list[str] = typer.Option(
        [],
        "--export",
        "-e",
        help=f"Additional export formats (repeatable): {', '.join(sorted(_VALID_EXPORTS))}",
    ),
    slack_webhook: str = typer.Option(
        None,
        "--slack-webhook",
        envvar="GUARDSTRIKE_SLACK_WEBHOOK",
        help="Slack/Discord incoming-webhook URL — required when --export slack",
    ),
    defectdojo_url: str = typer.Option(
        None,
        "--defectdojo-url",
        help="DefectDojo base URL (overrides integrations.defectdojo.base_url)",
    ),
    defectdojo_engagement: int = typer.Option(
        None,
        "--defectdojo-engagement",
        help="DefectDojo engagement id to import into (overrides config)",
    ),
):
    """
    Generate penetration testing report

    Creates a professional report from session data. Pass ``--export sarif``
    or ``--export defectdojo`` for CI integrations; ``--export slack`` posts
    a summary to a webhook.
    """
    import asyncio

    from guardstrike.ai.gemini_client import GeminiClient
    from guardstrike.core.memory import PentestMemory
    from guardstrike.core.reporter_agent import ReporterAgent
    from guardstrike.utils.helpers import (
        list_session_ids,
        load_config,
        resolve_reports_dir,
        resolve_session_path,
    )

    console.print(f"[bold cyan]📄 Generating Report: {session_id}[/bold cyan]\n")

    # Validate export selectors up front so we fail fast.
    for fmt in export:
        if fmt.lower() not in _VALID_EXPORTS:
            console.print(
                f"[red]Unknown export format '{fmt}'. "
                f"Valid: {', '.join(sorted(_VALID_EXPORTS))}[/red]"
            )
            raise typer.Exit(1)

    # Load session (path from config output.save_path)
    config = load_config(str(config_file))
    session_file = resolve_session_path(config, session_id)
    if not session_file.exists():
        console.print(f"[red]Session not found:[/red] {session_file}", soft_wrap=True)
        ids = list_session_ids(config)
        if ids:
            console.print(f"Available sessions: [cyan]{', '.join(ids)}[/cyan]")
        else:
            console.print(
                f"[dim]No sessions in {resolve_reports_dir(config)}. "
                f"Run: guardstrike workflow run --name <name> --target <target>[/dim]"
            )
        raise typer.Exit(1)

    try:
        memory = PentestMemory(target="")
        memory.load_state(session_file)

        gemini = GeminiClient(config)
        reporter = ReporterAgent(config, gemini, memory)

        console.print(f"Generating {format} report...")
        report = asyncio.run(reporter.execute(format=format))

        if not output:
            ext = {"markdown": "md", "html": "html", "json": "json"}.get(format, "txt")
            output = resolve_reports_dir(config) / f"report_{session_id}.{ext}"

        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(report["content"])

        console.print("\n[green]✓ Report generated successfully![/green]")
        console.print(f"Output: [cyan]{output}[/cyan]")
        console.print(f"Format: [cyan]{format}[/cyan]")
        console.print(f"Findings: [cyan]{len(memory.findings)}[/cyan]")

        # ── Additional exports ────────────────────────────────────────────────
        from guardstrike.core.exporters import dispatch

        try:
            for line in dispatch.run_exports(
                memory,
                output.parent,
                session_id,
                {f.lower() for f in export},
                config=config,
                defectdojo_url=defectdojo_url,
                defectdojo_engagement=defectdojo_engagement,
                slack_webhook=slack_webhook,
            ):
                console.print(f"[green]✓ {line}[/green]")
        except ValueError as e:  # slack selected without a webhook
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise typer.Exit(1)
