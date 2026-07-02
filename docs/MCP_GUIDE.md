# GuardStrike MCP Server

Expose GuardStrike workflows to MCP clients (Claude Desktop / Code) over stdio.

## Install

```bash
pip install -e ".[mcp]"
```

## Run

```bash
guardstrike mcp                 # uses config/guardstrike.yaml
guardstrike mcp --provider ollama   # no cloud API key (local LLM)
```

## Tools exposed

| Tool | Args | Notes |
|---|---|---|
| `list_workflows` | — | Names + descriptions of built-in + user workflows |
| `run_workflow` | `name, target, assume_yes=false` | Scope-validated; active scans require `assume_yes=true`; destructive blocked by safe_mode |
| `get_report` | `session_id, fmt=md` | Read-only; returns a saved report |
| `kb_query` | `query, top_k=5` | Offline CVE/CWE/MITRE lookup |

## Claude Desktop config

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "guardstrike": { "command": "guardstrike", "args": ["mcp"] }
  }
}
```

## Authorization

Only run against targets you are explicitly authorized to test. Scope
blacklists (RFC1918 by default) are enforced on every `run_workflow`.

## No-API mode

`run_workflow` runs GuardStrike's own agents, which need an LLM. Set
`ai.provider: ollama` (or pass `--provider ollama`) to run entirely on a local
model with no cloud API key.
