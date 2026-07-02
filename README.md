<div align="center">

<img src="docs/logo.svg" alt="GuardStrike Logo" width="200" />

# 🔐 GuardStrike

### AI-Powered Penetration Testing Automation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**GuardStrike** is an enterprise-grade AI-powered penetration testing automation framework that orchestrates a multi-agent engine over 9 pluggable AI providers (OpenAI, Claude, Gemini, OpenRouter, Requesty, Ollama, OpenAI-compatible, and keyless local gateways like Antigravity and 9Router) and 50 battle-tested security tools. It delivers intelligent, adaptive assessments with cross-provider fallback, deterministic attack-chain detection, worst-first finding prioritization, an MCP server surface, and turnkey SARIF/DefectDojo/Slack reporting — all with full evidence traceability.

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## ⚠️ Legal Disclaimer

**GuardStrike is designed exclusively for authorized security testing and educational purposes.**

- ✅ **Legal Use**: Authorized penetration testing, security research, educational environments
- ❌ **Illegal Use**: Unauthorized access, malicious activities, any form of cyber attack

**You are fully responsible for ensuring you have explicit written permission before testing any system.** Unauthorized access to computer systems is illegal under laws including the Computer Fraud and Abuse Act (CFAA), GDPR, and equivalent international legislation.

**By using GuardStrike, you agree to use it only on systems you own or have explicit authorization to test.**

---

## ✨ Features

### 🤖 Multi-Provider AI Intelligence

- **9 AI Providers Supported**: OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini), OpenRouter, **Requesty**, **Ollama (local)**, **OpenAI-compatible (vLLM, LM Studio, Together, Groq)**, **Antigravity (keyless — via a local OpenAI-compatible proxy)**, **9Router (keyless — local gateway to 40+ providers / 100+ models with free tiers; `guardstrike models --live` lists the full live catalog straight from your gateway)**
- **Cross-Provider Fallback + Budget Caps**: transient / model-not-found errors fail over across the configured provider chain; a per-run token and USD budget stops the run cleanly before overspend
- **Plugin Provider Contract**: Third-party providers ship via `[project.entry-points."guardstrike.providers"]` — no fork required
- **Multi-Agent Architecture**: Specialized AI agents (Planner, Tool Selector, Analyst, Reporter) plus debate triage roles (Red Advocate, Blue Advocate, Judge) and Visual Triage
- **Multi-Agent Debate Triage**: Three-role red/blue/judge debate on ambiguous findings — F1 ≥ single-agent baseline +5pp
- **Vision-LLM Visual Triage**: Headless screenshot capture + image-grounded analyst enrichment via gpt-4o / Claude 3.5+ / Gemini 1.5+
- **RAG Knowledge Base**: SQLite + FTS5 grounded retrieval over CVE / CWE / MITRE ATT&CK feeds — kills hallucinated CVE refs
- **Judge Model Routing**: `think_deeply` swap-and-restore — big model thinks, small model judges, ~10x cost reduction
- **Learned Tool Selection**: Offline ranker trained on session telemetry; abstains when low-confidence and falls back to LLM selector
- **Adaptive Testing**: AI adjusts tactics based on discovered vulnerabilities and prior tool yields
- **False Positive Filtering**: Debate triage cuts noise; cheap path skips when fp_probability is decisive

### 🛠️ Extensive Tool Arsenal

**50 Integrated Security Tools across 10 categories:**

| Category | Tools |
|---|---|
| **Network** | nmap, masscan |
| **Web Reconnaissance** | httpx, whatweb, wafw00f, cmseek |
| **Subdomain / DNS** | subfinder, amass, dnsrecon |
| **Vulnerability Scanning** | nuclei, nikto, sqlmap, wpscan |
| **SSL/TLS Testing** | testssl, sslyze |
| **Content Discovery** | gobuster, ffuf, arjun |
| **Security Analysis** | xsstrike, gitleaks |
| **Cloud / Container / SBOM** | trivy, grype, syft, scoutsuite, prowler, kube-bench |
| **Modern Web + OSINT** | graphw00f, clairvoyance, jwt_tool, shodan, theharvester |
| **SAST + Secrets (B11)** | semgrep, trufflehog, dependency-check |
| **API Fuzzers (B10)** | schemathesis, cariddi, restler |
| **Burp/ZAP Bridge (B13)** | zap, burp |
| **LLM Red-Team (B12)** | garak, pyrit, prompt_fuzz |
| **Mobile Android (B9)** | mobsf, apkleaks, objection |
| **Active Directory (B8)** | netexec, bloodhound, kerbrute, impacket-secretsdump |
| **Vision Evidence (A3)** | playwright_screenshot |

### 📊 Enhanced Evidence Capture

- **Execution Traceability**: Every finding linked to its source tool execution via `execution_id`
- **Complete Command History**: Full tool output preserved with each finding
- **Raw Evidence Storage**: Output snippets bound to findings
- **Visual Evidence**: Screenshots captured per URL, attached to web findings
- **Session Reconstruction**: Atomic-checkpointed `session_<id>.json` enables `--resume`

### 🧠 Intelligent Analysis Engine

- **Finding Deduplication**: merges duplicate findings across tools by vulnerability identity (CVE, else CWE + normalized title) per target, preserving every contributor's `tool:execution_id` so evidence traceability is never lost
- **Deterministic Attack-Chain Detection**: a rule engine correlates per-target findings into known chains — SSRF→Cloud Metadata, SQLi→Data Breach, XSS→Account Takeover, IDOR+Weak-Auth→Horizontal Escalation, Path-Traversal/LFI→RCE, and more — rendered as a guaranteed **Attack Chains** report section (complements, not replaces, the LLM correlation)
- **Worst-First Prioritization**: findings ordered by a transparent lexicographic key (severity → attack-chain membership → CVSS → corroboration count), surfaced as a **Prioritized Findings** triage table and used to order the technical narrative

### 🔄 Smart Workflow System (DSL v2)

- **DAG Scheduler**: Steps with `depends_on` run in parallel up to `max_parallel_tools`
- **Jinja2 Templates (sandboxed)**: `parameters: {key: "{{ <id>.parsed.alive_hosts }}"}` resolves against prior step results
- **Conditional Steps**: `when:` clauses gate execution on prior output
- **Resume**: `--resume` picks up after the last completed step
- **Parameter Priority**: Workflow YAML > config block > tool defaults
- **Custom Agents**: `agent: debate | visual | analyst` on analysis steps
- **Multiple Report Formats**: Markdown, HTML, JSON

### 📤 Output Integrations (B14)

- **SARIF v2.1.0**: GitHub-friendly, includes `security-severity`, dedup `fingerprints` from `execution_id`
- **DefectDojo**: Direct REST upload
- **Slack**: Webhook posts with severity colour-coding
- **Triggered via**: `guardstrike report --export sarif --export defectdojo --export slack`
- **DefectDojo API push**: with `integrations.defectdojo` configured (base_url + engagement + `DEFECTDOJO_API_TOKEN`), `--export defectdojo` POSTs straight to the DefectDojo import-scan API; otherwise it writes the JSON for manual import

### 🔌 MCP Server & CLI Experience

- **MCP Server**: `guardstrike mcp` exposes workflows, reports, and the knowledge base over stdio for Claude Desktop / Claude Code — a read-only surface by default (`list_workflows`, `run_workflow`, `get_report`, `kb_query`); active/intrusive tools stay opt-in per call
- **Discoverability**: `guardstrike tools list|info` (browse the 50-tool arsenal with install status + risk class), `guardstrike config show` (resolved config with secrets masked), and shell completion (`--install-completion`)
- **Live Workflow Progress**: deterministic per-step progress lines (`▸ group 2/5 · 3/12 steps · scanning`) during long runs, without corrupting streamed tool output
- **Clean CLI**: banner only on the bare invocation, config-driven session/report paths, and actionable not-found errors

### 🔒 Security & Compliance

- **DNS-Resolve Scope Validation**: Closes SSRF-class bypass; private RFC1918 ranges blacklisted
- **Prompt-Injection Defense**: All tool output wrapped via `<UNTRUSTED_TOOL_OUTPUT>` delimiters + ANSI strip
- **API Key Scrubbing**: Logs and reports redact secrets at write time
- **Confirmation Gate**: Active+ tools (intrusive/destructive) require explicit user approval
- **Audit Logging**: Rotating logs of every AI decision and action
- **Safe Mode**: Prevents destructive actions by default

### 📋 Professional Reporting

- **CVSS v3.1 Recomputation**: Validates claimed scores against vector math; flags drift
- **Executive Summaries**: Non-technical overviews
- **Technical Deep-Dives**: Findings with evidence, CVSS, CWE, CVE, MITRE technique
- **AI Decision Traces**: Token usage, cost, thinking-chain ledger per agent
- **Visual Triage Sections**: Image-grounded enrichment baked into descriptions

### ⚡ Performance & Efficiency

- **Async Throughout**: Tool exec via `asyncio` subprocess; agents async
- **Lazy Tool Loading**: 50 tools registered, none imported until needed — `--help` stays under 500ms
- **Parallel DAG Execution**: Independent steps run concurrently per generation
- **Workflow Automation**: 13+ shipped workflows (recon, web, network, AD, mobile, LLM red-team, SAST, API)

---

## 📋 Prerequisites

### Required

- **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
- **AI Provider API Key** (Choose one):
  - OpenAI API Key ([Get it here](https://platform.openai.com/api-keys))
  - Anthropic API Key ([Get it here](https://console.anthropic.com/))
  - Google AI Studio API Key ([Get it here](https://makersuite.google.com/app/apikey))
  - OpenRouter API Key ([Get it here](https://openrouter.ai/keys))
  - Requesty API Key ([Get it here](https://app.requesty.ai/api-keys))
- **Git** (for cloning repository)

### Optional Tools (for full functionality)

GuardStrike can intelligently use these tools if installed:

| Tool | Purpose | Installation |
|------|---------|--------------|
| **nmap** | Port scanning | `apt install nmap` / `choco install nmap` |
| **masscan** | Ultra-fast scan | `apt install masscan` / Build from source |
| **httpx** | HTTP probing | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| **subfinder** | Subdomain enum | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| **amass** | Network mapping | `go install github.com/owasp-amass/amass/v4/...@master` |
| **nuclei** | Vuln scanning | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| **whatweb** | Tech fingerprint | `gem install whatweb` / `apt install whatweb` |
| **wafw00f** | WAF detection | `pip install wafw00f` |
| **nikto** | Web vuln scan | `apt install nikto` |
| **sqlmap** | SQL injection | `pip install sqlmap` / `apt install sqlmap` |
| **wpscan** | WordPress scan | `gem install wpscan` |
| **testssl** | SSL/TLS testing | Download from [testssl.sh](https://testssl.sh/) |
| **sslyze** | SSL/TLS analysis | `pip install sslyze` |
| **gobuster** | Directory brute | `go install github.com/OJ/gobuster/v3@latest` |
| **ffuf** | Web fuzzing | `go install github.com/ffuf/ffuf/v2@latest` |
| **arjun** | Parameter discovery | `pip install arjun` |
| **xsstrike** | Advanced XSS | `git clone https://github.com/s0md3v/XSStrike` |
| **gitleaks** | Secret scanning | `go install github.com/zricethezav/gitleaks/v8@latest` |
| **cmseek** | CMS detection | `pip install cmseek` |
| **dnsrecon** | DNS enumeration | `pip install dnsrecon` |

> **Note**: GuardStrike works without external tools but with limited scanning capabilities. The AI will adapt based on available tools.

---

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/300squarefeet/GuardStrike.git
cd guardstrike
```

### Step 2: Set Up Python Environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -e .
```

### Step 3: Configure AI Provider

GuardStrike supports multiple AI providers. Configure your preferred provider in `config/guardstrike.yaml`:

```yaml
# config/guardstrike.yaml
ai:
  # Choose your provider: openai, claude, gemini, openrouter, or requesty
  provider: openai
  
  # OpenAI Configuration (recommended)
  openai:
    model: gpt-4o
    api_key: sk-your-api-key-here  # Or set OPENAI_API_KEY env var
  
  # Claude Configuration
  claude:
    model: claude-3-5-sonnet-20241022
    api_key: null  # Or set ANTHROPIC_API_KEY env var
  
  # Gemini Configuration
  gemini:
    model: gemini-2.5-pro
    api_key: null  # Or set GOOGLE_API_KEY env var
  
  # OpenRouter Configuration
  openrouter:
    model: anthropic/claude-3.5-sonnet
    api_key: null  # Or set OPENROUTER_API_KEY env var

  # Requesty Configuration (OpenAI-compatible gateway)
  requesty:
    model: openai/gpt-4o-mini
    api_key: null  # Or set REQUESTY_API_KEY env var
```

**Or use environment variables:**

```bash
# Linux/macOS
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GOOGLE_API_KEY="your-gemini-key"
export OPENROUTER_API_KEY="your-router-key"
export REQUESTY_API_KEY="your-requesty-key"

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Step 4: Initialize Configuration

```bash
# Verify installation
python -m guardstrike --help

# Check AI provider status
python -m guardstrike models
```

---

## 🎯 Quick Start

### Basic Commands

```bash
# List available workflows
python -m guardstrike workflow list

# View AI providers and models
python -m guardstrike models

# Run with specific provider
python -m guardstrike workflow run --name web_pentest --target example.com --provider openai
```

### Example Usage Scenarios

#### 1. Quick Web Application Pen Test
```bash
# Fast security check with evidence capture
python -m guardstrike workflow run --name web_pentest --target https://dvwa.csalab.app
```

**Expected Output:**
- ✅ HTTP discovery with httpx
- ✅ Vulnerability scan with nuclei
- ✅ Full evidence linking (commands + outputs)
- ✅ Markdown report with findings

#### 2. Comprehensive Network Assessment
```bash
# Full network penetration test
python -m guardstrike workflow run --name network --target 192.168.1.0/24
```

#### 3. Custom Workflow with Parameters
```bash
# Run with workflow-specific parameters
# Parameters in workflow YAML override config defaults
python -m guardstrike workflow run --name web_pentest --target example.com
```

**Workflow Parameter Priority:**
1. Workflow YAML parameters (highest priority)
2. Config file parameters
3. Tool defaults (lowest priority)

#### 4. Generate Report from Session
```bash
# Create HTML report with evidence
python -m guardstrike report --session 20260203_175905 --format html
```

#### 5. Switch AI Providers
```bash
# Use OpenAI GPT-4
python -m guardstrike workflow run --name web_pentest --target example.com --provider openai

# Use Claude
python -m guardstrike workflow run --name web_pentest --target example.com --provider claude

# Use Gemini
python -m guardstrike workflow run --name web_pentest --target example.com --provider gemini

# Local Ollama (no cloud)
OLLAMA_HOST=http://localhost:11434 python -m guardstrike workflow run --name recon --target scanme.nmap.org --provider ollama

# Any OpenAI-compatible endpoint (vLLM, LM Studio, Together, Groq)
python -m guardstrike workflow run --name web_pentest --target example.com --provider openai_compatible

# Antigravity — keyless, via a local Antigravity OpenAI-compatible proxy (default http://localhost:3000/v1)
python -m guardstrike workflow run --name recon --target scanme.nmap.org --provider antigravity

# 9Router — keyless, via a local 9Router gateway (default http://localhost:20128/v1); free-tier models
python -m guardstrike workflow run --name recon --target scanme.nmap.org --provider 9router
```

#### 6. Knowledge Base (RAG grounding)
```bash
# Seed bundled offline corpus
python -m guardstrike kb seed

# Show corpus stats
python -m guardstrike kb status

# Ad-hoc retrieval
python -m guardstrike kb query "log4j JNDI" --top 5

# Ingest external feed (NVD JSON / MITRE STIX / nuclei metadata)
python -m guardstrike kb update --kind cve --file ./nvd-2025.json
```

Enable analyst grounding in `config/guardstrike.yaml`:
```yaml
rag:
  enabled: true
  top_k: 5
```

#### 7. Multi-agent Debate Triage
```bash
# Workflow YAML uses agent: debate on an analysis step
python -m guardstrike workflow run --name web_pentest_with_debate --target https://example.com
```

Three roles (red advocate, blue advocate, judge) debate ambiguous findings only — confident verdicts skip the debate to bound token cost.

#### 8. Visual Triage (vision-LLM)
```bash
# Captures full-page screenshots and feeds them to a vision-capable provider
python -m guardstrike workflow run --name web_visual_pentest --target https://example.com --provider openai
```

Requires playwright: `pip install playwright && python -m playwright install chromium`. Skipped silently when active provider has no vision support.

#### 9. Output Exporters (SARIF / DefectDojo / Slack)
```bash
# SARIF (GitHub code-scanning friendly)
python -m guardstrike report --session 20260203_175905 --export sarif

# Multiple sinks at once
python -m guardstrike report --session 20260203_175905 --export sarif --export defectdojo --export slack \
  --slack-webhook https://hooks.slack.com/services/...
```

#### 10. Telemetry + Learned Ranker (offline)
```bash
# Anonymise sessions into JSONL (no raw targets, no commands, no secrets)
python -m guardstrike telemetry export ./reports --out telemetry.jsonl

# Train the offline tool ranker
python -m guardstrike telemetry train telemetry.jsonl

# Inspect what the ranker learned
python -m guardstrike telemetry status
```

Enable in config:
```yaml
ai:
  use_learned_ranker: true   # ToolAgent calls ranker before LLM selector
```

> **Windows Users**: Use `python -m guardstrike` instead of `guardstrike`

---

## 🔧 Configuration

### Complete Configuration Reference

Edit `config/guardstrike.yaml` to customize GuardStrike's behavior:

```yaml
# AI Configuration
ai:
  provider: openai  # openai, claude, gemini, openrouter, requesty
  
  openai:
    model: gpt-4o
    api_key: sk-your-key  # Or use OPENAI_API_KEY env var
  
  claude:
    model: claude-3-5-sonnet-20241022
    api_key: null
  
  gemini:
    model: gemini-2.5-pro
    api_key: null
  
  temperature: 0.2
  max_tokens: 8000

# Penetration Testing Settings
pentest:
  safe_mode: true              # Prevent destructive actions
  require_confirmation: true   # Confirm before each step
  max_parallel_tools: 3        # Concurrent tool execution
  max_depth: 3                 # Maximum scan depth
  tool_timeout: 300            # Tool timeout in seconds

# Output Configuration
output:
  format: markdown             # markdown, html, json
  save_path: ./reports
  include_reasoning: true
  verbosity: normal            # quiet, normal, verbose, debug

# Scope Validation
scope:
  blacklist:                   # Never scan these
    - 127.0.0.0/8
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16
  require_scope_file: false
  max_targets: 100

# Tool Configuration (defaults)
tools:
  httpx:
    threads: 50
    timeout: 10
    tech_detect: true
  
  nuclei:
    severity: ["critical", "high", "medium"]
    templates_path: ~/nuclei-templates
  
  nmap:
    default_args: "-sV -sC"
    timing: T4
```

### Workflow Parameters

Create custom workflows in `workflows/` directory:

```yaml
# workflows/custom_web.yaml
name: custom_web_assessment
description: Custom web security testing

steps:
  - name: http_discovery
    type: tool
    tool: httpx
    parameters:
      threads: 100        # Override config default (50)
      timeout: 15         # Override config default (10)
      tech_detect: true
  
  - name: vulnerability_scan
    type: tool
    tool: nuclei
    parameters:
      severity: ["critical", "high"]  # Override config
      templates_path: ".shared/nuclei/templates/"
  
  - name: generate_report
    type: report
    # Format will use config default (markdown)
```

**Parameter Priority:**
- Workflow parameters **override** config parameters
- Config parameters **override** tool defaults
- Self-contained, reusable workflows

---

## 📖 Documentation

### User Guides
- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Command Reference](docs/)** - Detailed documentation for all commands
- **[Configuration Guide](config/guardstrike.yaml)** - Complete configuration reference
- **[Workflow Guide](docs/WORKFLOW_GUIDE.md)** - Creating custom workflows
- **[Eval Guide](docs/EVAL_GUIDE.md)** - Running and extending the eval harness
- **[Plugin Guide](docs/PLUGIN_GUIDE.md)** - Shipping third-party providers and tools
- **[Changelog](CHANGELOG.md)** - Version history and migration notes

### MCP Server

GuardStrike ships a built-in MCP stdio server that exposes its workflows, reporting, and knowledge-base tools to any MCP client (Claude Desktop, Claude Code, etc.). Install the optional dependency, then start the server:

```bash
pip install -e ".[mcp]"
guardstrike mcp
```

See **[docs/MCP_GUIDE.md](docs/MCP_GUIDE.md)** for the full tools table, Claude Desktop config snippet, authorization notes, and no-API/Ollama mode.

### Developer Guides
- **[Creating Custom Tools](docs/TOOLS_DEVELOPMENT_GUIDE.md)** - Build your own tool integrations
- **[Workflow Development](docs/WORKFLOW_GUIDE.md)** - Create custom testing workflows
- **[Available Tools](tools/README.md)** - Overview of integrated tools

### Architecture Overview

```
GuardStrike Architecture:
┌─────────────────────────────────────────┐
│         AI Provider Layer               │
│  (OpenAI, Claude, Gemini, OpenRouter,   │
│   Requesty)                             │
└─────────────────────────────────────────┘
                 │
┌─────────────────────────────────────────┐
│       Multi-Agent System                │
│  Planner → Tool Agent → Analyst →      │
│            Reporter                      │
└─────────────────────────────────────────┘
                 │
┌─────────────────────────────────────────┐
│      Workflow Engine                    │
│  - Parameter Priority                   │
│  - Evidence Capture                     │
│  - Session Management                   │
└─────────────────────────────────────────┘
                 │
┌─────────────────────────────────────────┐
│      Tool Integration Layer             │
│  (50 Security Tools)                    │
└─────────────────────────────────────────┘
```

---

## 🏗️ Project Structure

```
guardstrike/
├── ai/                    # AI integration
│   └── providers/         # Multi-provider support
│       ├── base_provider.py
│       ├── openai_provider.py
│       ├── claude_provider.py
│       ├── gemini_provider.py
│       ├── openrouter_provider.py
│       └── requesty_provider.py
├── cli/                   # Command-line interface
│   └── commands/         # CLI commands (init, scan, recon, etc.)
├── core/                  # Core agent system
│   ├── agent.py          # Base agent
│   ├── planner.py        # Planner agent
│   ├── tool_agent.py     # Tool selection agent
│   ├── analyst_agent.py  # Analysis agent
│   ├── reporter_agent.py # Reporting agent
│   ├── memory.py         # State management
│   └── workflow.py       # Workflow orchestration
├── tools/                 # Pentesting tool wrappers
│   ├── nmap.py           # Nmap integration
│   ├── masscan.py        # Masscan integration
│   ├── httpx.py          # httpx integration
│   ├── subfinder.py      # Subfinder integration
│   ├── amass.py          # Amass integration
│   ├── nuclei.py         # Nuclei integration
│   ├── sqlmap.py         # SQLMap integration
│   ├── wpscan.py         # WPScan integration
│   ├── whatweb.py        # WhatWeb integration
│   ├── wafw00f.py        # Wafw00f integration
│   ├── nikto.py          # Nikto integration
│   ├── testssl.py        # TestSSL integration
│   ├── sslyze.py         # SSLyze integration
│   ├── gobuster.py       # Gobuster integration
│   ├── ffuf.py           # FFuf integration
│   └── ...               # 50 tools total
├── workflows/             # Workflow definitions (YAML)
├── utils/                 # Utilities (logging, validation)
├── config/                # Configuration files
├── docs/                  # Documentation
└── reports/               # Generated reports
```

---

## 🆕 Latest Updates

### Version 4.0.0 — Novel R&D + Coverage Expansion

**Track A — AI/Agent R&D (7 items)**

| ID | Item | Highlights |
|---|---|---|
| A1 | RAG knowledge base | `core/knowledge_base.py` SQLite + FTS5 + optional embeddings; analyst grounding via `kb_references` slot; `guardstrike kb {seed,update,query,status}` |
| A2 | Multi-agent debate triage | Red/Blue/Judge over MEDIUM-fp findings only; new analysis step type `agent: debate` |
| A3 | Vision-LLM screenshot analysis | `tools/playwright_screenshot.py` + `core/agents/visual_triage.py`; OpenAI + Claude `generate_with_images` |
| A4 | Plugin contract + local providers | Entry-point discovery for providers AND tools; **Ollama** + **OpenAI-compatible** providers shipped |
| A5 | Learned tool selection (offline) | `core/learners/tool_ranker.py` + `core/telemetry.py`; opt-in via `ai.use_learned_ranker: true` |
| A6 | Eval harness | `evals/{__init__,scoring,fixtures_loader,test_*}.py` + golden fixtures; 3 tiers (parser, workflow, agent grounding) |
| A7 | Judge model upgrade | `BaseAgent.think_deeply(judge_model=...)` swap-and-restore; transcript-judging for ~10x cost reduction |

**Track B — Tool Coverage Expansion (7 items)**

| ID | Category | Tools Added |
|---|---|---|
| B8 | Active Directory | netexec, bloodhound, kerbrute, impacket-secretsdump |
| B9 | Mobile Android | mobsf, apkleaks, objection |
| B10 | API fuzzers | schemathesis, restler, cariddi |
| B11 | SAST + secrets | semgrep, trufflehog, dependency-check |
| B12 | LLM red-team | garak, pyrit, prompt_fuzz |
| B13 | Burp/ZAP bridge | zap, burp |
| B14 | Output exporters | SARIF v2.1.0, DefectDojo, Slack |

**Quality bar:**
- 299 tests, 296 passing, 3 known-failing stubs (`TestMarkdownToHtml`), 7 skipped (+93% from v3 baseline of 153)
- All v3 hardening preserved: prompt-injection delimiters, key scrub, DNS-resolve scope, atomic checkpoints, log rotation, lazy tool loading
- `guardstrike --help` startup time stays <500ms despite 50 tools
- New CLI surfaces: `guardstrike kb`, `guardstrike telemetry`
- 8 new shipped workflows: `web_pentest_with_debate`, `web_visual_pentest`, `ad_assessment`, `mobile_android`, `llm_redteam`, `sast_review`, `api_pentest_v2`, plus existing v3 workflows

### Version 3.0.0 — Hardening + Engine v2

- Prompt-injection delimiters (`<UNTRUSTED_TOOL_OUTPUT>`) on all tool output
- DAG scheduler, Pydantic schemas, atomic checkpoints, `--resume`
- 11 new wrappers (cloud/container/SBOM/GraphQL/JWT/OSINT)
- CVSS v3.1 recomputation + drift detection
- Log rotation, key scrub at write time
- Confirmation gate wired for active+ tools

### Version 2.0.0

- Multi-provider AI (OpenAI, Claude, Gemini, OpenRouter, Requesty)
- Evidence linking via `execution_id`
- Workflow parameter priority system

---

## 🤝 Contributing

We welcome contributions! Here's how:

### Setting Up Development Environment

```bash
# Fork and clone
git clone https://github.com/300squarefeet/GuardStrike.git
cd guardstrike

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Format code
black .
```

### Contribution Areas

- 🤖 **AI Provider Integrations** - Add more AI models
- 🛠️ **New Tool Integrations** - Add more security tools
- 🔄 **Custom Workflows** - Share your workflow templates
- 🐛 **Bug Fixes** - Report and fix issues
- 📚 **Documentation** - Improve guides and examples
- 🧪 **Testing** - Expand test coverage

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📊 Roadmap

**Shipped in v4.0.0:**
- [x] Multi-provider AI (OpenAI, Claude, Gemini, OpenRouter, Requesty, Ollama, OpenAI-compatible)
- [x] Plugin entry-point contract for providers AND tools
- [x] RAG knowledge base (CVE/CWE/MITRE)
- [x] Multi-agent debate triage (red/blue/judge)
- [x] Vision-LLM visual triage with screenshots
- [x] Learned tool selection (offline ranker)
- [x] Judge-model routing for cost reduction
- [x] Eval harness (parser fixtures, workflow integration, agent grounding)
- [x] AD / Mobile / API-fuzz / SAST / LLM red-team / Burp-ZAP / Vision tool tracks
- [x] SARIF + DefectDojo + Slack exporters
- [x] CVSS v3.1 recomputation
- [x] DAG workflow engine with `--resume`

**Future:**
- [ ] Web Dashboard for visualization
- [ ] PostgreSQL backend for multi-session analytics
- [ ] Real-time multi-operator collaboration
- [ ] Custom LLM fine-tuning pipeline once telemetry corpus matures
- [ ] Plugin marketplace / hub UI

---

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Reinstall dependencies
pip install -e . --force-reinstall
```

**AI Provider Errors**
```bash
# Verify API key is set
python -m guardstrike models

# Check provider configuration
cat config/guardstrike.yaml | grep -A 5 "ai:"
```

**Tool Not Found**
```bash
# Check tool availability
which nmap
which httpx

# Install missing tools (see Prerequisites)
```

**Workflow Not Loading**
```bash
# Check workflow file exists
ls workflows/web_pentest.yaml

# Verify YAML syntax
python -c "import yaml; yaml.safe_load(open('workflows/web_pentest.yaml'))"
```

**Windows Command Not Found**
```powershell
# Use full command
python -m guardstrike --help
```

For more help, [open an issue](https://github.com/300squarefeet/GuardStrike/issues).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 capabilities
- **Anthropic** - Claude AI
- **Google** - Gemini AI
- **LangChain** - AI orchestration framework
- **ProjectDiscovery** - Open-source security tools (httpx, subfinder, nuclei)
- **Nmap** - Network exploration and security auditing
- **The Security Community** - Tool developers and researchers

---

## 📞 Support & Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/300squarefeet/GuardStrike/issues)
- **Discussions**: [Join community discussions](https://github.com/300squarefeet/GuardStrike/discussions)
- **Documentation**: [Read the docs](docs/)
- **Security**: Report vulnerabilities privately to security@example.com

---

## 🌟 Star History

<a href="https://github.com/300squarefeet/GuardStrike/stargazers">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=300squarefeet/GuardStrike&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=300squarefeet/GuardStrike&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=300squarefeet/GuardStrike&type=Date" />
  </picture>
</a>

---
---

<div align="center">

**GuardStrike** - Intelligent, Ethical, Automated Penetration Testing

Made with ❤️ by the Security Community

[⬆ Back to Top](#-guardstrike)

</div>
