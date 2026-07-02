"""
AI Client for GuardStrike
Generic client that delegates to specific providers (Gemini, OpenAI, Claude, OpenRouter)
and exposes generate_with_usage() + get_token_report() for token cost tracking.
"""

from typing import Any

from guardstrike.ai.budget import BudgetTracker, CostBudgetExceeded, TokenBudgetExceeded
from guardstrike.ai.providers import get_provider_chain
from guardstrike.ai.providers.base_provider import TRANSIENT_MARKERS as _TRANSIENT_MARKERS
from guardstrike.utils.logger import get_logger

_AUTH_MARKERS = ("401", "403", "api key", "unauthorized", "authentication")
_MODEL_404_MARKERS = ("model not found", "does not exist", " 404", "not_found")


def _should_fallback(exc: BaseException) -> bool:
    """True if the next provider should be tried. Auth + budget errors return
    False (handled separately / raised). Transient or model-not-found -> True."""
    if isinstance(exc, (TokenBudgetExceeded, CostBudgetExceeded)):
        return False
    msg = str(exc).lower()
    if any(m in msg for m in _AUTH_MARKERS):
        return False
    from guardstrike.ai.providers.base_provider import BaseProvider

    if BaseProvider.default_is_retriable(exc):
        return True
    if any(m in msg for m in _TRANSIENT_MARKERS):
        return True
    return any(m in msg for m in _MODEL_404_MARKERS)


class AIClient:
    """
    Unified AI client that works with multiple providers.
    Delegates all operations to the configured provider chain (primary + fallbacks).
    Adds generate_with_usage() for token cost tracking and
    get_token_report() for report generation.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = get_logger(config)

        # Ordered provider chain (primary + fallbacks) sharing one budget.
        self.providers = get_provider_chain(config)
        self.provider = self.providers[0]  # back-compat: callers use .provider

        ai = config.get("ai", {})
        self.budget = BudgetTracker(ai.get("token_budget"), ai.get("max_cost_usd"), self.logger)
        for p in self.providers:
            p.budget = self.budget  # shared run-global tracker

        self.model_name = self.provider.get_model_name()
        names = ", ".join(p.__class__.__name__ for p in self.providers)
        self.logger.info(f"AIClient initialized with chain [{names}]: {self.model_name}")

    # ── Chain runners ─────────────────────────────────────────────────────────

    async def _run_chain(self, method: str, *args, **kwargs):
        last = len(self.providers) - 1
        for i, p in enumerate(self.providers):
            try:
                return await getattr(p, method)(*args, **kwargs)
            except (TokenBudgetExceeded, CostBudgetExceeded):
                raise
            except Exception as e:
                if i == last or not _should_fallback(e):
                    raise
                nxt = self.providers[i + 1].__class__.__name__
                self.logger.warning(
                    f"Provider '{p.__class__.__name__}' failed ({e}); falling back to '{nxt}'"
                )

    def _run_chain_sync(self, method: str, *args, **kwargs):
        last = len(self.providers) - 1
        for i, p in enumerate(self.providers):
            try:
                return getattr(p, method)(*args, **kwargs)
            except (TokenBudgetExceeded, CostBudgetExceeded):
                raise
            except Exception as e:
                if i == last or not _should_fallback(e):
                    raise
                nxt = self.providers[i + 1].__class__.__name__
                self.logger.warning(
                    f"Provider '{p.__class__.__name__}' failed ({e}); falling back to '{nxt}'"
                )

    # ── Text generation (basic) ───────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: list | None = None,
    ) -> str:
        """Generate AI response asynchronously (text only)"""
        return await self._run_chain("generate", prompt, system_prompt, context)

    def generate_sync(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: list | None = None,
    ) -> str:
        """Generate AI response synchronously (text only)"""
        return self._run_chain_sync("generate_sync", prompt, system_prompt, context)

    # ── Text generation + token tracking ─────────────────────────────────────

    async def generate_with_usage(
        self,
        prompt: str,
        system_prompt: str,
        context: list | None = None,
    ) -> dict[str, Any]:
        """
        Generate a response AND return full token usage metadata.

        Returns:
          {
            "response":           str,
            "reasoning":          str,
            "prompt_tokens":      int,
            "completion_tokens":  int,
            "total_tokens":       int,
            "cost_usd":           float,
            "model":              str,
            "provider":           str,
          }
        """
        return await self._run_chain("generate_with_usage", prompt, system_prompt, context)

    async def generate_with_reasoning(
        self,
        prompt: str,
        system_prompt: str,
        task_context: str | None = None,
    ) -> dict[str, Any]:
        """
        Backward-compatible wrapper around generate_with_usage().
        Always returns at least {"response", "reasoning"}.
        """
        return await self._run_chain("generate_with_reasoning", prompt, system_prompt, task_context)

    # ── Token reporting ───────────────────────────────────────────────────────

    @staticmethod
    def get_token_report(memory) -> str:
        """
        Generate a formatted text token-cost report from memory.token_ledger.
        Suitable for embedding in CLI output or the report appendix.

        Args:
            memory: PentestMemory instance

        Returns:
            Formatted multi-line string with token usage tables.
        """
        summary = memory.get_token_summary()

        lines: list[str] = [
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║              AI USAGE & COST SUMMARY                    ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
            "  By Agent:",
            f"  {'Agent':<20} {'Model':<30} {'Tokens':>10} {'Est. USD':>12}",
            "  " + "─" * 76,
        ]

        for entry in memory.token_ledger:
            lines.append(
                f"  {entry.agent:<20} {entry.model:<30} "
                f"{entry.total_tokens:>10,} {entry.cost_usd:>11.6f}"
            )

        lines += [
            "",
            "  By Provider:",
            f"  {'Provider':<20} {'Calls':>8} {'Tokens':>12} {'Est. USD':>14}",
            "  " + "─" * 58,
        ]
        for provider, data in summary.get("by_provider", {}).items():
            lines.append(
                f"  {provider:<20} {data['calls']:>8} "
                f"{data['tokens']:>12,} {data['cost_usd']:>13.6f}"
            )

        lines += [
            "",
            "  ─" * 40,
            f"  TOTAL PROMPT TOKENS     : {summary['total_prompt_tokens']:>12,}",
            f"  TOTAL COMPLETION TOKENS : {summary['total_completion_tokens']:>12,}",
            f"  TOTAL TOKENS            : {summary['total_tokens']:>12,}",
            f"  ESTIMATED TOTAL COST    : ${summary['total_cost_usd']:>11.4f} USD",
            f"  AI CALLS                : {len(memory.token_ledger):>12}",
            f"  THINKING STEPS          : {len(memory.thinking_chain):>12}",
            "",
            "  Note: Costs are estimates based on ai.pricing in config/guardstrike.yaml.",
            "        Actual billed amounts may differ.",
            "",
        ]

        return "\n".join(lines)

    # ── Introspection ─────────────────────────────────────────────────────────

    def get_model_name(self) -> str:
        """Get the current model name"""
        return self.model_name

    def is_available(self) -> bool:
        """Check if the provider is properly configured"""
        return self.provider.is_available()


# Backward compatibility alias
GeminiClient = AIClient
