"""
Examples of using research_agent as a library.

Opt-in extras (not loaded by default):
    register_kanban_wait_complete()  — blocking kanban wait for batch pipelines
    register_meeting_tools()         — meeting orchestration for moderator agents
"""
from __future__ import annotations

from research_agent import GeneralAgent, ChatSession, KanbanWatcher
# load_builtin_tools() is called automatically inside GeneralAgent.__init__


# ── 1. Single-turn ────────────────────────────────────────────────────────

agent = GeneralAgent(model="deepseek-chat", provider="deepseek")
result = agent.run("Summarise README.md in one paragraph.")
print(result["final"])


# ── 2. Multi-turn with ChatSession ────────────────────────────────────────

session = ChatSession(GeneralAgent(model="deepseek-chat", provider="deepseek"))
session.run_turn("Create notes.txt with 3 bullet points about Python.")
session.run_turn("Append a 4th bullet point about type hints.")
# history is carried automatically between turns


# ── 3. Kanban — batch mode (blocking wait) ────────────────────────────────
#
# Agent dispatches pipeline, then kanban_wait_complete blocks internally
# until all tasks finish. No LLM calls during the wait.
# Requires explicit opt-in.

from research_agent.tools.kanban import register_kanban_wait_complete
register_kanban_wait_complete()

batch_session = ChatSession(GeneralAgent(model="deepseek-chat", provider="deepseek"))
batch_session.run_turn("""
Create a kanban board 'research' with 3 parallel tasks:
  task-a: search Python asyncio docs
  task-b: search Python threading docs
  task-c: search Python multiprocessing docs
Dispatch, then call kanban_wait_complete, then summarise all results.
""")
# run_turn() returns only after the full pipeline + review is done


# ── 4. Kanban — interactive mode (event-driven) ───────────────────────────
#
# Agent subscribes and returns immediately. Caller polls for events
# via drain_pending() and decides when to trigger the next turn.
# start_watcher() must be called to enable event delivery.

import time

interactive_session = ChatSession(GeneralAgent(model="deepseek-chat", provider="deepseek"))
interactive_session.start_watcher()   # start background polling for kanban events

interactive_session.run_turn("""
Create a kanban board 'research2' with the same 3 tasks.
Dispatch, then kanban_notify_subscribe, then respond_to_user saying pipeline started.
""")
# run_turn() returns quickly — agent is done for this turn

# Caller's own scheduling loop
while True:
    time.sleep(1)
    pending = interactive_session.drain_pending()
    if pending:
        result = interactive_session.run_turn(pending[0]["content"])
        print(result)
        break


# ── 5. Interactive terminal (CLI-style) ───────────────────────────────────
#
# Hand off entirely to ChatSession — it manages input(), history, and watcher.

# ChatSession(GeneralAgent(...)).start_interactive()


# ── 6. KanbanWatcher standalone ───────────────────────────────────────────
#
# For callers that manage their own agent lifecycle and just need the event hook.

def on_pipeline_done(msgs: list[dict]) -> None:
    print("Pipeline complete:", msgs[0]["content"][:80])

watcher = KanbanWatcher(on_event=on_pipeline_done).start()
# ... do other work ...
watcher.stop()


# ── 7. Meeting orchestration ──────────────────────────────────────────────
#
# A Moderator agent runs a structured multi-agent discussion.
# Participants are full GeneralAgents with their own tool loops,
# but without kanban_* and meeting_* tools.

from research_agent import register_meeting_tools
register_meeting_tools()

moderator = GeneralAgent(model="deepseek-chat", provider="deepseek")
ChatSession(moderator).run_turn("""
You are a meeting moderator. Run the following discussion:

1. Create two participants:
   - Alice: role=Advocate, skills=system design and scalability
   - Bob:   role=Critic,   skills=security and cost analysis

2. Set agenda: "Should we migrate from REST to GraphQL?"

3. Run a chain discussion (2 rounds):
   - Prompt: "What is your position on migrating to GraphQL?"

4. Ask Alice alone: "Given Bob's critique, do you revise your position?"

5. Synthesise and conclude.
""")
# The moderator internally calls meeting_create_participants, meeting_chain,
# meeting_ask_one, meeting_conclude, then respond_to_user with the conclusion.
