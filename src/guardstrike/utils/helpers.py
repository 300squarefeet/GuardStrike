"""
Common utility functions for GuardStrike
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str = "config/guardstrike.yaml") -> dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Warning: Could not load config from {config_path}: {e}")
        return {}


def save_json(data: Any, filepath: Path):
    """Save data as JSON"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(filepath: Path) -> Any:
    """Load JSON file"""
    with open(filepath) as f:
        return json.load(f)


def is_valid_domain(domain: str) -> bool:
    """Validate domain name format"""
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))


def is_valid_ip(ip: str) -> bool:
    """Validate IP address format"""
    pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(pattern, ip))


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r"^https?://(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}|(?:[0-9]{1,3}\.){3}[0-9]{1,3})(?::[0-9]{1,5})?(?:/.*)?$"
    return bool(re.match(pattern, url))


def extract_domain_from_url(url: str) -> str | None:
    """Extract domain from URL"""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        return parsed.hostname or parsed.netloc
    except:
        return None


def format_timestamp(dt: datetime | None = None) -> str:
    """Format timestamp for reports"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem-safe"""
    # Remove/replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")
    # Limit length
    return filename[:200]


def parse_severity(severity: str) -> int:
    """Convert severity string to numeric value for sorting"""
    severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    return severity_map.get(severity.lower(), 0)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def ensure_dir(path: Path):
    """Ensure directory exists"""
    path.mkdir(parents=True, exist_ok=True)


def color_severity(severity: str) -> str:
    """Return rich markup color for severity"""
    colors = {
        "critical": "bold red",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "cyan",
    }
    return colors.get(severity.lower(), "white")


def resolve_reports_dir(config: dict) -> Path:
    """Directory where sessions/reports live (config output.save_path, default ./reports)."""
    save_path = (config.get("output") or {}).get("save_path") or "./reports"
    return Path(save_path)


def resolve_session_path(config: dict, session_id: str) -> Path:
    """Path to session_<id>.json under the configured reports dir."""
    return resolve_reports_dir(config) / f"session_{session_id}.json"


def list_session_ids(config: dict) -> list[str]:
    """Sorted session ids found in the reports dir (empty if none / dir missing)."""
    d = resolve_reports_dir(config)
    if not d.is_dir():
        return []
    ids = (p.stem[len("session_") :] for p in d.glob("session_*.json"))
    return sorted(i for i in ids if i)


_SECRET_MARKERS = ("api_key", "apikey", "token", "webhook", "password", "secret")


def _is_secret_key(key: object) -> bool:
    """True if a config key looks sensitive (substring match — over-masks by design)."""
    return isinstance(key, str) and any(m in key.lower() for m in _SECRET_MARKERS)


def mask_secrets(config: dict) -> dict:
    """Deep-copy config with sensitive values masked to '***' (null/empty kept).

    Matches secret markers as substrings so keys like ``openai_api_key`` or
    ``client_secret`` are caught. Prefers over-masking to leaking.
    """

    def _mask(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: ("***" if (_is_secret_key(k) and v) else _mask(v)) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_mask(x) for x in obj]
        return obj

    return _mask(config)
