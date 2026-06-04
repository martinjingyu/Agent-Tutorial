# General Run Agent

This repo is now a compact general-purpose tool-use agent. The core code lives in `research_agent/`.

It supports:

- LLM tool-call agent loop
- Browser tools with per-run isolated browser state
- Optional shared Chrome profile for retained login sessions
- File read/search/write/patch tools
- Terminal tool
- Persistent memory
- Local skill library
- Session save/resume
- Automatic context compaction and large-result spill-to-disk
- Guardian restart flow for self-fixes

## Setup

Install Python dependencies:

```powershell
pip install -r requirements.txt
```

Choose one provider.

DeepSeek API key mode:

```powershell
$env:AGENT_PROVIDER="deepseek"
$env:DEEPSEEK_API_KEY="your-key"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
$env:DEEPSEEK_THINKING="disabled"
```

Codex API mode:

```powershell
codex login
$env:AGENT_PROVIDER="codex"
$env:CODEX_MODEL="gpt-5.4"
```

Codex mode reads the OAuth access token from `%USERPROFILE%\.codex\auth.json` by default. You can override with:

```powershell
$env:CODEX_HOME="C:\path\to\.codex"
$env:CODEX_BASE_URL="https://chatgpt.com/backend-api/codex"
$env:CODEX_MAX_RETRIES="8"
$env:CODEX_RETRY_SLEEP="3.5"
```

Generic OpenAI-compatible mode also works:

```powershell
$env:AGENT_PROVIDER="openai"
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_MODEL="gpt-4o-mini"
```

Optional workspace override:

```powershell
$env:AGENT_WORKSPACE_ROOT="C:\Users\LX034\Code"
```

## Run

Single task:

```powershell
python .\run_agent.py "Use the browser to research X, then save a markdown report under reports/."
```

Provider/model can also be selected per command:

```powershell
python .\run_agent.py --provider deepseek --model deepseek-v4-flash "Do the task."
python .\run_agent.py --provider codex --model gpt-5.4 "Do the task."
```

Interactive chat:

```powershell
python .\run_agent.py --chat
```

Resume a saved session:

```powershell
python .\run_agent.py --resume 20260526_141013 "Continue from the last state and finish the report."
python .\run_agent.py --resume .\sessions\20260526_141013.json --chat
```

Guardian mode:

```powershell
python .\run_agent.py --guardian "Run the task. If you find a bug in your own source, fix it and restart."
```

`run_research_agent.py` remains as a compatibility alias for old commands.

## Browser Session

The browser tool launches Chrome through the local CDP controller in `research_agent/tools/cli.js`.

Each Python process gets:

- its own CDP port
- its own `.agentbrowser/<pid>/refs.json`
- its own scratch profile when a shared profile exists

Prepare a reusable shared browser profile from your existing Chrome profile:

```powershell
python .\run_agent.py --setup-browser-profile
```

Or open a manual login session:

```powershell
python .\run_agent.py --login-browser
```

After login, close Chrome completely. Future agent runs copy `research_agent/.agentbrowser/profiles/shared` into a per-run scratch profile, so cookies are reused but the shared profile is not mutated during the run.

## Project Layout

```text
research_agent/
  agent.py              # general tool-call loop, compaction, session save, restart hook
  browser_profile.py    # shared/scratch browser profile management
  cli.py                # command-line entry point
  context.py            # rough token counting and LLM compaction
  guardian.py           # parent process for self-restart flow
  llm.py                # OpenAI-compatible client
  prompts.py            # general agent and self-review prompts
  state.py              # session save/load helpers
  tools/
    browser.py          # browser/search tools
    cli.js              # minimal Chrome CDP controller
    cdp.js              # CDP helper
    compact.py          # compact_context tool
    files.py            # read/list/search/write/patch tools
    memory.py           # persistent memory tool
    registry.py         # tool registry
    respond.py          # final response tool
    restart.py          # guardian restart request tool
    skills.py           # skill management tools
    terminal.py         # terminal command tool
skills/                 # reusable local skills
memories/               # persistent USER.md and MEMORY.md
sessions/               # saved conversations
reports/                # generated outputs
run_agent.py            # primary entry point
```

## Context And Memory

The agent keeps context lean by:

- compacting long conversation history with an LLM summary
- truncating older browser snapshots once newer snapshots arrive
- spilling oversized browser results to `sessions/.tool_cache/<session_id>/`
- preserving session JSON under `sessions/`

Use `memory` for stable preferences and project facts. Use `skills` for reusable task workflows, templates, scripts, and checklists.
