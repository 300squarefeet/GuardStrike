"""FastMCP stdio server exposing GuardStrike workflows over MCP.

This is the ONLY module that imports the optional `mcp` package. Import it only
after confirming `mcp` is installed (the CLI command guards this).
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from guardstrike.mcp import handlers


def build_server(config: dict[str, Any]) -> FastMCP:
    mcp = FastMCP("guardstrike")

    @mcp.tool()
    def list_workflows() -> list[dict[str, str]]:
        """List available GuardStrike pentest workflows (name + description)."""
        return handlers.list_workflows(config)

    @mcp.tool()
    async def run_workflow(name: str, target: str, assume_yes: bool = False) -> dict[str, Any]:
        """Run a named workflow against a target. Target scope is validated.
        Active tools (e.g. port scans) run only when assume_yes=true; destructive
        tools are always blocked by safe_mode. WARNING: authorized targets only."""
        return await handlers.run_workflow(config, name, target, assume_yes)

    @mcp.tool()
    def get_report(session_id: str, fmt: str = "md") -> dict[str, Any]:
        """Return the saved report for a completed session (read-only)."""
        return handlers.get_report(config, session_id, fmt)

    @mcp.tool()
    def kb_query(query: str, top_k: int = 5) -> dict[str, Any]:
        """Query the offline CVE/CWE/MITRE knowledge base."""
        return handlers.kb_query(config, query, top_k)

    return mcp


def serve(config: dict[str, Any]) -> None:
    build_server(config).run(transport="stdio")
