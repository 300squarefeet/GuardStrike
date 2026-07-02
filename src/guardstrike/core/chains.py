"""Deterministic attack-chain detection over findings.

A chain fires when, for a single target, every component of a curated rule is
matched by at least one finding (keyword substring in title/description, or a
matching CWE number). Pure and deterministic — complements the LLM correlation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from guardstrike.core.dedup import severity_rank
from guardstrike.core.memory import Finding


@dataclass
class AttackChain:
    name: str
    technique: str
    severity: str
    finding_ids: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ChainRule:
    name: str
    components: list[dict]
    technique: str
    severity: str
    rationale: str


RULES: list[ChainRule] = [
    ChainRule(
        "SSRF → Cloud Metadata",
        [{"any_keywords": ["ssrf", "server-side request forgery"], "any_cwes": ["918"]}],
        "Cloud credential theft via the instance metadata endpoint",
        "critical",
        "An SSRF can reach the cloud metadata endpoint (169.254.169.254) to steal instance credentials.",
    ),
    ChainRule(
        "SQL Injection → Data Breach",
        [{"any_keywords": ["sql injection", "sqli"], "any_cwes": ["89"]}],
        "Database exfiltration or authentication bypass",
        "critical",
        "SQL injection allows dumping or altering the backing database.",
    ),
    ChainRule(
        "XSS → Account Takeover",
        [{"any_keywords": ["xss", "cross-site scripting"], "any_cwes": ["79"]}],
        "Session/cookie theft leading to account takeover",
        "high",
        "Stored or reflected XSS can exfiltrate session tokens to hijack accounts.",
    ),
    ChainRule(
        "IDOR + Weak Auth → Horizontal Escalation",
        [
            {"any_keywords": ["idor", "insecure direct object"], "any_cwes": ["639"]},
            {
                "any_keywords": [
                    "broken access",
                    "access control",
                    "authorization",
                    "missing auth",
                ],
                "any_cwes": ["284", "285", "862"],
            },
        ],
        "Cross-account data access via unprotected object references",
        "high",
        "An IDOR combined with weak authorization enables reading other users' data.",
    ),
    ChainRule(
        "Open Redirect → OAuth Token Theft",
        [
            {"any_keywords": ["open redirect"], "any_cwes": ["601"]},
            {
                "any_keywords": ["oauth", "sso", "access token", "authorization code"],
                "any_cwes": [],
            },
        ],
        "OAuth authorization-code/token theft via redirect_uri abuse",
        "high",
        "An open redirect on an OAuth flow can leak the authorization code or access token.",
    ),
    ChainRule(
        "Subdomain Takeover",
        [{"any_keywords": ["subdomain takeover", "dangling", "unclaimed"], "any_cwes": []}],
        "Hijack a dangling subdomain for phishing or cookie scoping",
        "high",
        "A dangling DNS record pointing at an unclaimed service can be taken over.",
    ),
    ChainRule(
        "Exposed Secret → Lateral Movement",
        [
            {
                "any_keywords": [
                    "exposed secret",
                    "api key",
                    "hardcoded",
                    "leaked token",
                    "leaked credential",
                ],
                "any_cwes": ["798", "200"],
            }
        ],
        "Use a leaked credential to move laterally to other systems",
        "high",
        "An exposed secret can authenticate an attacker to connected systems.",
    ),
    ChainRule(
        "Path Traversal / LFI → RCE",
        [
            {
                "any_keywords": [
                    "path traversal",
                    "directory traversal",
                    "local file inclusion",
                    "lfi",
                ],
                "any_cwes": ["22", "98"],
            }
        ],
        "Arbitrary file read escalating toward code execution",
        "high",
        "Path traversal or LFI can read sensitive files or include executable content.",
    ),
]


def _cwe_digits(cwe: str | None) -> str:
    return re.sub(r"[^0-9]", "", cwe or "")


def _finding_matches_component(f: Finding, comp: dict) -> bool:
    hay = f"{f.title or ''} {f.description or ''}".lower()
    if any(kw.lower() in hay for kw in comp.get("any_keywords", [])):
        return True
    fcwe = _cwe_digits(f.cwe)
    return bool(fcwe) and fcwe in {_cwe_digits(c) for c in comp.get("any_cwes", [])}


def detect_chains(findings: list[Finding]) -> list[AttackChain]:
    by_target: dict[str, list[Finding]] = {}
    for f in findings:
        by_target.setdefault((f.target or "").strip().lower(), []).append(f)

    chains: list[AttackChain] = []
    seen: set = set()
    for group in by_target.values():
        for rule in RULES:
            matched: list[str] = []
            ok = True
            for comp in rule.components:
                comp_ids = [f.id for f in group if _finding_matches_component(f, comp)]
                if not comp_ids:
                    ok = False
                    break
                matched.extend(comp_ids)
            if not ok:
                continue
            ids = list(dict.fromkeys(matched))  # unique, order-preserving
            key = (rule.name, tuple(sorted(ids)))
            if key in seen:
                continue
            seen.add(key)
            chains.append(
                AttackChain(rule.name, rule.technique, rule.severity, ids, rule.rationale)
            )

    chains.sort(key=lambda c: (-severity_rank(c.severity), c.name))
    return chains


def render_attack_chains(findings: list[Finding]) -> str:
    chains = detect_chains(findings)
    if not chains:
        return ""
    lines = ["## Attack Chains", ""]
    for c in chains:
        lines.append(f"### {c.name} ({c.severity})")
        lines.append(f"- **Technique:** {c.technique}")
        lines.append(f"- **Contributing findings:** {', '.join(c.finding_ids)}")
        lines.append(f"- {c.rationale}")
        lines.append("")
    return "\n".join(lines)
