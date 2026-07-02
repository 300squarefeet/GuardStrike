"""
DefectDojo exporter.

DefectDojo's Generic Findings Import schema is a JSON document with a
``findings`` array. Each finding has a fixed shape; the importer creates
or updates entries in an existing engagement / test on import.

API reference: https://documentation.defectdojo.com/integrations/parsers/file/generic/

This exporter produces the JSON document and can push it to a running
DefectDojo instance. ``post()`` performs the import-scan push via the
``/api/v2/import-scan/`` endpoint; pure document translation stays in
``export()``.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from guardstrike.core.memory import Finding, PentestMemory

_SEVERITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Info",
}


def export(memory: PentestMemory) -> dict[str, Any]:
    """Return a Generic Findings Import-compatible JSON dict."""
    return {
        "findings": [_finding_to_dd(f) for f in memory.findings if not f.false_positive],
    }


def _finding_to_dd(f: Finding) -> dict[str, Any]:
    out: dict[str, Any] = {
        "title": f.title or "Untitled finding",
        "description": _build_description(f),
        "severity": _SEVERITY_MAP.get((f.severity or "info").lower(), "Info"),
        "active": True,
        "verified": False,
        "false_p": bool(f.false_positive),
        "mitigation": f.remediation or "",
        "tool": f.tool,
        "static_finding": False,
        "dynamic_finding": True,
    }
    if f.cve:
        out["cve"] = f.cve
    if f.cvss_score is not None:
        out["cvssv3_score"] = f.cvss_score
    if f.cvss_vector:
        out["cvssv3"] = f.cvss_vector
    if f.cwe and f.cwe.upper().startswith("CWE-") and f.cwe[4:].isdigit():
        out["cwe"] = int(f.cwe[4:])
    if f.target:
        out["url"] = f.target
    return out


def _build_description(f: Finding) -> str:
    parts = []
    if f.description:
        parts.append(f.description)
    if f.evidence:
        parts.append("\n## Evidence\n" + f.evidence[:2000])
    if f.execution_id:
        parts.append(f"\n## Execution ID\n{f.execution_id}")
    return "\n\n".join(parts) or f.title or ""


def post(
    base_url: str,
    api_token: str,
    engagement_id: int,
    doc: dict[str, Any],
    *,
    scan_type: str = "Generic Findings Import",
    timeout: int = 30,
) -> int:
    """POST an exported findings doc to DefectDojo ``/api/v2/import-scan/``.

    Sends multipart/form-data: a ``file`` part (the JSON doc) plus form
    fields (scan_type, engagement, active, verified). Auth via
    ``Authorization: Token <api_token>``. Returns the HTTP status code.
    Raises on transport/HTTP error — the caller decides how to surface it.
    """
    url = base_url.rstrip("/") + "/api/v2/import-scan/"
    boundary = "----guardstrikeboundaryZ9x7Kq2Lp"

    chunks: list[bytes] = []

    def _field(name: str, value: str) -> None:
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        chunks.append(f"{value}\r\n".encode())

    _field("scan_type", scan_type)
    _field("engagement", str(engagement_id))
    _field("active", "true")
    _field("verified", "false")

    file_bytes = json.dumps(doc).encode("utf-8")
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(b'Content-Disposition: form-data; name="file"; filename="findings.json"\r\n')
    chunks.append(b"Content-Type: application/json\r\n\r\n")
    chunks.append(file_bytes)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    body = b"".join(chunks)

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Token {api_token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — operator-supplied URL
        return resp.status
