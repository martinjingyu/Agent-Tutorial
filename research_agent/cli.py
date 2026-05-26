from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import ResearchAgent
from .env import load_dotenv
from .state import load_session
from .ui import ConsoleUI


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Agent-Tutorial browser research agent.")
    parser.add_argument("prompt", nargs="?", help="Research or automation task")
    parser.add_argument("--model", default=None)
    parser.add_argument("--no-self-review", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=50)
    parser.add_argument("--chat", action="store_true", help="Start an interactive multi-turn chat session.")
    parser.add_argument("--resume", help="Resume from a session id or sessions/*.json path.")
    parser.add_argument("--quiet-actions", action="store_true", help="Hide per-action model/tool trace lines.")
    parser.add_argument(
        "--guardian",
        action="store_true",
        help="Wrap the agent in a Guardian process that auto-restarts on code changes.",
    )
    args = parser.parse_args()

    # ── Guardian mode ──────────────────────────────────────────────
    if args.guardian:
        from .guardian import run_guardian

        # Forward all args except --guardian itself to the Worker
        worker_args = [a for a in sys.argv[1:] if a != "--guardian"]
        run_guardian(worker_args)
        return

    # ── Normal (Worker) mode ───────────────────────────────────────
    load_dotenv()
    agent = ResearchAgent(
        model=args.model,
        max_iterations=args.max_iterations,
        self_review=not args.no_self_review,
        ui=ConsoleUI(enabled=not args.quiet_actions),
    )
    history = _load_history(args.resume) if args.resume else []

    if args.chat:
        if args.prompt:
            history = _run_once(agent, args.prompt, history)
        print(f"Interactive session: {agent.session_id}")
        print("Type /exit to quit.")
        while True:
            try:
                prompt = input("\nYou> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not prompt:
                continue
            if prompt in {"/exit", "/quit"}:
                break
            history = _run_once(agent, prompt, history)
        return

    if not args.prompt:
        parser.error("prompt is required unless --chat is used")
    _run_once(agent, args.prompt, history)


def _load_history(resume: str) -> list[dict]:
    path = Path(resume)
    if path.exists():
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    return load_session(resume)


def _run_once(agent: ResearchAgent, prompt: str, history: list[dict]) -> list[dict]:
    result = agent.run(prompt, history=history)
    print(result["final"])
    print(f"\nSession saved: {result['session_path']}")
    return result["messages"]
