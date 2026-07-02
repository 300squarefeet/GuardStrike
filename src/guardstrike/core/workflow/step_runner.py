"""Executes a single workflow step (tool/analysis/report) or AI decision."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from guardstrike.core.memory import PentestMemory, ToolExecution
from guardstrike.core.workflow.session import SessionStore


class StepRunner:
    def __init__(
        self,
        config: dict[str, Any],
        target: str,
        memory: PentestMemory,
        tool_agent,
        analyst,
        reporter,
        scope_validator,
        logger,
        assume_yes: bool,
        console: Console | None,
        gemini_client,
    ):
        self.config = config
        self.target = target
        self.memory = memory
        self.tool_agent = tool_agent
        self.analyst = analyst
        self.reporter = reporter
        self.scope_validator = scope_validator
        self.logger = logger
        self.assume_yes = assume_yes
        self._console = console
        self.gemini_client = gemini_client  # passed to DebateTriage/VisualTriage
        # Save-on-crash in execute_ai_decision needs an atomic checkpoint path;
        # mirrors the engine's SessionStore (same config-derived save_path).
        self.session = SessionStore(config)

    async def execute_step(self, step: dict[str, Any]) -> dict[str, Any] | None:
        """Execute a workflow step with streaming output and AI thinking display.

        Returns the tool result dict (``success``/``command``/``exit_code``/
        ``raw_output``/``parsed``) for a successful tool step, else ``None``.
        The caller uses this return value to build the DSL v2 Jinja context, so
        concurrent steps in one generation never clobber each other (the result
        lives in the coroutine frame, not on shared instance state).
        """
        step_type = step.get("type", "tool")
        con = self._console  # may be None — all prints are guarded
        step_result: dict[str, Any] | None = None

        # ── TOOL step ────────────────────────────────────────────────────────
        if step_type == "tool":
            tool_name = step["tool"]
            objective = step.get("objective", f"Execute {tool_name}")

            # Confirmation gate (item 6: wire dead config). Active+ tools
            # require explicit user approval unless --yes was passed or
            # pentest.require_confirmation is false in config.
            if not self._confirm_tool(tool_name, step):
                if con:
                    con.print(
                        Panel(
                            f"[yellow]User declined to run [bold]{tool_name}[/bold] — step skipped.[/yellow]",
                            title="[yellow]SKIPPED[/yellow]",
                            border_style="yellow",
                        )
                    )
                self.logger.warning(f"Step '{step['name']}' skipped by user confirmation gate")
                self.memory.mark_action_complete(step["name"])
                return

            if con:
                con.print(Rule(f"[bold cyan]TOOL  {tool_name.upper()}[/bold cyan]", style="cyan"))
                con.print(f"  [dim]Objective:[/dim] {objective}")
                con.print(f"  [dim]Target   :[/dim] [yellow]{self.target}[/yellow]\n")

            self.logger.info(f"Tool Agent selecting tool: {tool_name}")

            # Build a line-by-line stream callback for Rich
            def _stream(line: str):
                if con and line.strip():
                    try:
                        con.print(line, markup=True, highlight=False)
                    except Exception:
                        con.print(line, markup=False)

            result = await self.tool_agent.execute_tool(
                tool_name=tool_name,
                target=self.target,  # always the exact CLI target
                stream_callback=_stream,
                **step.get("parameters", {}),
            )

            if result.get("skipped"):
                if con:
                    con.print(
                        Panel(
                            f"[yellow]Tool [bold]{tool_name}[/bold] is not installed — step skipped.[/yellow]\n"
                            f"Install it and re-run, or remove this step from the workflow.",
                            title="[yellow]SKIPPED[/yellow]",
                            border_style="yellow",
                        )
                    )
                self.logger.warning(
                    f"Step '{step['name']}' skipped — tool {tool_name} not available"
                )

            elif result.get("success"):
                # Record execution with unique ID
                import time

                execution_id = f"{tool_name}_{int(time.time() * 1000)}"

                execution = ToolExecution(
                    id=execution_id,
                    tool=tool_name,
                    command=result.get("command", ""),
                    target=self.target,
                    timestamp=datetime.now().isoformat(),
                    exit_code=result.get("exit_code", 0),
                    output=result.get("raw_output", ""),
                    duration=result.get("duration", 0),
                )
                self.memory.add_tool_execution(execution)

                # Hand the full tool result back to the caller so DSL v2 can
                # pull ``parsed``, ``success``, etc. into downstream Jinja
                # context — returned, not stashed, so concurrent steps are safe.
                step_result = result

                # Re-validate any newly discovered hosts before downstream steps
                # consume them. A recon tool returning a host that resolves into
                # a blacklisted range must not propagate to a follow-on scanner.
                self._validate_discovered_hosts(tool_name, result.get("parsed", {}))

                # Analyst AI thinking panel
                self.logger.info("Analyst Agent analyzing results...")
                if con:
                    con.print(Rule("[bold green]AI ANALYST[/bold green]", style="green"))

                analysis = await self.analyst.interpret_output(
                    tool=tool_name,
                    target=self.target,
                    command=result.get("command", ""),
                    output=result.get("raw_output", ""),
                    execution_id=execution_id,
                )

                if con and analysis.get("reasoning"):
                    con.print(
                        Panel(
                            Text(analysis["reasoning"][:600], style="dim"),
                            title="[cyan]Analyst Reasoning[/cyan]",
                            border_style="cyan",
                            expand=False,
                        )
                    )

                self.logger.info(f"Found {len(analysis['findings'])} findings from {tool_name}")
                if con:
                    colour = "red" if analysis["findings"] else "green"
                    con.print(f"  [{colour}]Findings: {len(analysis['findings'])}[/{colour}]\n")

            else:
                err = result.get("error", "unknown error")
                self.logger.warning(f"Tool execution failed: {err}")
                if con:
                    con.print(f"  [red]Tool failed:[/red] {err}\n")

        # ── ANALYSIS step ────────────────────────────────────────────────────
        elif step_type == "analysis":
            agent_kind = (step.get("agent") or "analyst").lower()

            # Three-role debate triage — run on every MEDIUM-fp finding.
            if agent_kind == "debate" or step.get("type_subtype") == "triage_debate":
                if con:
                    con.print(Rule("[bold magenta]TRIAGE DEBATE[/bold magenta]", style="magenta"))

                from guardstrike.core.agents.debate_triage import DebateTriage

                triage = DebateTriage(self.config, self.gemini_client, self.memory)
                ambiguous = [
                    f
                    for f in self.memory.findings
                    if DebateTriage._extract_fp_probability(f) == "MEDIUM"
                ]
                self.logger.info(f"Debate triage: {len(ambiguous)} ambiguous findings to debate")

                for finding in ambiguous:
                    verdict = await triage.triage(finding)
                    self.logger.info(
                        f"Debate verdict for {finding.id}: {verdict.verdict} "
                        f"(severity → {verdict.adjusted_severity})"
                    )
                    # Apply judge's adjustments to the in-memory finding.
                    if verdict.verdict == "FALSE_POSITIVE":
                        finding.false_positive = True
                    finding.severity = verdict.adjusted_severity
                    if verdict.rationale:
                        finding.description = (
                            f"{finding.description}\n\n[Triage Verdict — "
                            f"{verdict.verdict}, conf={verdict.confidence}] "
                            f"{verdict.rationale}"
                        )

                if con:
                    fp_count = sum(1 for f in self.memory.findings if f.false_positive)
                    con.print(
                        f"  [green]Debate complete[/green]: "
                        f"{len(ambiguous)} debated, {fp_count} flagged as FP\n"
                    )
                return

            # Visual triage — vision-LLM enriches findings with screenshot evidence.
            if agent_kind == "visual" or step.get("type_subtype") == "visual_triage":
                if con:
                    con.print(Rule("[bold magenta]VISUAL TRIAGE[/bold magenta]", style="magenta"))

                from guardstrike.core.agents.visual_triage import VisualTriage

                visual = VisualTriage(self.config, self.gemini_client, self.memory)
                result = await visual.triage_findings()
                if result.get("skipped_reason"):
                    self.logger.info(f"Visual triage skipped: {result['skipped_reason']}")
                    if con:
                        con.print(f"  [yellow]Skipped:[/yellow] {result['skipped_reason']}\n")
                else:
                    n = len(result.get("enrichments", []))
                    self.logger.info(f"Visual triage enriched {n} findings")
                    if con:
                        con.print(f"  [green]Enriched[/green] {n} findings with image evidence\n")
                return

            if con:
                con.print(
                    Rule("[bold magenta]AI CORRELATION ANALYSIS[/bold magenta]", style="magenta")
                )

            self.logger.info("Running correlation analysis...")
            analysis = await self.analyst.correlate_findings()
            self.logger.info("Correlation analysis complete")

            if con and analysis.get("analysis"):
                # Show a trimmed preview
                preview = analysis["analysis"][:800]
                con.print(
                    Panel(
                        Text(preview, style="white"),
                        title="[magenta]Correlation Result[/magenta]",
                        border_style="magenta",
                        expand=False,
                    )
                )

        # ── REPORT step ──────────────────────────────────────────────────────
        elif step_type == "report":
            config_format = self.config.get("output", {}).get("format", "markdown")
            report_format = step.get("format", config_format)

            if con:
                con.print(
                    Rule(
                        f"[bold blue]AI REPORTER — {report_format.upper()}[/bold blue]",
                        style="blue",
                    )
                )

            self.logger.info(f"Generating {report_format} report...")
            report = await self.reporter.execute(format=report_format)

            output_dir = Path(self.config.get("output", {}).get("save_path", "./reports"))
            output_dir.mkdir(parents=True, exist_ok=True)
            extension_map = {"markdown": "md", "html": "html", "json": "json"}
            extension = extension_map.get(report_format, "md")
            report_file = output_dir / f"report_{self.memory.session_id}.{extension}"

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report["content"])

            self.logger.info(f"Report saved to: {report_file}")
            if con:
                con.print(
                    f"  [green]Report saved:[/green] [link={report_file}]{report_file}[/link]\n"
                )

        self.memory.mark_action_complete(step["name"])
        return step_result

    def _confirm_tool(self, tool_name: str, step: dict[str, Any]) -> bool:
        """Return True if the tool should run, False to skip.

        Honors ``pentest.require_confirmation`` from config and the ``--yes``
        CLI flag. Passive tools always proceed. Active/intrusive/destructive
        tools prompt unless the user has waived confirmation. In safe_mode,
        destructive tools are blocked even with --yes (they need an explicit
        config opt-out).
        """
        from guardstrike.core.tool_agent import TOOL_RISK_CLASS

        risk = TOOL_RISK_CLASS.get(tool_name, "active")
        require = self.config.get("pentest", {}).get("require_confirmation", True)
        safe_mode = self.config.get("pentest", {}).get("safe_mode", True)

        # Block destructive tools in safe_mode regardless of --yes.
        if risk == "destructive" and safe_mode:
            self.logger.warning(
                f"Tool {tool_name} is destructive and safe_mode is on — skipping. "
                "Set pentest.safe_mode=false in config to enable."
            )
            return False

        # Passive tools never prompt.
        if risk == "passive":
            return True

        # Confirmation disabled or pre-approved.
        if not require or self.assume_yes:
            return True

        # Interactive prompt.
        try:
            import typer

            params = step.get("parameters", {}) or {}
            param_str = ", ".join(f"{k}={v}" for k, v in params.items()) or "(defaults)"
            msg = (
                f"\n  Tool      : {tool_name} [risk: {risk}]\n"
                f"  Target    : {self.target}\n"
                f"  Parameters: {param_str}\n"
                f"  Run this tool?"
            )
            if self._console:
                self._console.print(msg)
            return typer.confirm("  Confirm", default=False)
        except Exception as e:
            # Non-interactive context (no TTY) — fall through to skip rather
            # than silently auto-approve.
            self.logger.warning(
                f"Could not prompt for confirmation ({e}); skipping {tool_name}. "
                "Pass --yes for unattended runs."
            )
            return False

    def _validate_discovered_hosts(self, tool_name: str, parsed: dict[str, Any]):
        """Re-run scope validation for hosts a tool discovered.

        Recon tools (subfinder/amass/dnsrecon) and probers (httpx/nmap) emit
        hostnames or IPs in their parsed output. Without re-validation, a
        downstream step could scan an out-of-scope or blacklisted host that
        the initial single-target check never saw.

        Logs SCOPE_VIOLATION for each rejected host. Does not abort the
        workflow — abort is the responsibility of the consuming step that
        chooses to act on those hosts. Today nothing consumes parsed cross-step
        (DSL v1 has no var-passing), so this is a tripwire + audit log until
        DSL v2 lands; at that point variable interpolation will read from a
        filtered host list.
        """
        if not isinstance(parsed, dict):
            return

        candidate_keys = (
            "subdomains",
            "alive_hosts",
            "hosts",
            "live_hosts",
            "found_hosts",
            "results",
            "targets",
        )
        candidates: list[str] = []
        for key in candidate_keys:
            val = parsed.get(key)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        candidates.append(item)
                    elif isinstance(item, dict):
                        for h_key in ("host", "url", "ip", "address", "subdomain"):
                            h = item.get(h_key)
                            if isinstance(h, str):
                                candidates.append(h)
                                break

        rejected: list[str] = []
        for host in candidates:
            ok, reason = self.scope_validator.validate_target(host)
            if not ok:
                rejected.append(f"{host} ({reason})")

        if rejected:
            self.logger.warning(
                f"[{tool_name}] {len(rejected)} discovered host(s) failed scope re-validation: "
                + "; ".join(rejected[:5])
                + (f" (+{len(rejected) - 5} more)" if len(rejected) > 5 else "")
            )

    async def execute_ai_decision(self, decision: dict[str, Any]):
        """Execute an AI-decided action.

        This is the autonomous-loop counterpart to ``execute_step``. It MUST
        keep the Finding ⇄ ToolExecution linkage that the workflow path
        provides, otherwise findings emitted from autonomous mode lose their
        evidence trail entirely.

        Three things this method gets right that the original did not:
          * Mints an ``execution_id`` and passes it to ``analyst.interpret_output``
            so findings carry the link.
          * Records the ``ToolExecution`` exactly once (the ToolAgent path
            already records on success — passing ``record_execution=False``
            would be cleaner, but the current ToolAgent contract records
            unconditionally on success, so we don't add a second record here).
          * Wraps any exception in a session save so a crash doesn't lose
            partial findings.
        """
        action = decision.get("next_action", "")
        self.logger.info(f"Executing AI decision: {action}")

        try:
            tool_selection = await self.tool_agent.execute(
                objective=action,
                target=self.target,
            )
            tool_name = tool_selection["tool"]

            # Confirmation gate also applies in autonomous mode.
            fake_step = {"name": action, "parameters": {}}
            if not self._confirm_tool(tool_name, fake_step):
                self.logger.warning(f"Autonomous step '{action}' skipped by confirmation gate")
                self.memory.mark_action_complete(action)
                return

            result = await self.tool_agent.execute_tool(
                tool_name=tool_name,
                target=self.target,
            )

            if result.get("success"):
                # Mint the execution_id the same way the workflow path does
                # so analyst-emitted Findings carry their evidence link.
                import time

                execution_id = f"{tool_name}_{int(time.time() * 1000)}"

                # Update the most-recent ToolExecution record (added by
                # ToolAgent.execute_tool) with the id so the link is consistent
                # with what we hand to the analyst. Avoids double-recording.
                if self.memory.tool_executions:
                    last = self.memory.tool_executions[-1]
                    if last.tool == tool_name and last.id is None:
                        last.id = execution_id

                # Re-validate any newly discovered hosts.
                self._validate_discovered_hosts(tool_name, result.get("parsed", {}))

                analysis = await self.analyst.interpret_output(
                    tool=tool_name,
                    target=self.target,
                    command=result.get("command", ""),
                    output=result.get("raw_output", ""),
                    execution_id=execution_id,
                )
                self.logger.info(f"Found {len(analysis['findings'])} new findings (autonomous)")

            # Honor planner-declared phase transition if present.
            phase_t = decision.get("phase_transition")
            if isinstance(phase_t, str) and phase_t in {
                "reconnaissance",
                "scanning",
                "analysis",
                "reporting",
            }:
                if phase_t != self.memory.current_phase:
                    self.logger.info(
                        f"Planner advancing phase: {self.memory.current_phase} → {phase_t}"
                    )
                    self.memory.update_phase(phase_t)

        except Exception as e:
            self.logger.error(f"Failed to execute AI decision: {e}")
            # Persist whatever findings we have so a crash mid-loop doesn't
            # lose evidence collected before the failure.
            self.session.save(self.memory)

        self.memory.mark_action_complete(action)
