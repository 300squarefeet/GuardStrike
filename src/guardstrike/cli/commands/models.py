"""
guardstrike models - List available AI models
"""

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def list_models_command(
    live: bool = typer.Option(
        False,
        "--live",
        "-L",
        help="Fetch the live model list from a gateway provider (9router / antigravity / openai_compatible)",
    ),
    provider: str = typer.Option(
        "9router", "--provider", "-p", help="Gateway provider to query when --live"
    ),
    config_file: str = typer.Option(
        "config/guardstrike.yaml", "--config", "-c", help="Configuration file path"
    ),
):
    """List available AI models across all providers (or live from a gateway with --live)."""
    if live:
        _list_live_models(provider, config_file)
        return

    table = Table(title="Available AI Models")

    table.add_column("Model Name", style="cyan", no_wrap=True)
    table.add_column("Provider", style="magenta")
    table.add_column("Capabilities", style="white")

    # Gemini Models
    table.add_section()
    table.add_row("GEMINI MODELS", "", "", style="bold green")
    table.add_row("gemini-2.5-pro", "Google", "General Purpose, Extended Context")
    table.add_row("gemini-2.5-flash", "Google", "Fast, Efficient, Cost-Effective")
    table.add_row("gemini-1.5-pro", "Google", "Long Context, High Intelligence")
    table.add_row("gemini-1.5-flash", "Google", "Fast Responses, Good Quality")

    # OpenAI Models
    table.add_section()
    table.add_row("OPENAI MODELS", "", "", style="bold green")
    table.add_row("gpt-4-turbo", "OpenAI", "Advanced Reasoning, Latest GPT-4")
    table.add_row("gpt-4", "OpenAI", "High Intelligence, Reliable")
    table.add_row("gpt-3.5-turbo", "OpenAI", "Fast, Cost-Effective")

    # Claude Models
    table.add_section()
    table.add_row("CLAUDE MODELS", "", "", style="bold green")
    table.add_row("claude-opus-4-8", "Anthropic", "Maximum Capability")
    table.add_row("claude-sonnet-4-6", "Anthropic", "Best Balance (default)")
    table.add_row("claude-haiku-4-5", "Anthropic", "Fast, Efficient")

    # OpenRouter Models
    table.add_section()
    table.add_row("OPENROUTER MODELS", "", "", style="bold green")
    table.add_row("anthropic/claude-3.5-sonnet", "OpenRouter", "Claude via OpenRouter")
    table.add_row("openai/gpt-4-turbo", "OpenRouter", "GPT-4 via OpenRouter")
    table.add_row("google/gemini-pro", "OpenRouter", "Gemini via OpenRouter")

    # Requesty Models
    table.add_section()
    table.add_row("REQUESTY MODELS", "", "", style="bold green")
    table.add_row("openai/gpt-4o-mini", "Requesty", "GPT-4o mini via Requesty")
    table.add_row("openai/gpt-4o", "Requesty", "GPT-4o via Requesty")
    table.add_row("anthropic/claude-3.5-sonnet", "Requesty", "Claude via Requesty")

    # 9Router Models (local OpenAI-compatible gateway, keyless; model is pass-through)
    table.add_section()
    table.add_row("9ROUTER MODELS (via local gateway · keyless)", "", "", style="bold green")
    # Free tier (no cost)
    table.add_row("kr/claude-sonnet-4.5", "9Router", "Free · Claude Sonnet 4.5 (default)")
    table.add_row("kr/glm-5", "9Router", "Free · GLM-5")
    table.add_row("kr/MiniMax-M2.5", "9Router", "Free · MiniMax M2.5")
    table.add_row("oc/<auto>", "9Router", "Free · OpenCode auto-route")
    table.add_row("vertex/gemini-3.1-pro-preview", "9Router", "Free · Gemini 3.1 Pro")
    table.add_row("vertex/gemini-3-flash-preview", "9Router", "Free · Gemini 3 Flash")
    # Cheap tier ($0.2-$0.6 / 1M)
    table.add_row("glm/glm-5.1", "9Router", "Cheap · GLM-5.1")
    table.add_row("glm/glm-5", "9Router", "Cheap · GLM-5")
    table.add_row("glm/glm-4.7", "9Router", "Cheap · GLM-4.7")
    table.add_row("minimax/MiniMax-M2.7", "9Router", "Cheap · MiniMax M2.7")
    table.add_row("minimax/MiniMax-M2.5", "9Router", "Cheap · MiniMax M2.5")
    table.add_row("kimi/kimi-k2.5", "9Router", "Cheap · Kimi K2.5")
    table.add_row("kimi/kimi-k2.5-thinking", "9Router", "Cheap · Kimi K2.5 thinking")
    # Subscription tier (uses your Claude Code / Codex / Copilot plan)
    table.add_row("cc/claude-opus-4-7", "9Router", "Sub · Claude Opus 4.7")
    table.add_row("cc/claude-opus-4-6", "9Router", "Sub · Claude Opus 4.6")
    table.add_row("cc/claude-sonnet-4-6", "9Router", "Sub · Claude Sonnet 4.6")
    table.add_row("cc/claude-haiku-4-5-20251001", "9Router", "Sub · Claude Haiku 4.5")
    table.add_row("cx/gpt-5.5", "9Router", "Sub · GPT-5.5 (Codex)")
    table.add_row("cx/gpt-5.4", "9Router", "Sub · GPT-5.4 (Codex)")
    table.add_row("cx/gpt-5.3-codex", "9Router", "Sub · GPT-5.3 Codex")
    table.add_row("gh/gpt-5.4", "9Router", "Sub · GPT-5.4 (Copilot)")
    table.add_row("gh/claude-opus-4.7", "9Router", "Sub · Claude Opus 4.7 (Copilot)")
    table.add_row("gh/gemini-3.1-pro-preview", "9Router", "Sub · Gemini 3.1 Pro (Copilot)")

    console.print(table)
    console.print(
        "\n[dim]Set provider in config/guardstrike.yaml or use environment variables:[/dim]"
    )
    console.print(
        "[dim]  GOOGLE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY, REQUESTY_API_KEY[/dim]"
    )
    console.print(
        "[dim]Tip: `guardstrike models --live` lists ALL models from your local 9Router gateway.[/dim]"
    )


def _list_live_models(provider_name: str, config_file: str) -> None:
    """Fetch and print the full live model catalog from a gateway provider."""
    from guardstrike.ai.providers import get_provider
    from guardstrike.utils.helpers import load_config

    cfg = load_config(config_file)
    cfg = {**cfg, "ai": {**cfg.get("ai", {}), "provider": provider_name}}
    try:
        prov = get_provider(cfg)
        fetch = getattr(prov, "list_models", None)
        if fetch is None:
            console.print(
                f"[red]Provider '{provider_name}' does not support live model listing.[/red]"
            )
            raise typer.Exit(1)
        models = fetch()
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Could not reach the {provider_name} gateway:[/red] {e}")
        console.print(
            f"[dim]Start the {provider_name} gateway first "
            f"(9Router default: http://localhost:20128).[/dim]"
        )
        raise typer.Exit(1)

    table = Table(title=f"{provider_name} — live models ({len(models)})")
    table.add_column("Model ID", style="cyan")
    for m in models:
        table.add_row(m)
    console.print(table)
    console.print(f"\n[dim]Use with:[/dim] --provider {provider_name} --model <id>")
