"""9Router provider — keyless access to 40+ providers via a local 9Router gateway.

9Router (https://9router.com, github.com/decolua/9router) is a local
OpenAI-compatible gateway that routes to 40+ upstream providers with free
tiers, auto-fallback, and token saving. Run 9Router locally, then point this
provider at its endpoint — no API key required (the gateway holds the upstream
credentials). The ``model`` field is passed through, so any 9Router model ID
works (e.g. ``kr/claude-sonnet-4.5`` free, ``cc/claude-opus-4-7`` subscription,
``glm/glm-5.1`` cheap). See ``guardstrike models`` for the catalog.

Config:
    ai:
      provider: 9router
      9router:
        base_url: http://localhost:20128/v1   # default (9Router local gateway)
        model: kr/claude-sonnet-4.5            # default (free tier)
        # api_key: only if the gateway enforces one (env: NINEROUTER_API_KEY)
"""

from __future__ import annotations

import os
from typing import Any

from guardstrike.ai.providers.openai_compatible_provider import OpenAICompatibleProvider


class NineRouterProvider(OpenAICompatibleProvider):
    """9Router local gateway via the OpenAI-compatible surface (keyless by default)."""

    _DEFAULT_BASE_URL = "http://localhost:20128/v1"
    _DEFAULT_MODEL = "kr/claude-sonnet-4.5"

    def __init__(self, config: dict[str, Any], logger):
        ai = dict(config.get("ai", {}))
        nr = ai.get("9router", {}) or {}
        base_url = (
            nr.get("base_url") or os.environ.get("NINEROUTER_BASE_URL") or self._DEFAULT_BASE_URL
        )
        model = nr.get("model") or os.environ.get("NINEROUTER_MODEL") or self._DEFAULT_MODEL
        api_key = nr.get("api_key") or os.environ.get("NINEROUTER_API_KEY") or "EMPTY"
        # Feed the parent the `ai.openai_compatible` shape it reads (DRY reuse).
        synth_ai = dict(ai)
        synth_ai["openai_compatible"] = {"base_url": base_url, "model": model, "api_key": api_key}
        super().__init__({**config, "ai": synth_ai}, logger)

    async def generate_with_usage(
        self, prompt: str, system_prompt: str, context: list | None = None
    ) -> dict[str, Any]:
        out = await super().generate_with_usage(prompt, system_prompt, context)
        out["provider"] = "9router"  # parent hardcodes "openai_compatible"
        return out
