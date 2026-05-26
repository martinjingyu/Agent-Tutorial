# Guardian Process Tree Diagnosis

## Purpose

When debugging the Master-Worker (Guardian-Agent) restart architecture, use this guide to verify that:
1. The Guardian process is running and has spawned a Worker
2. After a restart (exit code 42), the new Worker is a child of the same Guardian
3. The restart signal file has been cleaned up

## Process Tree Structure (Healthy State)

```
Terminal (e.g., VS Code, cmd.exe)
  └─ Guardian (python run_research_agent.py --guardian --chat)
       └─ Worker/Agent (python run_research_agent.py --chat --resume ...)
```

## Diagnosis Commands

### 1. List all python processes with parent-child relationships

```cmd
wmic process where name='python.exe' get processid,parentprocessid
```

**Output example:**
```
ParentProcessId  ProcessId
6836             14296      ← Hermes agent (not part of our architecture)
14296            6172       ← Hermes agent child
13964            17968      ← Guardian (parent=13964, which is the terminal)
17968            15572      ← Worker (parent=17968 = Guardian!)
```

### 2. Identify each process by command line

```cmd
wmic process where processid=17968 get commandline
wmic process where processid=15572 get commandline
```

**Guardian command line:** Contains `--guardian`
**Worker command line:** Contains `--chat --resume` (after restart) or just `--chat` (first launch)

### 3. Check for restart signal file

```cmd
if exist research_agent\.restart_signal.json (type research_agent\.restart_signal.json) else (echo NO_SIGNAL_FILE)
```

After a successful restart, the signal file should be **absent** (Guardian reads and deletes it).

## Interpretation

| Condition | Meaning |
|-----------|---------|
| Guardian exists, Worker is its child | ✅ Architecture working |
| Worker command line has `--resume` | ✅ This is a restarted session |
| No signal file | ✅ Clean state after restart |
| Guardian missing | ❌ Started without `--guardian` flag |
| Worker not child of Guardian | ❌ Something else spawned the Worker |
| Signal file still exists | ❌ Guardian may have crashed before cleanup |

## Common Issues

### Issue: Worker is not a child of Guardian
- **Cause:** Started the agent directly without `--guardian`
- **Fix:** Use `python run_research_agent.py --guardian --chat`

### Issue: Multiple Guardian processes
- **Cause:** Multiple terminals each running with `--guardian`
- **Fix:** Only one Guardian should be active; close extra terminals

### Issue: WMIC blocked by security filter
- **Symptom:** `ValueError: Blocked risky command pattern: \bformat\b`
- **Workaround:** Use plain `wmic ... get ...` without `/format:csv`
- **Alternative:** Use `tasklist /v /fo csv` for basic info

## Script

A reusable batch script is available at:
`skills/utilities/context-management/scripts/diagnose-process-tree.bat`

Run it from the Agent-Tutorial root directory:
```cmd
skills\utilities\context-management\scripts\diagnose-process-tree.bat
```
