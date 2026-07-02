import pytest

from guardstrike.ai.ai_client import AIClient, _should_fallback


class _StubProvider:
    """Minimal stand-in: records calls, raises or returns as scripted."""

    def __init__(self, name, behavior):
        self._name = name
        self.behavior = behavior  # callable() -> str OR Exception to raise
        self.budget = None
        self.calls = 0

    def get_model_name(self):
        return f"{self._name}-model"

    async def generate(self, prompt, system_prompt=None, context=None):
        self.calls += 1
        b = self.behavior
        if isinstance(b, Exception):
            raise b
        return b


def _client_with(providers):
    c = AIClient.__new__(AIClient)  # bypass __init__/get_provider_chain
    import logging

    c.config = {}
    c.logger = logging.getLogger("t")
    c.providers = providers
    c.provider = providers[0]
    c.model_name = providers[0].get_model_name()
    return c


def test_should_fallback_classifies():
    assert _should_fallback(Exception("429 rate limit")) is True
    assert _should_fallback(Exception("model not found")) is True
    assert _should_fallback(Exception("the model does not exist")) is True
    assert _should_fallback(Exception("401 unauthorized: bad api key")) is False
    assert _should_fallback(Exception("totally unknown boom")) is False


@pytest.mark.asyncio
async def test_falls_over_on_transient():
    primary = _StubProvider("p", Exception("503 service unavailable"))
    backup = _StubProvider("b", "ok-from-backup")
    c = _client_with([primary, backup])
    assert await c.generate("hi") == "ok-from-backup"
    assert primary.calls == 1 and backup.calls == 1


@pytest.mark.asyncio
async def test_auth_error_raises_without_fallback():
    primary = _StubProvider("p", Exception("401 invalid api key"))
    backup = _StubProvider("b", "ok-from-backup")
    c = _client_with([primary, backup])
    with pytest.raises(Exception, match="401"):
        await c.generate("hi")
    assert backup.calls == 0


@pytest.mark.asyncio
async def test_single_provider_unchanged():
    only = _StubProvider("p", "single")
    c = _client_with([only])
    assert await c.generate("hi") == "single"
