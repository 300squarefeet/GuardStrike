"""Deterministic finding deduplication helpers.

Two findings are "the same" when they share a target and a vulnerability
identity (CVE, else CWE+normalized-title, else normalized-title). Duplicates
are MERGED into one finding that keeps the highest severity and records each
contributor's tool:execution_id — preserving evidence traceability.
"""

from __future__ import annotations

from guardstrike.core.memory import Finding

_SEVERITY = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def normalize_title(title: str) -> str:
    return " ".join((title or "").split()).lower()


def severity_rank(sev: str) -> int:
    return _SEVERITY.get((sev or "").lower(), 0)


def finding_dedup_key(f: Finding) -> tuple:
    target = (f.target or "").strip().lower()
    if f.cve:
        return (target, "cve", f.cve.strip().lower())
    if f.cwe:
        return (target, "cwe", f.cwe.strip().lower(), normalize_title(f.title))
    return (target, "title", normalize_title(f.title))


def merge_findings(primary: Finding, dup: Finding) -> Finding:
    """Merge ``dup`` into ``primary`` (mutated + returned). Highest severity
    wins; the duplicate's tool:execution_id is recorded; empty metadata is
    filled from the duplicate; ``primary.execution_id`` is never changed."""
    if severity_rank(dup.severity) > severity_rank(primary.severity):
        primary.severity = dup.severity
        primary.cvss_score = dup.cvss_score
        primary.cvss_vector = dup.cvss_vector

    primary.merged_from.append(f"{dup.tool}:{dup.execution_id or '?'}")

    for attr in ("cwe", "cve", "owasp", "mitre_technique", "remediation"):
        if not getattr(primary, attr) and getattr(dup, attr):
            setattr(primary, attr, getattr(dup, attr))

    return primary
