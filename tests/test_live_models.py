import json
import logging
import urllib.request


def _nr():
    from guardstrike.ai.providers.nine_router_provider import NineRouterProvider

    return NineRouterProvider({"ai": {"provider": "9router"}}, logging.getLogger("t"))


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._b


def test_list_models_fetches_ids(monkeypatch):
    cap = {}

    def fake(req, timeout=None):
        cap["url"] = req.full_url
        return _Resp({"data": [{"id": "kr/claude-sonnet-4.5"}, {"id": "glm/glm-5"}]})

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    p = _nr()
    assert p.list_models() == ["glm/glm-5", "kr/claude-sonnet-4.5"]  # sorted
    assert cap["url"] == "http://localhost:20128/v1/models"


def test_models_live_cli(monkeypatch):
    from typer.testing import CliRunner

    from guardstrike.cli.main import app

    def fake(req, timeout=None):
        return _Resp({"data": [{"id": "kr/glm-5"}, {"id": "cc/claude-opus-4-7"}]})

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    r = CliRunner().invoke(
        app, ["models", "--live", "--provider", "9router", "--config", "config/guardstrike.yaml"]
    )
    assert r.exit_code == 0
    assert "kr/glm-5" in r.output and "cc/claude-opus-4-7" in r.output


def test_models_live_gateway_down(monkeypatch):
    from typer.testing import CliRunner

    from guardstrike.cli.main import app

    def boom(req, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    r = CliRunner().invoke(app, ["models", "--live", "--config", "config/guardstrike.yaml"])
    assert r.exit_code == 1
    assert "gateway" in r.output.lower()
