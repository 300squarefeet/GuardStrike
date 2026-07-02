"""
Memory and context management for GuardStrike agents
Maintains state across the penetration testing workflow,
including a token ledger and thinking chain for full auditability.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Core data types
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    """Represents a security finding"""

    id: str
    severity: str  # critical, high, medium, low, info
    title: str
    description: str
    evidence: str
    tool: str
    target: str
    timestamp: str
    remediation: str | None = None
    cvss_score: float | None = None
    cvss_vector: str | None = None
    cwe: str | None = None
    cve: str | None = None
    owasp: str | None = None
    mitre_technique: str | None = None
    false_positive: bool = False
    execution_id: str | None = None  # Link to ToolExecution
    raw_evidence: str | None = None  # Full command output section
    merged_from: list[str] = field(default_factory=list)  # "tool:execution_id" of merged duplicates
    exploitability: float | None = None  # CVSS-vector exploitability sub-score
    exploit_available: bool | None = None  # public exploit reference found (NVD)
    exploit_refs: list[str] = field(default_factory=list)  # exploit reference URLs

    @property
    def duplicate_count(self) -> int:
        """1 (this finding) + number of merged duplicate contributors."""
        return 1 + len(self.merged_from)


@dataclass
class ToolExecution:
    """Represents a tool execution record"""

    tool: str
    command: str
    target: str
    timestamp: str
    exit_code: int
    output: str
    duration: float
    findings_count: int = 0
    id: str | None = None  # Unique execution ID for linking


@dataclass
class TokenUsage:
    """Records token consumption and estimated cost for one AI call"""

    timestamp: str
    agent: str  # Planner | ToolAgent | Analyst | Reporter
    model: str  # e.g. gpt-4o
    provider: str  # openai | gemini | claude | openrouter
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float  # estimated from config/guardstrike.yaml ai.pricing


@dataclass
class ThinkingStep:
    """Records a single reasoning step performed by an agent"""

    timestamp: str
    agent: str
    step_number: int
    prompt_summary: str  # first 300 chars of the prompt sent
    reasoning: str  # chain-of-thought text from the AI
    conclusion: str  # extracted decision / answer
    tokens_used: int
    round_number: int = 1  # 1 = first attempt, >1 = deep-think critique rounds


# ---------------------------------------------------------------------------
# Main memory class
# ---------------------------------------------------------------------------


class PentestMemory:
    """Manages penetration test state and context across all agents"""

    def __init__(self, target: str, session_id: str | None = None):
        self.target = target
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now().isoformat()

        # ── Phase tracking ──────────────────────────────────────────────────
        self.current_phase = "initialization"
        self.completed_actions: list[str] = []

        # ── Core stores ─────────────────────────────────────────────────────
        self.findings: list[Finding] = []
        self.tool_executions: list[ToolExecution] = []
        self.ai_decisions: list[dict[str, str]] = []

        # ── Extended memory ──────────────────────────────────────────────────
        self.token_ledger: list[TokenUsage] = []  # every AI call recorded
        self.thinking_chain: list[ThinkingStep] = []  # ordered reasoning history

        # ── Discovery context ────────────────────────────────────────────────
        self.context: dict[str, Any] = {
            "target": target,
            "scope": [],
            "discovered_assets": [],
            "open_ports": [],
            "services": [],
            "technologies": [],
            "subdomains": [],
            "waf_detected": None,
            "cms_detected": None,
        }

        # ── Threat model (built by PlannerAgent at session start) ────────────
        self.threat_model: str = ""  # free-text structured threat model
        self.attack_surface: list[str] = []  # enumerated high-value targets

    # ── Finding management ───────────────────────────────────────────────────

    def add_finding(self, finding: Finding):
        """Add a finding, merging it into an existing duplicate (same target +
        vulnerability identity) when one is present — see core/dedup."""
        from guardstrike.core.dedup import finding_dedup_key, merge_findings

        key = finding_dedup_key(finding)
        for existing in self.findings:
            if finding_dedup_key(existing) == key:
                merge_findings(existing, finding)
                return
        self.findings.append(finding)

    def add_tool_execution(self, execution: ToolExecution):
        """Record tool execution"""
        self.tool_executions.append(execution)

    def add_ai_decision(self, agent: str, decision: str, reasoning: str):
        """Record an AI agent decision"""
        self.ai_decisions.append(
            {
                "timestamp": datetime.now().isoformat(),
                "agent": agent,
                "decision": decision,
                "reasoning": reasoning,
            }
        )

    # ── Extended memory mutators ─────────────────────────────────────────────

    def add_token_usage(self, usage: TokenUsage):
        """Append one token-usage record to the ledger"""
        self.token_ledger.append(usage)

    def add_thinking_step(self, step: ThinkingStep):
        """Append one thinking step to the chain"""
        self.thinking_chain.append(step)

    def set_threat_model(self, model_text: str):
        """Store the structured threat model produced by the Planner"""
        self.threat_model = model_text

    def add_attack_surface_entry(self, entry: str):
        """Add a discovered attack-surface item"""
        if entry not in self.attack_surface:
            self.attack_surface.append(entry)

    # ── Token ledger aggregation ─────────────────────────────────────────────

    def get_token_summary(self) -> dict[str, Any]:
        """
        Compute cumulative token usage totals, grouped by provider and model.

        Returns a dict with:
          total_prompt_tokens, total_completion_tokens, total_tokens, total_cost_usd,
          by_provider: {provider: {tokens, cost}},
          by_model:    {model:    {tokens, cost}},
          by_agent:    {agent:    {tokens, cost}},
        """
        summary: dict[str, Any] = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "by_provider": {},
            "by_model": {},
            "by_agent": {},
        }

        for u in self.token_ledger:
            summary["total_prompt_tokens"] += u.prompt_tokens
            summary["total_completion_tokens"] += u.completion_tokens
            summary["total_tokens"] += u.total_tokens
            summary["total_cost_usd"] += u.cost_usd

            for group_key, group_name in [
                ("by_provider", u.provider),
                ("by_model", u.model),
                ("by_agent", u.agent),
            ]:
                bucket = summary[group_key].setdefault(
                    group_name, {"tokens": 0, "cost_usd": 0.0, "calls": 0}
                )
                bucket["tokens"] += u.total_tokens
                bucket["cost_usd"] += u.cost_usd
                bucket["calls"] += 1

        summary["total_cost_usd"] = round(summary["total_cost_usd"], 6)
        return summary

    # ── Phase management ─────────────────────────────────────────────────────

    def update_phase(self, phase: str):
        """Update current penetration testing phase"""
        self.current_phase = phase

    def mark_action_complete(self, action: str):
        """Mark an action as completed"""
        if action not in self.completed_actions:
            self.completed_actions.append(action)

    def update_context(self, key: str, value: Any):
        """Update context information (append to lists, overwrite scalars)"""
        if key in self.context and isinstance(self.context[key], list):
            if isinstance(value, list):
                self.context[key].extend(value)
            else:
                self.context[key].append(value)
        else:
            self.context[key] = value

    # ── Query helpers ────────────────────────────────────────────────────────

    def get_findings_by_severity(self, severity: str) -> list[Finding]:
        """Get real (non-FP) findings filtered by severity"""
        return [
            f
            for f in self.findings
            if f.severity.lower() == severity.lower() and not f.false_positive
        ]

    def get_findings_summary(self) -> dict[str, int]:
        """Get count of real findings per severity level"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in self.findings:
            if not finding.false_positive:
                severity = finding.severity.lower()
                if severity in summary:
                    summary[severity] += 1
        return summary

    def get_recent_thinking(self, n: int = 3) -> str:
        """Return the last n thinking steps formatted for AI context injection"""
        recent = self.thinking_chain[-n:] if len(self.thinking_chain) >= n else self.thinking_chain
        if not recent:
            return "No prior reasoning recorded."
        lines = []
        for step in recent:
            lines.append(
                f"[Step {step.step_number} | {step.agent} | Round {step.round_number}]\n"
                f"  Conclusion: {step.conclusion[:200]}"
            )
        return "\n".join(lines)

    def get_context_for_ai(self) -> str:
        """
        Format full session context for AI agents.
        Includes: target, phase, findings summary, assets, tech stack,
                  threat model excerpt, attack surface, and recent thinking.
        """
        fs = self.get_findings_summary()
        token_totals = self.get_token_summary()

        # Format services neatly
        services_str = (
            ", ".join(f"{s}" for s in self.context.get("services", [])) or "None discovered"
        )

        context_str = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SESSION CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Target:         {self.target}
Session ID:     {self.session_id}
Current Phase:  {self.current_phase}
Start Time:     {self.start_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 COMPLETED ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(f"  ✓ {a}" for a in self.completed_actions) or "  (none)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 FINDINGS SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  💀 Critical : {fs['critical']}
  🔴 High     : {fs['high']}
  🟠 Medium   : {fs['medium']}
  🟡 Low      : {fs['low']}
  ℹ️  Info     : {fs['info']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DISCOVERED ASSETS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subdomains   : {', '.join(self.context.get('subdomains', [])) or 'None'}
Open Ports   : {', '.join(map(str, self.context.get('open_ports', []))) or 'None'}
Services     : {services_str}
Technologies : {', '.join(self.context.get('technologies', [])) or 'None'}
WAF          : {self.context.get('waf_detected') or 'Not detected'}
CMS          : {self.context.get('cms_detected') or 'Not detected'}

Attack Surface Items:
{chr(10).join(f"  • {e}" for e in self.attack_surface) or "  (none mapped yet)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 THREAT MODEL (excerpt)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self.threat_model[:600] + "…" if len(self.threat_model) > 600 else self.threat_model or "(not yet built)"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 RECENT REASONING (last 3 steps)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{self.get_recent_thinking(3)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 TOKEN USAGE SO FAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total tokens : {token_totals['total_tokens']:,}
Est. cost    : ${token_totals['total_cost_usd']:.4f} USD
AI calls     : {len(self.token_ledger)}
""".strip()

        return context_str

    # ── Persistence ──────────────────────────────────────────────────────────

    def save_state(self, filepath: Path):
        """Serialize full memory state to JSON, including token ledger and thinking chain"""
        state = {
            "target": self.target,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "current_phase": self.current_phase,
            "completed_actions": self.completed_actions,
            "findings": [asdict(f) for f in self.findings],
            "tool_executions": [asdict(t) for t in self.tool_executions],
            "ai_decisions": self.ai_decisions,
            "token_ledger": [asdict(u) for u in self.token_ledger],
            "thinking_chain": [asdict(s) for s in self.thinking_chain],
            "threat_model": self.threat_model,
            "attack_surface": self.attack_surface,
            "context": self.context,
            "token_summary": self.get_token_summary(),
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def load_state(self, filepath: Path) -> bool:
        """Deserialize full memory state from JSON"""
        try:
            with open(filepath, encoding="utf-8") as f:
                state = json.load(f)

            self.target = state["target"]
            self.session_id = state["session_id"]
            self.start_time = state["start_time"]
            self.current_phase = state["current_phase"]
            self.completed_actions = state["completed_actions"]
            self.findings = [Finding(**f) for f in state["findings"]]
            self.tool_executions = [ToolExecution(**t) for t in state["tool_executions"]]
            self.ai_decisions = state["ai_decisions"]
            self.token_ledger = [TokenUsage(**u) for u in state.get("token_ledger", [])]
            self.thinking_chain = [ThinkingStep(**s) for s in state.get("thinking_chain", [])]
            self.threat_model = state.get("threat_model", "")
            self.attack_surface = state.get("attack_surface", [])
            self.context = state["context"]

            return True
        except Exception:
            return False
