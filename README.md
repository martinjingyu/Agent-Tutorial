# Agent Deep Research Tutorial

This repo now contains two tutorial agents:

- `agent_deep_research.py`: the original linear search/rank/report pipeline.
- `run_research_agent.py`: a Hermes-inspired action-loop agent with browser, file, memory, skills, terminal, context compaction, and **self-updating code** via a Master-Worker architecture.

## Setup

```powershell
pip install -r requirements.txt
npm install
npx agent-browser install
```

Set a DeepSeek API key:

```powershell
$env:DEEPSEEK_API_KEY="your-key"
$env:DEEPSEEK_MODEL="deepseek-v4-flash"
$env:DEEPSEEK_THINKING="disabled"
```

Optional:

```powershell
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
```

## Run The Browser Research Agent

### Normal Mode

```powershell
python .\run_research_agent.py "Research Beijing University of Posts and Telecommunications 电信工程及管理专业 and save a markdown report."
```

### Guardian Mode (Self-Updating)

```powershell
python .\run_research_agent.py --guardian "Research Beijing University of Posts and Telecommunications 电信工程及管理专业"
```

In Guardian mode, if the agent discovers a bug in its own source code and fixes it, it can call `request_restart(changes=[...])` to trigger a clean restart. The Guardian (parent process) detects the exit code 42 and spawns a fresh Worker process with the updated code.

### Chat Mode

```powershell
python .\run_research_agent.py --chat
python .\run_research_agent.py --guardian --chat   # with self-updating support
```

### Resume a Session

```powershell
python .\run_research_agent.py --resume 20260526_141013
```

## Capabilities

The agent can:

- **Browse the web** — navigate pages with `browser_navigate`, inspect `browser_snapshot`, and interact with refs using `browser_click`/`browser_type`.
- **Read & write files** — read, search, patch, and write files under the whole `C:\Users\LX034\Code` workspace by default.
- **Save reports** — tutorial-agent reports under `Agent-Tutorial/reports/` when no other path is requested.
- **Persistent memory** — project-local memory in `memories/MEMORY.md` and `memories/USER.md`.
- **Skill library** — read and update project-local skills under `skills/`.
- **Context compaction** — automatic pre-action compact when tool results accumulate after a final response; manual compact via `compact_context(focus="...")`.
- **Self-updating code** — when running under `--guardian`, the agent can fix bugs in its own source code and trigger a clean restart via `request_restart(changes=[...])`.
- **Error recovery** — after 3+ consecutive identical errors, the agent stops retrying and reviews its own source code to find and fix the root cause.

By default, tool paths are resolved against the parent `Code` folder, not only this repo. You can override that root:

```powershell
$env:AGENT_WORKSPACE_ROOT="C:\Users\LX034\Code"
```

## Project Layout

```text
research_agent/
  agent.py          # action loop + pre-action compact check + self-restart logic
  cli.py            # CLI entry point (normal + guardian mode)
  context.py        # rough token count + compaction
  guardian.py       # Master process: spawns Worker, detects exit code 42, auto-restarts
  prompts.py        # system and self-review prompts
  state.py          # session save/load
  paths.py          # project directory paths
  tools/
    __init__.py     # tool loader
    registry.py     # tool registration & dispatch
    browser.py      # browser navigation tools
    compact.py      # compact_context tool
    files.py        # read/write/search/patch file tools
    memory.py       # memory read/write tools
    respond.py      # respond_to_user tool
    restart.py      # request_restart tool (signals Guardian to restart)
    skills.py       # skill management tools
    terminal.py     # terminal command tool
skills/             # project-local skill library
  utilities/
    context-management/     # context compaction best practices
    windows-file-operations/ # Windows file I/O best practices
  research/
    university-program-research/  # university program research workflow
  hr-recruitment/
    cv-link-deep-research/        # CV link verification workflow
    stage1-screening-report/      # Stage 1 screening report workflow
memories/           # project-local persistent memory
reports/            # generated reports
sessions/           # saved conversation JSON
```

## Master-Worker Architecture

```
┌─ Guardian (master) ────────────────────────────┐
│  python run_research_agent.py --guardian ...    │
│                                                 │
│  ① spawn Worker subprocess                      │
│  ② process.wait() — monitor exit code           │
│  ③ exit code 42 → read signal file → re-spawn   │
│  ④ exit code 0 → normal exit                    │
│  ⑤ Ctrl+C → terminate Worker → exit             │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─ Worker (agent) ───────────────────────────────┐
│  ① Execute tasks normally                       │
│  ② Discover bug → read_file → write_file fix    │
│  ③ Call request_restart(changes=["..."])         │
│  ④ run() ends → detect flag → sys.exit(42)      │
│  ⑤ Guardian detects 42 → re-spawn               │
│  ⑥ New Worker loads updated code + --resume      │
└──────────────────────────────────────────────────┘
```

**Safety limits**:
- Maximum 10 restarts per session (prevents infinite loops).
- Signal file `.restart_signal.json` records changes, session info, and next prompt.
- Session is saved before exit; new Worker resumes automatically.

## Offline Linear Demo

```powershell
python .\agent_deep_research.py "AI agents in software engineering" --mock-model --provider mock --mock-content
```

## Interrupt & Correct

During a run, press `Ctrl+C` to interrupt the current model/tool action. The agent will pause and show:

```text
Correction>
```

Enter a correction such as `不要继续点招生页面，回到计算机学院官网查课程设置`, and the same session will continue with that instruction in context. Enter `/stop` or press `Ctrl+C` again at the correction prompt to save the current session and exit the turn.
