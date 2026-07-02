"""Resolve a workflow name to a parsed YAML document."""

from __future__ import annotations

import logging
from typing import Any

import yaml

from guardstrike.utils.resources import find_workflow

_FALLBACK: dict[str, Any] = {
    "version": 2,
    "name": "fallback",
    "steps": [
        {"id": "subdomain_discovery", "type": "tool", "tool": "subfinder"},
        {
            "id": "port_scanning",
            "type": "tool",
            "tool": "nmap",
            "depends_on": ["subdomain_discovery"],
        },
        {"id": "analysis", "type": "analysis", "depends_on": ["port_scanning"]},
    ],
}


class WorkflowLoader:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def load_doc(self, workflow_name: str) -> dict[str, Any]:
        workflow_file = find_workflow(workflow_name)
        if workflow_file is None:
            self.logger.warning(f"Workflow file not found for '{workflow_name}' — using fallback")
            return dict(_FALLBACK)
        self.logger.info(f"Loading workflow: {workflow_file.name}")
        with open(workflow_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
