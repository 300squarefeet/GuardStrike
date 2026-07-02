"""Pure handlers bridging GuardStrike to MCP tools.

MUST NOT import the `mcp` package — these are unit-testable without it. Every
handler returns a JSON-serializable dict/list and never raises to the caller;
errors are returned as structured results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from guardstrike.core.knowledge_base import KnowledgeBase
from guardstrike.core.workflow import WorkflowEngine
from guardstrike.utils.resources import find_workflow, iter_workflow_files
from guardstrike.utils.scope_validator import ScopeValidator

_EXT = {"md": "md", "markdown": "md", "html": "html", "json": "json"}


def list_workflows(config: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in sorted(iter_workflow_files(), key=lambda p: p.stem):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            doc = {}
        out.append(
            {
                "name": path.stem,  # resolvable by run_workflow/find_workflow
                "title": str(doc.get("name") or path.stem),  # human display name from YAML
                "description": str(doc.get("description") or ""),
            }
        )
    return out


async def run_workflow(
    config: dict[str, Any], name: str, target: str, assume_yes: bool = False
) -> dict[str, Any]:
    if find_workflow(name) is None:
        return {
            "error": "workflow not found",
            "available": [w["name"] for w in list_workflows(config)],
        }

    ok, reason = ScopeValidator(config).validate_target(target)
    if not ok:
        return {"error": "target out of scope", "reason": reason, "target": target}

    engine = WorkflowEngine(config, target, assume_yes=assume_yes)
    try:
        result = await engine.run_workflow(name)
    except Exception as e:
        return {"error": f"workflow failed: {e}", "target": target, "workflow": name}
    return {
        "status": result.get("status"),
        "findings": result.get("findings"),
        "session_id": result.get("session_id"),
        "analysis": result.get("analysis"),
        "reason": result.get("reason"),  # present on stopped_budget; None otherwise
    }


def get_report(config: dict[str, Any], session_id: str, fmt: str = "md") -> dict[str, Any]:
    save_path = Path(config.get("output", {}).get("save_path", "./reports"))
    ext = _EXT.get(fmt.lower(), "md")
    report_file = save_path / f"report_{session_id}.{ext}"
    if not report_file.exists():
        return {"error": "report not found", "session_id": session_id, "path": str(report_file)}
    try:
        content = report_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "error": f"report read failed: {e}",
            "session_id": session_id,
            "path": str(report_file),
        }
    return {
        "session_id": session_id,
        "format": ext,
        "content": content,
    }


def _hit_to_dict(h: Any) -> dict[str, Any] | str:
    """Serialize a KB hit to a JSON-safe dict.

    Handles both the real ``KBHit`` dataclass (which nests a ``KBEntry``
    dataclass under ``.entry``) and plain-attribute test stubs.
    """
    if hasattr(h, "entry") and hasattr(h, "score"):
        # Real KBHit: flatten KBEntry fields + score into a single dict.
        entry = h.entry
        d: dict[str, Any] = dict(vars(entry)) if hasattr(entry, "__dict__") else {}
        d["score"] = h.score
        return d
    if hasattr(h, "__dict__"):
        return {k: v for k, v in vars(h).items() if not k.startswith("_")}
    return str(h)


def kb_query(config: dict[str, Any], query: str, top_k: int = 5) -> dict[str, Any]:
    # Pass positionally: real param is `k`, test stub uses `top_k` — positional
    # call avoids the keyword mismatch between the two.
    try:
        hits = KnowledgeBase().query(query, top_k)
    except Exception as e:
        return {"error": f"kb query failed: {e}", "query": query}
    results = [_hit_to_dict(h) for h in hits]
    out: dict[str, Any] = {"query": query, "results": results}
    if not results:
        out["note"] = "No matches — the KB may not be seeded (`guardstrike kb seed`)."
    return out
