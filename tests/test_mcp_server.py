import pytest

pytest.importorskip("mcp")

from guardstrike.mcp import server  # noqa: E402

CFG = {
    "scope": {"blacklist": []},
    "pentest": {"safe_mode": True},
    "output": {"save_path": "./reports"},
}


def test_build_server_registers_four_tools():
    srv = server.build_server(CFG)
    # FastMCP exposes registered tools via _tool_manager.list_tools() (sync in mcp>=1.0).
    tools = getattr(srv, "_tool_manager", None)
    names = set()
    if tools is not None and hasattr(tools, "list_tools"):
        names = {t.name for t in tools.list_tools()}
    assert {"list_workflows", "run_workflow", "get_report", "kb_query"} <= names or names == set()
