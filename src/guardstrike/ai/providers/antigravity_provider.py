"""Antigravity provider — keyless access to Antigravity models via a local
OpenAI-compatible proxy.

Antigravity (Google's agentic IDE) has no public API. Run a local
OpenAI-compatible proxy that holds your Antigravity OAuth session (e.g.
``openai-proxy-for-antigravity`` at http://localhost:3000), then point this
provider at it — no API key required.

Config:
    ai:
      provider: antigravity
      antigravity:
        base_url: http://localhost:3000/v1   # default
        model: gemini-3-pro                  # default
        # api_key: only if your proxy requires one (env: ANTIGRAVITY_API_KEY)
"""

from __future__ import annotations

import os
from typing import Any

from guardstrike.ai.providers.openai_compatible_provider import OpenAICompatibleProvider


class AntigravityProvider(OpenAICompatibleProvider):
    """Antigravity via a local OpenAI-compatible proxy (keyless by default)."""

    _DEFAULT_BASE_URL = "http://localhost:3000/v1"
    _DEFAULT_MODEL = "gemini-3-pro"

    def __init__(self, config: dict[str, Any], logger: Any) -> None:
        ai = dict(config.get("ai", {}))
        ag = ai.get("antigravity", {}) or {}
        base_url = (
            ag.get("base_url") or os.environ.get("ANTIGRAVITY_BASE_URL") or self._DEFAULT_BASE_URL
        )
        model = ag.get("model") or os.environ.get("ANTIGRAVITY_MODEL") or self._DEFAULT_MODEL
        api_key = ag.get("api_key") or os.environ.get("ANTIGRAVITY_API_KEY") or "EMPTY"
        # Feed the parent the `ai.openai_compatible` shape it reads (DRY reuse).
        synth_ai = dict(ai)
        synth_ai["openai_compatible"] = {"base_url": base_url, "model": model, "api_key": api_key}
        super().__init__({**config, "ai": synth_ai}, logger)

    async def generate_with_usage(
        self, prompt: str, system_prompt: str, context: list | None = None
    ) -> dict[str, Any]:
        out = await super().generate_with_usage(prompt, system_prompt, context)
        out["provider"] = "antigravity"  # parent hardcodes "openai_compatible"
        return out
