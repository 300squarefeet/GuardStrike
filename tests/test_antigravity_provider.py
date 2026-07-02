import logging

import pytest


def _p(cfg):
    from guardstrike.ai.providers.antigravity_provider import AntigravityProvider

    return AntigravityProvider(cfg, logging.getLogger("test"))


def test_default_keyless_init(monkeypatch):
    monkeypatch.delenv("ANTIGRAVITY_BASE_URL", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_API_KEY", raising=False)
    p = _p({"ai": {"provider": "antigravity"}})
    assert p.base_url == "http://localhost:3000/v1"
    assert p.api_key == "EMPTY"
    assert p.get_model_name() == "gemini-3-pro"
    assert p.is_available() is True


def test_config_override():
    p = _p(
        {
            "ai": {
                "provider": "antigravity",
                "antigravity": {
                    "base_url": "http://localhost:9000/v1",
                    "model": "claude-opus-4-6",
                    "api_key": "tok",
                },
            }
        }
    )
    assert p.base_url == "http://localhost:9000/v1"
    assert p.get_model_name() == "claude-opus-4-6"
    assert p.api_key == "tok"


def test_env_override_and_config_wins(monkeypatch):
    monkeypatch.setenv("ANTIGRAVITY_BASE_URL", "http://env:1234/v1")
    monkeypatch.setenv("ANTIGRAVITY_MODEL", "env-model")
    # No config → env used (uniform config > env > default across all three fields).
    ep = _p({"ai": {"provider": "antigravity"}})
    assert ep.base_url == "http://env:1234/v1"
    assert ep.get_model_name() == "env-model"
    # Config set → config wins over env.
    p = _p(
        {
            "ai": {
                "provider": "antigravity",
                "antigravity": {"base_url": "http://cfg:1/v1", "model": "cfg-model"},
            }
        }
    )
    assert p.base_url == "http://cfg:1/v1"
    assert p.get_model_name() == "cfg-model"


def test_registered_and_get_provider(monkeypatch):
    monkeypatch.delenv("ANTIGRAVITY_API_KEY", raising=False)
    from guardstrike.ai.providers import PROVIDERS, get_provider
    from guardstrike.ai.providers.antigravity_provider import AntigravityProvider

    assert "antigravity" in PROVIDERS
    p = get_provider({"ai": {"provider": "antigravity"}})
    assert isinstance(p, AntigravityProvider)


@pytest.mark.asyncio
async def test_usage_label(monkeypatch):
    from unittest.mock import AsyncMock, MagicMock

    p = _p({"ai": {"provider": "antigravity"}})

    class _Resp:
        content = "hi"
        response_metadata = {
            "token_usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
        }

    # Replace the whole backend (ChatOpenAI is a Pydantic model — its own
    # attributes can't be monkeypatched; the provider attribute can).
    p.backend = MagicMock()
    p.backend.ainvoke = AsyncMock(return_value=_Resp())
    out = await p.generate_with_usage("p", "s")
    assert out["provider"] == "antigravity"
    assert out["model"] == "gemini-3-pro"
