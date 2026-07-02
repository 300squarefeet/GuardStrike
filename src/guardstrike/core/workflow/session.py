"""Atomic session checkpointing for resumable workflows."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from guardstrike.core.memory import PentestMemory
from guardstrike.utils.logger import get_logger


class SessionStore:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = get_logger(config)

    def _output_dir(self) -> Path:
        d = Path(self.config.get("output", {}).get("save_path", "./reports"))
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, memory: PentestMemory) -> None:
        output_dir = self._output_dir()
        final = output_dir / f"session_{memory.session_id}.json"
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=output_dir,
            prefix=f".session_{memory.session_id}_",
            suffix=".tmp",
            encoding="utf-8",
        ) as tmp:
            tmp_path = Path(tmp.name)
        try:
            memory.save_state(tmp_path)
            os.replace(tmp_path, final)
            self.logger.debug(f"Checkpoint saved: {final}")
        except Exception:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

    def resume(self, session_id: str, memory: PentestMemory) -> bool:
        state_file = self._output_dir() / f"session_{session_id}.json"
        if not state_file.exists():
            self.logger.error(f"Cannot resume: session file not found: {state_file}")
            return False
        return memory.load_state(state_file)
