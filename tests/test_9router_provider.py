import logging

import pytest


def _p(cfg):
    from guardstrike.ai.providers.nine_router_provider import NineRouterProvider

    return NineRouterProvider(cfg, logging.getLogger("test"))


def test_default_keyless_init(monkeypatch):
    monkeypatch.delenv("NINEROUTER_BASE_URL", raising=False)
    monkeypatch.delenv("NINEROUTER_MODEL", raising=False)
    monkeypatch.delenv("NINEROUTER_API_KEY", raising=False)
    p = _p({"ai": {"provider": "9router"}})
    assert p.base_url == "http://localhost:20128/v1"
    assert p.api_key == "EMPTY"
    assert p.get_model_name() == "kr/claude-sonnet-4.5"
    assert p.is_available() is True


def test_config_override():
    p = _p(
        {
            "ai": {
                "provider": "9router",
                "9router": {
                    "base_url": "http://localhost:9000/v1",
                    "model": "cc/claude-opus-4-7",
                    "api_key": "tok",
                },
            }
        }
    )
    assert p.base_url == "http://localhost:9000/v1"
    assert p.get_model_name() == "cc/claude-opus-4-7"
    assert p.api_key == "tok"


def test_env_override_and_config_wins(monkeypatch):
    monkeypatch.setenv("NINEROUTER_BASE_URL", "http://env:1234/v1")
    monkeypatch.setenv("NINEROUTER_MODEL", "kr/glm-5")
    ep = _p({"ai": {"provider": "9router"}})
    assert ep.base_url == "http://env:1234/v1"
    assert ep.get_model_name() == "kr/glm-5"
    p = _p({"ai": {"provider": "9router", "9router": {"base_url": "http://cfg:1/v1"}}})
    assert p.base_url == "http://cfg:1/v1"


def test_registered_and_get_provider(monkeypatch):
    monkeypatch.delenv("NINEROUTER_API_KEY", raising=False)
    from guardstrike.ai.providers import PROVIDERS, get_provider
    from guardstrike.ai.providers.nine_router_provider import NineRouterProvider

    assert "9router" in PROVIDERS
    p = get_provider({"ai": {"provider": "9router"}})
    assert isinstance(p, NineRouterProvider)


@pytest.mark.asyncio
async def test_usage_label():
    from unittest.mock import AsyncMock, MagicMock

    p = _p({"ai": {"provider": "9router"}})

    class _Resp:
        content = "hi"
        response_metadata = {
            "token_usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
        }

    p.backend = MagicMock()
    p.backend.ainvoke = AsyncMock(return_value=_Resp())
    out = await p.generate_with_usage("p", "s")
    assert out["provider"] == "9router"
    assert out["model"] == "kr/claude-sonnet-4.5"


def test_models_command_lists_9router():
    from typer.testing import CliRunner

    from guardstrike.cli.main import app

    result = CliRunner().invoke(app, ["models"])
    assert result.exit_code == 0
    assert "9ROUTER" in result.output
    assert "kr/claude-sonnet-4.5" in result.output
