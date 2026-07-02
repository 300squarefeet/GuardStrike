"""
guardstrike models - List available AI models
"""

from rich.console import Console
from rich.table import Table

console = Console()


def list_models_command():
    """List available AI models across all providers"""

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

    console.print(table)
    console.print(
        "\n[dim]Set provider in config/guardstrike.yaml or use environment variables:[/dim]"
    )
    console.print(
        "[dim]  GOOGLE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY, REQUESTY_API_KEY[/dim]"
    )
