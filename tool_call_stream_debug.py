"""
Stream-debug a model tool call with the OpenAI Responses API.

What this demonstrates:
1. Register a Python-side tool as JSON Schema.
2. Ask the model a question that requires the tool.
3. Stream raw event types and function-call argument deltas.
4. Execute the local Python function.
5. Send function_call_output back to the model.
6. Stream the final answer.

Important:
The API streams tool-call metadata and argument deltas. It does not expose the
model's private chain-of-thought. For reasoning models, you may see reasoning
events or summaries depending on model/API settings, but private reasoning is
not the same thing as user-visible text.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from openai import OpenAI


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def load_dotenv(path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a local .env file without extra dependencies."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def get_weather(city: str) -> dict[str, Any]:
    """A fake local tool. Replace this with a real weather API if needed."""
    weather_by_city = {
        "上海": {"temperature_c": 24, "condition": "cloudy", "humidity": "70%"},
        "shanghai": {"temperature_c": 24, "condition": "cloudy", "humidity": "70%"},
        "beijing": {"temperature_c": 21, "condition": "sunny", "humidity": "42%"},
        "北京": {"temperature_c": 21, "condition": "sunny", "humidity": "42%"},
        "new york": {"temperature_c": 18, "condition": "rain", "humidity": "81%"},
    }

    data = weather_by_city.get(city.strip().lower())
    if not data:
        data = {"temperature_c": 20, "condition": "unknown", "humidity": "unknown"}

    return {"city": city, **data}


TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "获取指定城市的实时天气。",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如 上海、北京、New York",
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


def call_local_tool(name: str, arguments_json: str) -> str:
    args = json.loads(arguments_json or "{}")

    if name == "get_weather":
        return json.dumps(get_weather(**args), ensure_ascii=False)

    raise ValueError(f"Unknown tool: {name}")


def event_to_dict(event: Any) -> dict[str, Any]:
    if hasattr(event, "model_dump"):
        return event.model_dump()
    if isinstance(event, dict):
        return event
    return {"repr": repr(event)}


def stream_first_turn(client: OpenAI, model: str, user_input: str) -> list[dict[str, Any]]:
    print("\n=== First turn: model decides whether to call a tool ===\n")

    stream = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
        tools=TOOLS,
        stream=True,
    )

    output_items: dict[int, dict[str, Any]] = {}

    for event in stream:
        data = event_to_dict(event)
        event_type = data.get("type")
        print(f"[event] {event_type}")

        if event_type == "response.output_item.added":
            item = data.get("item", {})
            output_index = data.get("output_index", len(output_items))
            output_items[output_index] = item
            if item.get("type") == "function_call":
                print(f"  tool name started: {item.get('name')}")
                print(f"  call_id: {item.get('call_id')}")

        elif event_type == "response.function_call_arguments.delta":
            output_index = data.get("output_index", 0)
            delta = data.get("delta", "")
            output_items.setdefault(output_index, {"type": "function_call"})
            output_items[output_index]["arguments"] = (
                output_items[output_index].get("arguments", "") + delta
            )
            print(f"  arguments delta: {delta!r}")

        elif event_type == "response.function_call_arguments.done":
            output_index = data.get("output_index", 0)
            arguments = data.get("arguments", "")
            output_items.setdefault(output_index, {"type": "function_call"})
            output_items[output_index]["arguments"] = arguments
            print(f"  arguments done: {arguments}")

        elif event_type == "response.output_item.done":
            output_index = data.get("output_index", 0)
            item = data.get("item", {})
            output_items[output_index] = item
            print(f"  output item done: {item.get('type')}")

        elif event_type == "response.output_text.delta":
            print(data.get("delta", ""), end="", flush=True)

        elif event_type == "response.completed":
            print("\n  response completed")

        elif event_type == "error":
            raise RuntimeError(data)
        
        else:
            print(f"\n  [unhandled event data] {data}")

    return [output_items[index] for index in sorted(output_items)]


def stream_second_turn(
    client: OpenAI,
    model: str,
    first_turn_output: list[dict[str, Any]],
) -> None:
    tool_outputs = []

    for item in first_turn_output:
        if item.get("type") != "function_call":
            continue

        name = item["name"]
        arguments = item.get("arguments", "{}")
        call_id = item["call_id"]

        print("\n=== Local Action: execute Python function ===")
        print(f"tool: {name}")
        print(f"arguments: {arguments}")

        output = call_local_tool(name, arguments)
        print(f"output: {output}")

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": output,
            }
        )

    if not tool_outputs:
        print("\nNo function call was produced. Try a more tool-dependent prompt.")
        return

    print("\n=== Second turn: model receives tool output and answers ===\n")

    stream = client.responses.create(
        model=model,
        input=[*first_turn_output, *tool_outputs],
        tools=TOOLS,
        stream=True,
    )

    for event in stream:
        data = event_to_dict(event)
        event_type = data.get("type")

        if event_type == "response.output_text.delta":
            print(data.get("delta", ""), end="", flush=True)
        elif event_type == "response.completed":
            print("\n\n[done]")
        elif event_type == "error":
            raise RuntimeError(data)
        else:
            print(f"\n[event] {event_type}")


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Debug streaming OpenAI tool calls.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model to use. Defaults to OPENAI_MODEL or gpt-4.1-mini.",
    )
    parser.add_argument(
        "--prompt",
        default="请查询上海现在的天气，并用中文一句话告诉我是否适合出门散步。",
        help="Prompt that should require the get_weather tool.",
    )
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set.")

    client = OpenAI()
    first_turn_output = stream_first_turn(client, args.model, args.prompt)
    stream_second_turn(client, args.model, first_turn_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
