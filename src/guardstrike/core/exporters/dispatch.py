"""Dispatch additional report exports (sarif / defectdojo / slack).

Kept separate from ``cli/commands/report.py`` so the export + push logic
is testable without the LLM report-generation path. Writes files and POSTs
to configured integrations; returns human-readable result lines.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from guardstrike.core.exporters import defectdojo, sarif, slack
from guardstrike.core.memory import PentestMemory


def run_exports(
    memory: PentestMemory,
    out_dir: Path,
    session_id: str,
    selectors: set[str],
    *,
    config: dict,
    defectdojo_url: str | None = None,
    defectdojo_engagement: int | None = None,
    slack_webhook: str | None = None,
) -> list[str]:
    """Run the selected exports. Returns result lines for the caller to print.

    Raises ValueError if 'slack' is selected without a webhook. A DefectDojo
    POST failure is caught and reported (never re-raised) — the JSON file is
    already on disk.
    """
    lines: list[str] = []
    for fmt in sorted(selectors):
        if fmt == "sarif":
            doc = sarif.export(memory)
            path = out_dir / f"report_{session_id}.sarif"
            path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
            lines.append(f"SARIF: {path}")

        elif fmt == "defectdojo":
            doc = defectdojo.export(memory)
            path = out_dir / f"report_{session_id}.defectdojo.json"
            path.write_text(json.dumps(doc, indent=2), encoding="utf-8")

            dd = config.get("integrations", {}).get("defectdojo", {})
            base_url = defectdojo_url or dd.get("base_url")
            engagement = defectdojo_engagement or dd.get("engagement_id")
            scan_type = dd.get("scan_type", "Generic Findings Import")
            token = os.environ.get("DEFECTDOJO_API_TOKEN")
            # Honour the config opt-in toggle. Explicit CLI flags are a
            # per-run opt-in that overrides integrations.defectdojo.enabled.
            enabled = bool(defectdojo_url or defectdojo_engagement or dd.get("enabled"))

            if enabled and base_url and engagement and token:
                try:
                    status = defectdojo.post(
                        base_url, token, int(engagement), doc, scan_type=scan_type
                    )
                    lines.append(f"DefectDojo: HTTP {status}")
                except Exception as e:  # noqa: BLE001 — report already written
                    lines.append(f"DefectDojo POST gagal: {e}. JSON tersimpan di {path}")
            else:
                lines.append(
                    f"DefectDojo JSON: {path} (set integrations.defectdojo "
                    f"base_url+engagement_id & DEFECTDOJO_API_TOKEN untuk auto-POST)"
                )

        elif fmt == "slack":
            if not slack_webhook:
                raise ValueError(
                    "slack export requires a webhook "
                    "(--slack-webhook or GUARDSTRIKE_SLACK_WEBHOOK)"
                )
            payload = slack.build_payload(memory)
            status = slack.post(slack_webhook, payload)
            lines.append(f"Slack/Discord: HTTP {status}")

    return lines
