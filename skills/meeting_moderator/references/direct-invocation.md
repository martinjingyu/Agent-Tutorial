# Direct Meeting Invocation (Main Agent)

The meeting tools (`meeting_create_participants`, `meeting_set_agenda`, `meeting_ask_one`, `meeting_chain`, `meeting_group_discuss`, `meeting_add_notes`, `meeting_conclude`) can be called **directly by the main agent** — not only from within a Kanban task.

## When to use direct invocation

Use direct invocation when:
- The user explicitly asks to "test" or "try" the meeting tool
- The user wants a quick discussion/meeting without creating a Kanban board
- The meeting is a one-off task, not part of a larger workflow

## Workflow (main agent calling directly)

1. **Create participants** — Call `meeting_create_participants` with name, role, skills, model for each participant
2. **Set agenda** — Call `meeting_set_agenda` with the discussion topic
3. **Run discussion** — Use `meeting_group_discuss` (parallel brainstorming) or `meeting_chain` (sequential debate) or `meeting_ask_one` (targeted question)
4. **Conclude** — Call `meeting_conclude` with the synthesised result. This ends the meeting agent loop automatically.

## Key difference from Kanban-invoked mode

| Aspect | Kanban-invoked (moderator skill) | Direct invocation |
|--------|----------------------------------|-------------------|
| Entry point | Agent is spawned by Kanban dispatch | Main agent calls tools directly |
| After conclude | Meeting ends automatically | Meeting ends, main agent continues |
| kanban_dispatch | ❌ Do NOT use | ❌ Do NOT use |
| respond_to_user | ❌ Do NOT use (meeting_conclude exits) | ✅ Use after meeting_conclude to report to user |

## Common mistake

❌ Creating a Kanban task and dispatching it when the user says "test the meeting tool"
✅ Call the meeting tools directly and report results back to the user

The meeting tools are first-class tools available to the main agent, not hidden behind Kanban.
