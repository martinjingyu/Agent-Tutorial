# Meeting Participant Model Configuration

## Overview

Each participant in a meeting can be assigned a specific LLM model via the `model` parameter in `meeting_create_participants`. If no model is specified, the participant uses the **system default model** (the same provider/model the main agent is running on).

## When to specify models explicitly

- **User asks about models** — If the user asks "what models are the experts using?", you should have specified them explicitly. If you didn't, the answer is "default model" and the user may want you to re-run with specific models.
- **Diverse expertise** — When participants represent different domains (e.g., ML engineer vs. product manager vs. security expert), assigning different models can bring genuinely diverse perspectives.
- **Testing/comparison** — When the goal is to compare model outputs on the same topic.
- **Cost/quality tradeoff** — Use cheaper models for simple brainstorming rounds, more capable models for critical evaluation rounds.

## How to specify

```python
meeting_create_participants(
    participants=[
        {
            "name": "张三",
            "role": "资深算法工程师",
            "model": "gpt-4"  # explicit model
        },
        {
            "name": "李四",
            "role": "技术负责人",
            # no model specified → uses default
        }
    ]
)
```

## What models are available

This depends on the system configuration. Common options include:
- `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` (OpenAI)
- `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku` (Anthropic)
- Other providers configured in the system

Check the system's available model list or ask the user which models they prefer.

## Common mistake

❌ Creating participants without specifying models, then being unable to answer when the user asks what models they used.
✅ Either specify models explicitly, or be prepared to answer "default model" and offer to re-run with specific models if needed.

## Best practice

When the task prompt or user explicitly mentions "experts" or "different perspectives", always specify models explicitly so you can report back accurately. If the user doesn't specify, ask or make a reasonable choice and document it.
