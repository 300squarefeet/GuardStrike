"""Resolve packaged data (workflows, default config) and user overrides.

Built-in workflows ship inside the package (``importlib.resources``) so they
resolve after ``pip install``. User workflows are layered on top from the
current working directory and the user home, overriding built-ins by stem.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def _package_dir(subdir: str) -> Path:
    return Path(str(resources.files("guardstrike") / subdir))


def builtin_workflows_dir() -> Path:
    return _package_dir("workflows")


def default_config_path() -> Path:
    return _package_dir("data") / "guardstrike.yaml"


def _user_workflow_dirs() -> list[Path]:
    return [Path.cwd() / "workflows", Path.home() / ".guardstrike" / "workflows"]


def iter_workflow_files() -> list[Path]:
    """Built-in workflows plus user dirs; user stems override built-ins."""
    by_stem: dict[str, Path] = {}
    for yaml_file in sorted(builtin_workflows_dir().glob("*.yaml")):
        by_stem[yaml_file.stem.lower()] = yaml_file
    for d in _user_workflow_dirs():
        if d.is_dir():
            for yaml_file in sorted(d.glob("*.yaml")):
                by_stem[yaml_file.stem.lower()] = yaml_file
    return list(by_stem.values())


def find_workflow(name: str) -> Path | None:
    """Exact stem match first, then fuzzy substring match (either direction)."""
    files = iter_workflow_files()
    target = name.lower()
    for f in files:
        if f.stem.lower() == target:
            return f
    for f in files:
        stem = f.stem.lower()
        if stem in target or target in stem:
            return f
    return None
