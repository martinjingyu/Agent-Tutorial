from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import GeneralAgent
from .env import load_dotenv
from .session import ChatSession
from .state import load_session
from .ui import ConsoleUI


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Agent-Tutorial general tool-use agent.")
    parser.add_argument("prompt", nargs="?", help="Task for the agent")
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider", choices=["deepseek", "codex", "openai"])
    parser.add_argument("--no-self-review", action="store_true")
    parser.add_argument("--max-iterations", type=int, default=50)
    parser.add_argument("--chat", action="store_true", help="Start an interactive multi-turn chat session.")
    parser.add_argument("--resume", help="Resume from a session id or sessions/*.json path.")
    parser.add_argument("--quiet-actions", action="store_true")
    parser.add_argument("--setup-browser-profile", nargs="?", const="", metavar="CHROME_PROFILE")
    parser.add_argument("--login-browser", action="store_true")
    parser.add_argument("--guardian", action="store_true")
    args = parser.parse_args()

    if args.guardian:
        from .guardian import run_guardian
        run_guardian([a for a in sys.argv[1:] if a != "--guardian"])
        return

    load_dotenv()

    if args.setup_browser_profile is not None:
        from .browser_profile import setup_profile
        setup_profile(args.setup_browser_profile or None)
        return

    if args.login_browser:
        from .browser_profile import login_session
        login_session()
        return

    agent = GeneralAgent(
        model=args.model,
        provider=args.provider,
        max_iterations=args.max_iterations,
        self_review=not args.no_self_review,
        ui=ConsoleUI(enabled=not args.quiet_actions),
    )
    history = _load_history(args.resume) if args.resume else []
    session = ChatSession(agent, history=history)

    if args.chat:
        if args.prompt:
            print(session.run_turn(args.prompt))
        print(f"Interactive session: {agent.session_id}")
        print("Type /exit to quit.")
        session.start_interactive()
        return

    if not args.prompt:
        parser.error("prompt is required unless --chat is used")
    print(session.run_turn(args.prompt))
    print(f"\nSession saved: {agent.session_id}")


def _load_history(resume: str) -> list[dict]:
    path = Path(resume)
    if path.exists():
        import json
        return json.loads(path.read_text(encoding="utf-8"))
    return load_session(resume)
