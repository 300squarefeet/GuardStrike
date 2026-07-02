"""Deterministic tool-execution recovery: classify a failed tool run, decide
whether to retry, compute backoff, and downshift parameters (adaptive
rate-limit / WAF timing). Pure helpers — no I/O, no side effects.
"""

from __future__ import annotations

TIMEOUT = "timeout"
RATE_LIMITED = "rate_limited"
WAF_BLOCK = "waf_block"
CONNECTION = "connection"
PERMISSION = "permission"
NOT_FOUND = "not_found"
UNKNOWN = "unknown"

_RETRIABLE = {TIMEOUT, RATE_LIMITED, WAF_BLOCK, CONNECTION}
_EXIT_MAP = {124: TIMEOUT, 126: PERMISSION, 127: NOT_FOUND}

# First matching marker wins — order matters (specific throttling before generic timeout).
_MARKERS: list[tuple[str, str]] = [
    ("rate limit", RATE_LIMITED),
    ("too many requests", RATE_LIMITED),
    (" 429", RATE_LIMITED),
    (" 403", WAF_BLOCK),
    (" 406", WAF_BLOCK),
    ("forbidden", WAF_BLOCK),
    ("blocked by", WAF_BLOCK),
    ("waf", WAF_BLOCK),
    ("timed out", TIMEOUT),
    ("timeout", TIMEOUT),
    ("connection refused", CONNECTION),
    ("connection reset", CONNECTION),
    ("unreachable", CONNECTION),
    ("no route to host", CONNECTION),
    ("permission denied", PERMISSION),
    ("not permitted", PERMISSION),
    ("command not found", NOT_FOUND),
    ("no such file", NOT_FOUND),
]


def classify_error(exit_code: int | None, output: str, error: str | None) -> str:
    if exit_code in _EXIT_MAP:
        return _EXIT_MAP[exit_code]
    hay = f"{output or ''}\n{error or ''}".lower()
    for marker, etype in _MARKERS:
        if marker in hay:
            return etype
    return UNKNOWN


def is_retriable(error_type: str) -> bool:
    return error_type in _RETRIABLE


def backoff_delay(attempt: int, error_type: str, base: float = 2.0, cap: float = 30.0) -> float:
    initial = 5.0 if error_type in (RATE_LIMITED, WAF_BLOCK) else 1.0
    return min(cap, initial * (base ** max(0, attempt)))


_HALVE_KEYS = ("threads", "rate", "concurrency")
_PER_TOOL: dict[str, dict[str, dict]] = {
    "nmap": {
        TIMEOUT: {"timing": "-T2"},
        RATE_LIMITED: {"timing": "-T1", "delay": 1},
        WAF_BLOCK: {"timing": "-T1", "delay": 1},
    },
}


def adjust_params(tool_name: str, error_type: str, params: dict) -> dict:
    """Return a NEW params dict with a conservative downshift for the failure.

    Only halves concurrency knobs that are already present and adds a delay on
    throttling signals; per-tool patches fill tool-specific knobs. Knobs a tool
    doesn't read are harmlessly ignored downstream.
    """
    out = dict(params)
    if error_type in (TIMEOUT, RATE_LIMITED, WAF_BLOCK):
        for k in _HALVE_KEYS:
            v = out.get(k)
            if isinstance(v, int) and v > 1:
                out[k] = max(1, v // 2)
    if error_type in (RATE_LIMITED, WAF_BLOCK):
        d = out.get("delay")
        out["delay"] = int(d) * 2 if isinstance(d, int) and d > 0 else 1
    for k, v in _PER_TOOL.get(tool_name, {}).get(error_type, {}).items():
        out.setdefault(k, v)
    return out
