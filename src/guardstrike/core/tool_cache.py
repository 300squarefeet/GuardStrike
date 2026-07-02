"""Opt-in, TTL'd on-disk cache of successful tool results.

Keyed by (tool, target, params). Default OFF. Best-effort: never raises — an
I/O fault degrades to a cache miss / no-op so it cannot break a tool run.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from guardstrike.utils.logger import get_logger


class ToolCache:
    def __init__(self, config: dict[str, Any]):
        cache = config.get("cache", {}) or {}
        self.enabled = bool(cache.get("enabled", False))
        self.ttl_seconds = float(cache.get("ttl_hours", 24)) * 3600.0
        self.dir = Path(cache.get("dir") or (Path.home() / ".guardstrike" / "cache"))
        self.logger = get_logger(config)

    def _key(self, tool: str, target: str, params: dict[str, Any]) -> str:
        raw = f"{tool}|{target}|{json.dumps(params or {}, sort_keys=True, default=str)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _path(self, tool: str, target: str, params: dict[str, Any]) -> Path:
        return self.dir / f"{self._key(tool, target, params)}.json"

    def get(self, tool: str, target: str, params: dict[str, Any]) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        path = self._path(tool, target, params)
        try:
            if not path.exists():
                return None
            payload = json.loads(path.read_text(encoding="utf-8"))
            if time.time() - float(payload.get("stored_at", 0)) > self.ttl_seconds:
                return None
            return payload.get("result")
        except Exception as e:  # best-effort
            self.logger.debug(f"tool cache read miss ({path.name}): {e}")
            return None

    def put(self, tool: str, target: str, params: dict[str, Any], result: dict[str, Any]) -> None:
        if not self.enabled:
            return
        path = self._path(tool, target, params)
        payload = {"stored_at": time.time(), "tool": tool, "target": target, "result": result}
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", delete=False, dir=self.dir, prefix=".tmp_", suffix=".json", encoding="utf-8"
            ) as tmp:
                json.dump(payload, tmp, default=str)
                tmp_path = Path(tmp.name)
            os.replace(tmp_path, path)
        except Exception as e:  # best-effort
            self.logger.debug(f"tool cache write skipped ({path.name}): {e}")

    def count(self) -> int:
        try:
            return sum(1 for _ in self.dir.glob("*.json"))
        except Exception:
            return 0

    def clear(self) -> int:
        n = 0
        try:
            for f in self.dir.glob("*.json"):
                try:
                    f.unlink()
                    n += 1
                except Exception:
                    pass
        except Exception:
            pass
        return n
