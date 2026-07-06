"""Deterministic finding prioritization.

Orders findings worst-first via a lexicographic sort key:
severity → attack-chain membership → public exploit availability →
exploitability → CVSS → corroboration. Pure and deterministic —
complements the LLM narrative; never mutates memory.
"""

from __future__ import annotations

from guardstrike.core.chains import AttackChain
from guardstrike.core.dedup import severity_rank
from guardstrike.core.memory import Finding


def _chain_ids(chains: list[AttackChain]) -> set[str]:
    ids: set[str] = set()
    for c in chains:
        ids.update(c.finding_ids)
    return ids


def _chain_lookup(chains: list[AttackChain]) -> dict[str, list[str]]:
    """finding_id -> [chain name, ...] in chains order (deterministic)."""
    lookup: dict[str, list[str]] = {}
    for c in chains:
        for fid in c.finding_ids:
            lookup.setdefault(fid, []).append(c.name)
    return lookup


def finding_priority_key(f: Finding, chain_ids: set[str]) -> tuple:
    """Descending sort key — higher tuple = higher priority."""
    return (
        severity_rank(f.severity),  # 1. severity dominates
        1 if f.id in chain_ids else 0,  # 2. within severity: chain member first
        1 if f.exploit_available else 0,  # 3. public exploit = strong boost
        float(f.exploitability or 0.0),  # 4. ease of exploitation
        float(f.cvss_score or 0.0),  # 5. then higher CVSS
        f.duplicate_count,  # 6. then more corroboration (SP4a)
    )


def rank_findings(findings: list[Finding], chains: list[AttackChain]) -> list[Finding]:
    """Return a NEW list worst-first. Stable: ties keep discovery order."""
    ids = _chain_ids(chains)
    return sorted(findings, key=lambda f: finding_priority_key(f, ids), reverse=True)


def priority_rationale(f: Finding, chain_lookup: dict[str, list[str]]) -> str:
    """One-line, human-readable 'why prioritized'."""
    parts = [f.severity]
    names = chain_lookup.get(f.id, [])
    if names:
        parts.append("part of " + " & ".join(names))
    if f.exploit_available:
        parts.append("public exploit available")
    if f.duplicate_count > 1:
        parts.append(f"corroborated by {f.duplicate_count} tool executions")
    return "; ".join(parts)


def render_prioritized_findings(findings: list[Finding], chains: list[AttackChain]) -> str:
    if not findings:
        return ""
    ranked = rank_findings(findings, chains)
    lookup = _chain_lookup(chains)
    lines = [
        "## Prioritized Findings",
        "",
        "| # | Finding | Severity | Why prioritized |",
        "|---|---|---|---|",
    ]
    for i, f in enumerate(ranked, 1):
        title = (f.title or "Untitled").replace("|", "\\|")
        why = priority_rationale(f, lookup).replace("|", "\\|")
        lines.append(f"| {i} | {title} | {f.severity} | {why} |")
    lines.append("")
    return "\n".join(lines)
