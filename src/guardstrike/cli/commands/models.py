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
