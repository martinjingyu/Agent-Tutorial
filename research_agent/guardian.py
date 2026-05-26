"""
Guardian (Master) process for the Agent-Tutorial.

Architecture: Master-Worker (Guardian-Agent)

The Guardian is a thin, stable process that:
1. Spawns the Worker (agent) as a subprocess.
2. Monitors the Worker's exit code and a signal file.
3. If the Worker exits with code 42 (self-update signal), re-spawns it.
4. Loops until the user presses Ctrl+C or the Worker exits normally (code 0).

This allows the Agent to modify its own source code and then trigger a
clean restart by simply exiting with code 42. The Guardian handles the
restart transparently.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SIGNAL_FILE = Path(__file__).resolve().parent / ".restart_signal.json"
"""Signal file used by the Worker to communicate restart details to the Guardian."""

RESTART_EXIT_CODE = 42
"""Exit code that tells the Guardian to restart the Worker."""

MAX_RESTART_COUNT = 10
"""Safety limit: prevent infinite restart loops."""


def _read_signal() -> dict[str, Any] | None:
    """Read and remove the restart signal file."""
    if not SIGNAL_FILE.exists():
        return None
    try:
        data = json.loads(SIGNAL_FILE.read_text(encoding="utf-8"))
        SIGNAL_FILE.unlink(missing_ok=True)
        return data
    except (json.JSONDecodeError, OSError):
        SIGNAL_FILE.unlink(missing_ok=True)
        return None


def _write_signal(
    changes: list[str],
    session_id: str | None = None,
    resume_path: str | None = None,
    next_prompt: str | None = None,
) -> None:
    """Write a restart signal file for the Guardian to read."""
    data: dict[str, Any] = {
        "changes": changes,
        "session_id": session_id,
        "resume_path": resume_path,
        "next_prompt": next_prompt,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    SIGNAL_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_worker_args(original_args: list[str], signal: dict[str, Any] | None) -> list[str]:
    """Build command-line arguments for the Worker subprocess."""
    args = list(original_args)

    # If resuming from a previous session, inject --resume
    if signal and signal.get("resume_path"):
        # Remove any existing --resume flag first
        args = [a for a in args if not a.startswith("--resume")]
        args.extend(["--resume", signal["resume_path"]])

    # If there's a next_prompt from the signal, append it as the prompt
    if signal and signal.get("next_prompt"):
        # If args already has a prompt (positional), replace it
        positional_count = sum(1 for a in args if not a.startswith("-"))
        if positional_count > 0:
            # Find the last positional arg (the prompt) and replace it
            for i in range(len(args) - 1, -1, -1):
                if not args[i].startswith("-"):
                    args[i] = signal["next_prompt"]
                    break
        else:
            args.append(signal["next_prompt"])

    return args


def _print_banner(signal: dict[str, Any] | None) -> None:
    """Print a banner showing what changed during the restart."""
    if not signal:
        return
    changes = signal.get("changes", [])
    if not changes:
        return
    print()
    print("=" * 60)
    print("  🔄 AGENT CODE UPDATED — RESTARTED")
    print("=" * 60)
    for change in changes:
        print(f"  • {change}")
    print("=" * 60)
    print()


def run_guardian(worker_args: list[str]) -> None:
    """
    Run the Guardian loop.

    Args:
        worker_args: Command-line arguments for the Worker process.
                     Should NOT include the script path (sys.argv[0] is used).
    """
    restart_count = 0
    signal: dict[str, Any] | None = None

    while restart_count < MAX_RESTART_COUNT:
        # Build the full command
        cmd = [sys.executable, str(Path(__file__).resolve().parent.parent / "run_research_agent.py")]
        cmd.extend(_build_worker_args(worker_args, signal))

        # Print restart info
        if restart_count > 0:
            _print_banner(signal)
            print(f"  ↻ Restart #{restart_count} — spawning new Worker...\n")
        else:
            print(f"  🚀 Starting Agent-Tutorial (Guardian mode)...\n")

        # Spawn the Worker
        process = subprocess.Popen(
            cmd,
            cwd=os.getcwd(),
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            env=os.environ.copy(),
        )

        try:
            process.wait()
        except KeyboardInterrupt:
            # Forward Ctrl+C to the Worker, then exit
            print("\n  ⏹  Received Ctrl+C, shutting down...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            break

        exit_code = process.returncode

        if exit_code == RESTART_EXIT_CODE:
            # Worker modified its code and requested a restart
            signal = _read_signal()
            restart_count += 1
            print(f"\n  🔄 Worker requested restart (exit code {RESTART_EXIT_CODE})...")
            continue

        if exit_code == 0:
            # Normal exit
            print("\n  ✅ Worker exited normally.")
            break

        # Unexpected exit code
        print(f"\n  ⚠️  Worker exited with unexpected code {exit_code}.")
        user_input = input("  Restart? [Y/n]: ").strip().lower()
        if user_input in ("", "y", "yes"):
            restart_count += 1
            continue
        break

    if restart_count >= MAX_RESTART_COUNT:
        print(f"\n  ❌ Maximum restart count ({MAX_RESTART_COUNT}) reached. Aborting.")
        sys.exit(1)


def request_restart(
    changes: list[str],
    session_id: str | None = None,
    resume_path: str | None = None,
    next_prompt: str | None = None,
) -> None:
    """
    Called by the Worker to signal a restart.

    This writes the signal file and then the Worker should call sys.exit(RESTART_EXIT_CODE).

    Args:
        changes: List of human-readable change descriptions.
        session_id: Current session ID (for resuming).
        resume_path: Path to the session file to resume from.
        next_prompt: The prompt to run after restart (for chat continuity).
    """
    _write_signal(
        changes=changes,
        session_id=session_id,
        resume_path=resume_path,
        next_prompt=next_prompt,
    )


if __name__ == "__main__":
    # Allow running guardian.py directly for testing
    run_guardian(sys.argv[1:])
