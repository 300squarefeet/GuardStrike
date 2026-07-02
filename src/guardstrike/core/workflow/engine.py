"""Orchestrates the penetration testing workflow (DAG scheduler)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from rich.console import Console

from guardstrike.ai.budget import CostBudgetExceeded, TokenBudgetExceeded
from guardstrike.core.memory import PentestMemory
from guardstrike.core.workflow.loader import WorkflowLoader
from guardstrike.core.workflow.session import SessionStore
from guardstrike.core.workflow.step_runner import StepRunner
from guardstrike.utils.logger import get_logger
from guardstrike.utils.scope_validator import ScopeValidator

if TYPE_CHECKING:
    from guardstrike.core.workflow_schema import WorkflowStep


def _progress_line(
    done: int, total: int, phase: str = "", group: tuple[int, int] | None = None
) -> str:
    """Deterministic one-line progress marker for a workflow run.

    YAML (group given):     '▸ group 2/5 · 3/12 steps · scanning'
    Autonomous (no group):  '▸ step 4/20 · analysis'
    """
    if group is not None:
        g, total_g = group
        head = f"▸ group {g}/{total_g} · {done}/{total} steps"
    else:
        head = f"▸ step {done}/{total}"
    ph = phase.strip()
    return f"{head} · {ph}" if ph else head


class WorkflowEngine:
    """Orchestrates the penetration testing workflow"""

    def __init__(self, config: dict[str, Any], target: str, assume_yes: bool = False):
        self.config = config
        self.target = target
        self.logger = get_logger(config)
        self.assume_yes = assume_yes

        # Initialize components
        self.memory = PentestMemory(target)
        self.scope_validator = ScopeValidator(config)
        # Resolve GeminiClient through the package namespace so tests can patch
        # ``guardstrike.core.workflow.GeminiClient`` (the monolith's surface).
        from guardstrike.core import workflow as _workflow_pkg

        self.gemini_client = _workflow_pkg.GeminiClient(config)

        # Initialize all agents
        from guardstrike.core.analyst_agent import AnalystAgent
        from guardstrike.core.planner import PlannerAgent
        from guardstrike.core.reporter_agent import ReporterAgent
        from guardstrike.core.tool_agent import ToolAgent

        self.planner = PlannerAgent(config, self.gemini_client, self.memory)
        self.tool_agent = ToolAgent(config, self.gemini_client, self.memory)
        self.analyst = AnalystAgent(config, self.gemini_client, self.memory)
        self.reporter = ReporterAgent(config, self.gemini_client, self.memory)

        # Workflow state
        self.is_running = False
        self.current_step = 0
        self.max_steps = config.get("workflows", {}).get("max_steps", 20)

        # Rich console for real-time display (set by CLI layer)
        self._console: Console | None = None

        # Bounded collaborators (Task 3 split).
        self.loader = WorkflowLoader(self.logger)
        self.session = SessionStore(config)
        self._runner = self._build_runner()

    def _build_runner(self) -> StepRunner:
        return StepRunner(
            self.config,
            self.target,
            self.memory,
            self.tool_agent,
            self.analyst,
            self.reporter,
            self.scope_validator,
            self.logger,
            self.assume_yes,
            self._console,
            self.gemini_client,
        )

    # Back-compat shim: tests/test_workflow_resume.py calls this directly.
    def _save_session(self) -> None:
        self.session.save(self.memory)

    # Back-compat shim: tests/test_workflow_confirmation.py calls this directly.
    def _confirm_tool(self, tool_name: str, step: dict[str, Any]) -> bool:
        return self._runner._confirm_tool(tool_name, step)

    def set_console(self, console: Console):
        """Wire a Rich console for streaming output and AI panel display."""
        self._console = console
        self._runner._console = console

    async def run_workflow(self, workflow_name: str) -> dict[str, Any]:
        """
        Run a predefined workflow.

        Loads YAML, compiles to a DAG, executes generation-by-generation
        with up to ``max_parallel_tools`` concurrent steps per generation.
        Both v1 (linear) and v2 (DAG) YAML schemas accepted — v1 is migrated
        in-memory by the compiler so existing workflows keep working.

        Returns:
            Workflow results and findings
        """
        from guardstrike.core.workflow_schema import WorkflowCompileError, compile_workflow

        self.logger.info(f"Starting workflow: {workflow_name} for target: {self.target}")

        # Validate target
        is_valid, reason = self.scope_validator.validate_target(self.target)
        if not is_valid:
            self.logger.error(f"Target validation failed: {reason}")
            raise ValueError(f"Invalid target: {reason}")

        self.is_running = True
        self.memory.update_phase(f"{workflow_name}_workflow")

        try:
            doc = self.loader.load_doc(workflow_name)
            try:
                compiled = compile_workflow(doc)
            except WorkflowCompileError as e:
                self.logger.error(f"Workflow compile failed: {e}")
                raise

            # Concurrency cap from config; honored per-generation.
            max_parallel = max(
                1,
                int(self.config.get("pentest", {}).get("max_parallel_tools", 3)),
            )
            sem = asyncio.Semaphore(max_parallel)
            self.logger.info(
                f"Workflow '{compiled.name}' has {len(compiled.steps)} steps "
                f"in {len(compiled.levels)} generations (max_parallel={max_parallel})"
            )

            # Per-step result store, used as the Jinja2 context for downstream
            # steps. Keyed by step.id.
            step_results: dict[str, dict[str, Any]] = {}

            for gen_idx, level in enumerate(compiled.levels):
                if not self.is_running:
                    break
                self.logger.info(f"Generation {gen_idx + 1}/{len(compiled.levels)}: {level}")

                if self._console:
                    done = sum(len(lvl) for lvl in compiled.levels[:gen_idx])
                    self._console.print(
                        _progress_line(
                            done,
                            len(compiled.steps),
                            phase=self.memory.current_phase,
                            group=(gen_idx + 1, len(compiled.levels)),
                        ),
                        style="bold cyan",
                    )

                async def _run_one(step_id: str) -> None:
                    step = compiled.steps[step_id]
                    if step_id in self.memory.completed_actions:
                        self.logger.info(f"Skipping '{step_id}' — already completed (resumed)")
                        return
                    async with sem:
                        result = await self._execute_compiled_step(step, step_results)
                        step_results[step_id] = result
                        # Atomic checkpoint after each step.
                        self._save_session()

                await asyncio.gather(*[_run_one(sid) for sid in level])

            if self._console:
                self._console.print(
                    f"[bold green]✓ workflow complete[/bold green] — "
                    f"{len(compiled.steps)} steps, {len(self.memory.findings)} findings"
                )

            # Generate final analysis
            analysis = await self.planner.analyze_results()

            self._save_session()

            return {
                "status": "completed",
                "findings": len(self.memory.findings),
                "analysis": analysis,
                "session_id": self.memory.session_id,
            }

        except (TokenBudgetExceeded, CostBudgetExceeded) as e:
            self.logger.warning(f"Budget reached — stopping workflow: {e}")
            self._save_session()
            return {
                "status": "stopped_budget",
                "reason": str(e),
                "findings": len(self.memory.findings),
                "session_id": self.memory.session_id,
            }
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            self._save_session()
            raise
        finally:
            self.is_running = False

    async def run_autonomous(self) -> dict[str, Any]:
        """
        Run autonomous pentest where AI decides each step

        Returns:
            Final results
        """
        self.logger.info(f"Starting autonomous pentest for target: {self.target}")

        # Validate target
        is_valid, reason = self.scope_validator.validate_target(self.target)
        if not is_valid:
            raise ValueError(f"Invalid target: {reason}")

        self.is_running = True
        self.memory.update_phase("reconnaissance")

        try:
            while self.is_running and self.current_step < self.max_steps:
                # Ask planner for next action
                decision = await self.planner.decide_next_action()

                self.logger.info(f"AI Decision: {decision.get('next_action')}")
                self.logger.debug(f"Reasoning: {decision.get('reasoning', 'N/A')}")

                # Check if we should stop
                if decision.get("next_action", "").lower() in ["done", "complete", "finish"]:
                    self.logger.info("Planner decided workflow is complete")
                    break

                if self._console:
                    self._console.print(
                        _progress_line(
                            self.current_step + 1,
                            self.max_steps,
                            phase=self.memory.current_phase,
                        ),
                        style="bold cyan",
                    )

                # Execute the decided action
                await self._runner.execute_ai_decision(decision)

                self.current_step += 1
                # Atomic per-step checkpoint (item 10).
                self._save_session()

            if self._console:
                self._console.print(
                    f"[bold green]✓ autonomous run complete[/bold green] — "
                    f"{self.current_step} steps, {len(self.memory.findings)} findings"
                )

            # Final analysis
            analysis = await self.planner.analyze_results()

            self._save_session()

            return {
                "status": "completed",
                "findings": len(self.memory.findings),
                "analysis": analysis,
                "session_id": self.memory.session_id,
            }

        except (TokenBudgetExceeded, CostBudgetExceeded) as e:
            self.logger.warning(f"Budget reached — stopping workflow: {e}")
            self._save_session()
            return {
                "status": "stopped_budget",
                "reason": str(e),
                "findings": len(self.memory.findings),
                "session_id": self.memory.session_id,
            }
        except Exception as e:
            self.logger.error(f"Autonomous workflow failed: {e}")
            self._save_session()
            raise
        finally:
            self.is_running = False

    def stop(self):
        """Stop the workflow"""
        self.logger.info("Stopping workflow")
        self.is_running = False

    async def _execute_compiled_step(
        self,
        step: WorkflowStep,  # type: ignore[name-defined]
        prior: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute one compiled step, returning a result dict for Jinja context.

        The returned dict shape mirrors a tool result so downstream ``when``
        expressions and ``parameters`` can reference ``<id>.parsed.<key>``,
        ``<id>.success``, etc.
        """
        from guardstrike.core.workflow_schema import (
            WorkflowCompileError,
            evaluate_when,
            render_parameters,
        )

        # Evaluate ``when`` against prior results.
        try:
            should_run = evaluate_when(step.when, prior)
        except WorkflowCompileError as e:
            self.logger.error(f"Step '{step.id}' when-expr failed: {e}")
            return {"success": False, "skipped": True, "error": str(e)}

        if not should_run:
            self.logger.info(f"Step '{step.id}' skipped — when-expr evaluated false")
            self.memory.mark_action_complete(step.id)
            return {"success": False, "skipped": True, "reason": "when-false"}

        # Render parameters with prior results in scope.
        try:
            rendered_params = render_parameters(dict(step.parameters or {}), prior)
        except WorkflowCompileError as e:
            self.logger.error(f"Step '{step.id}' parameter render failed: {e}")
            return {"success": False, "skipped": True, "error": str(e)}

        # Bridge to the existing v1 step executor by building a v1-shaped dict.
        v1_step: dict[str, Any] = {
            "name": step.id,
            "type": step.type,
            "objective": step.objective,
            "parameters": rendered_params,
        }
        if step.tool:
            v1_step["tool"] = step.tool
        if step.agent:
            v1_step["agent"] = step.agent

        # execute_step returns this step's own result (or None for non-tool /
        # skipped / failed steps). Build the DSL v2 prior-step context from the
        # return value — never from shared state or ``tool_executions[-1]``,
        # both of which race when steps in a generation run concurrently.
        result = await self._runner.execute_step(v1_step) or {}
        succeeded = bool(result.get("success")) and result.get("exit_code", -1) == 0
        return {
            "id": step.id,
            "success": succeeded,
            "command": result.get("command", ""),
            "exit_code": result.get("exit_code", -1),
            "parsed": result.get("parsed", {}),
            "raw_output": (result.get("raw_output", "") or "")[:8000],
        }

    def resume_session(self, session_id: str) -> bool:
        ok = self.session.resume(session_id, self.memory)
        if ok:
            self.target = self.memory.target
            self._runner.target = self.memory.target
            self.current_step = len(self.memory.completed_actions)
            self.logger.info(
                f"Resumed session {session_id} at phase '{self.memory.current_phase}' "
                f"with {len(self.memory.findings)} findings, "
                f"{self.current_step} steps already completed"
            )
        return ok
