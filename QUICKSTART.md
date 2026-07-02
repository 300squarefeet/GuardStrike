# GuardStrike Quick Start Guide

## Installation (Windows)

1. **Navigate to project directory**:
   ```cmd
   cd c:\Users\MyBook Hype AMD\workarea\guardstrike
   ```

2. **Create virtual environment**:
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install GuardStrike**:
   ```cmd
   pip install -e .
   ```

4. **Initialize configuration**:
   ```cmd
   python -m guardstrike init
   ```
   Or use the batch launcher:
   ```cmd
   .\guardstrike.bat init
   ```

5. **Configure AI Provider Credentials**:

   Create a `.env` file with your provider key (any one is enough):
   ```cmd
   echo OPENAI_API_KEY=sk-your-key-here > .env
   ```

   Other supported keys: `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENROUTER_API_KEY`.

## Common Commands

### List Available Workflows
```cmd
python -m guardstrike workflow list
```

### Dry Run Reconnaissance
```cmd
python -m guardstrike recon --domain example.com --dry-run
```

### Run Port Scan (requires nmap)
```cmd
python -m guardstrike scan --target scanme.nmap.org
```

### Run Full Workflow
```cmd
python -m guardstrike workflow run --name recon --target example.com
```

### Run with Specific AI Model
```cmd
python -m guardstrike recon --domain example.com --model gemini-3-pro
```

### Use Local LLM (Ollama)
```cmd
set OLLAMA_HOST=http://localhost:11434
python -m guardstrike workflow run --name recon --target scanme.nmap.org --provider ollama
```

### Use OpenAI-Compatible Endpoint (vLLM / LM Studio / Together / Groq)
```cmd
python -m guardstrike workflow run --name web_pentest --target example.com --provider openai_compatible
```

## v4 Quick Wins

### Knowledge Base Grounding (RAG)
```cmd
python -m guardstrike kb seed
python -m guardstrike kb query "log4j JNDI" --top 5
```
Then enable in `config/guardstrike.yaml`:
```yaml
rag:
  enabled: true
  top_k: 5
```

### Multi-Agent Debate Triage
```cmd
python -m guardstrike workflow run --name web_pentest_with_debate --target https://example.com
```

### Visual Triage (vision-LLM)
Install Playwright once:
```cmd
pip install playwright
python -m playwright install chromium
```
Run:
```cmd
python -m guardstrike workflow run --name web_visual_pentest --target https://example.com --provider openai
```

### Output Exporters (SARIF / DefectDojo / Slack)
```cmd
python -m guardstrike report --session 20260203_175905 --export sarif --export slack ^
  --slack-webhook https://hooks.slack.com/services/...
```

### Telemetry + Learned Ranker
```cmd
python -m guardstrike telemetry export ./reports --out telemetry.jsonl
python -m guardstrike telemetry train telemetry.jsonl
```
Enable:
```yaml
ai:
  use_learned_ranker: true
```

## Configuration

Edit `config/guardstrike.yaml` or `~/.guardstrike/guardstrike.yaml` to customize:
- AI model and settings (incl. `judge_model`, `use_learned_ranker`, `rag.enabled`)
- Tool configurations
- Security guardrails (`safe_mode`, `require_confirmation`, scope)
- Output formats and exporter endpoints

## Getting Help

```cmd
python -m guardstrike --help
python -m guardstrike <command> --help
python -m guardstrike kb --help
python -m guardstrike telemetry --help
```

## Important Notes

- **Windows**: Use `python -m guardstrike` or `.\guardstrike.bat` instead of `guardstrike`
- **API Key**: Required for cloud AI providers; not required for Ollama
- **External Tools**: Optional but recommended — GuardStrike degrades gracefully when a tool is missing
- **Authorization**: Only scan systems you have explicit permission to test

## Troubleshooting

### Command not found
- Make sure you're in the project directory
- Activate the virtual environment
- Use `python -m guardstrike` instead of `guardstrike`

### Import errors
- Reinstall dependencies: `pip install -e .`
- Check Python version: `python --version` (requires 3.11+)

### API errors
- Verify your provider API key in `.env` or `.guardstrike/.env`
- Check internet connectivity
- For Ollama: ensure `ollama serve` is running on `OLLAMA_HOST`

### Vision triage skipped
- Install Playwright: `pip install playwright && python -m playwright install chromium`
- Vision requires gpt-4o / Claude 3.5+ / gpt-4-turbo as active provider

## Next Steps

1. Install external pentest tools for full functionality
2. Review `config/guardstrike.yaml` and customize settings
3. Run `--dry-run` mode to see what would be executed
4. Start with safe targets like `scanme.nmap.org`
5. Review logs in `logs/guardstrike.log`
6. Read [docs/V4_FEATURES.md](docs/V4_FEATURES.md) for the full v4.0 feature reference
7. See [CHANGELOG.md](CHANGELOG.md) for version history
