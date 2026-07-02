"""Run-global token + USD-cost budget tracking, shared across providers."""

from __future__ import annotations

import logging


class TokenBudgetExceeded(Exception):
    """Raised when cumulative token usage exceeds the configured budget."""


class CostBudgetExceeded(Exception):
    """Raised when cumulative estimated USD cost exceeds the configured cap."""


class BudgetTracker:
    """Accumulates token + cost usage for one run.

    ``token_budget``/``max_cost_usd`` of ``None`` disable that cap. Warns once
    at 80% of each active cap; raises at 100%. Shared across every provider in
    an AIClient so usage (and fallbacks) accumulate against one budget.
    """

    def __init__(
        self,
        token_budget: int | None,
        max_cost_usd: float | None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.token_budget = token_budget
        self.max_cost_usd = max_cost_usd
        self.logger = logger or logging.getLogger("guardstrike.budget")
        self._used_tokens = 0
        self._used_cost = 0.0
        self._token_warned = False
        self._cost_warned = False

    @property
    def used_tokens(self) -> int:
        return self._used_tokens

    @property
    def used_cost(self) -> float:
        return self._used_cost

    def add(self, total_tokens: int, cost_usd: float) -> None:
        self._used_tokens += int(total_tokens or 0)
        self._used_cost += float(cost_usd or 0.0)

        if self.token_budget:
            ratio = self._used_tokens / self.token_budget
            if ratio >= 1.0:
                raise TokenBudgetExceeded(
                    f"Token budget exhausted: used {self._used_tokens:,} "
                    f"of {self.token_budget:,}"
                )
            if ratio >= 0.8 and not self._token_warned:
                self._token_warned = True
                self.logger.warning(
                    f"Token budget at {ratio * 100:.0f}% "
                    f"({self._used_tokens:,} / {self.token_budget:,})."
                )

        if self.max_cost_usd:
            ratio = self._used_cost / self.max_cost_usd
            if ratio >= 1.0:
                raise CostBudgetExceeded(
                    f"Cost budget exhausted: used ${self._used_cost:.4f} "
                    f"of ${self.max_cost_usd:.4f}"
                )
            if ratio >= 0.8 and not self._cost_warned:
                self._cost_warned = True
                self.logger.warning(
                    f"Cost budget at {ratio * 100:.0f}% "
                    f"(${self._used_cost:.4f} / ${self.max_cost_usd:.4f})."
                )
