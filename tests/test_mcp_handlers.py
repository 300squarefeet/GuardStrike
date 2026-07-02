import pytest

from guardstrike.mcp import handlers

CFG = {
    "scope": {"blacklist": ["127.0.0.0/8"], "max_targets": 100},
    "pentest": {"safe_mode": True},
    "logging": {"enabled": False, "level": "ERROR"},
    "output": {"save_path": "./reports", "format": "markdown"},
}


def test_list_workflows_returns_named_entries():
    wfs = handlers.list_workflows(CFG)
    assert isinstance(wfs, list) and len(wfs) >= 25
    assert all("name" in w and "description" in w for w in wfs)
    assert any(w["name"] in ("reconnaissance", "recon") for w in wfs)


@pytest.mark.asyncio
async def test_run_workflow_rejects_out_of_scope(monkeypatch):
    called = {"engine": False}

    class _Boom:
        def __init__(self, *a, **k):
            called["engine"] = True

    monkeypatch.setattr("guardstrike.mcp.handlers.WorkflowEngine", _Boom)
    out = await handlers.run_workflow(CFG, "recon", "127.0.0.1")
    assert out.get("error") == "target out of scope"
    assert called["engine"] is False  # engine never constructed


@pytest.mark.asyncio
async def test_run_workflow_unknown_name(monkeypatch):
    out = await handlers.run_workflow(CFG, "does_not_exist_xyz", "example.com")
    assert out.get("error") == "workflow not found"
    assert isinstance(out.get("available"), list) and out["available"]


@pytest.mark.asyncio
async def test_run_workflow_runs_engine_and_passes_assume_yes(monkeypatch):
    seen = {}

    class _Engine:
        def __init__(self, config, target, assume_yes=False):
            seen["target"] = target
            seen["assume_yes"] = assume_yes

        async def run_workflow(self, name):
            seen["name"] = name
            return {"status": "completed", "findings": 3, "session_id": "sid1", "analysis": {}}

    monkeypatch.setattr("guardstrike.mcp.handlers.WorkflowEngine", _Engine)
    out = await handlers.run_workflow(CFG, "recon", "example.com", assume_yes=True)
    assert out["status"] == "completed" and out["session_id"] == "sid1"
    assert seen["target"] == "example.com"
    assert seen["assume_yes"] is True
    assert seen["name"] == "recon"


def test_get_report_found_and_missing(tmp_path):
    cfg = {**CFG, "output": {"save_path": str(tmp_path)}}
    (tmp_path / "report_abc.md").write_text("# Report\nfindings")
    ok = handlers.get_report(cfg, "abc")
    assert ok["session_id"] == "abc" and "findings" in ok["content"]
    missing = handlers.get_report(cfg, "nope")
    assert missing.get("error") == "report not found"


def test_every_listed_workflow_name_resolves():
    from guardstrike.utils.resources import find_workflow

    for w in handlers.list_workflows(CFG):
        assert find_workflow(w["name"]) is not None, w["name"]
        assert "title" in w


def test_kb_query_wraps_results(monkeypatch):
    seen = {}

    class _Hit:
        def __init__(self):
            self.title = "log4j"
            self.text = "JNDI"

    class _KB:
        def __init__(self, *a, **k):
            pass

        def query(self, q, top_k=5):
            seen["top_k"] = top_k
            return [_Hit()]

    monkeypatch.setattr("guardstrike.mcp.handlers.KnowledgeBase", _KB)
    out = handlers.kb_query(CFG, "log4j", top_k=3)
    assert out["query"] == "log4j" and out["results"]
    assert seen["top_k"] == 3  # top_k passed through


@pytest.mark.asyncio
async def test_run_workflow_engine_error_returns_structured(monkeypatch):
    class _Engine:
        def __init__(self, config, target, assume_yes=False):
            pass

        async def run_workflow(self, name):
            raise RuntimeError("boom in engine")

    monkeypatch.setattr("guardstrike.mcp.handlers.WorkflowEngine", _Engine)
    out = await handlers.run_workflow(CFG, "recon", "example.com")
    assert "error" in out and "boom in engine" in out["error"]


def test_kb_query_error_returns_structured(monkeypatch):
    class _KB:
        def __init__(self, *a, **k):
            pass

        def query(self, q, top_k=5):
            raise RuntimeError("kb exploded")

    monkeypatch.setattr("guardstrike.mcp.handlers.KnowledgeBase", _KB)
    out = handlers.kb_query(CFG, "log4j")
    assert "error" in out and "kb exploded" in out["error"]


def test_get_report_read_error_returns_structured(tmp_path, monkeypatch):
    cfg = {**CFG, "output": {"save_path": str(tmp_path)}}
    (tmp_path / "report_x.md").write_text("ok")

    def boom(*a, **k):
        raise OSError("disk gone")

    monkeypatch.setattr("pathlib.Path.read_text", boom)
    out = handlers.get_report(cfg, "x")
    assert "error" in out and "disk gone" in out["error"]
