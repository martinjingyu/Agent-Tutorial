from __future__ import annotations

import os
from pathlib import Path

import agent_browser as ab

from .registry import json_result, registry

# Point agent_browser at the project-local profiles directory so login state
# stays alongside the code rather than in the user's home directory.
_PROFILES_DIR = Path(__file__).parent.parent / ".agentbrowser" / "profiles"
os.environ.setdefault("AGENT_BROWSER_PROFILES_DIR", str(_PROFILES_DIR))


# ---------------------------------------------------------------------------
# Public helpers (imported directly by agent code)
# ---------------------------------------------------------------------------

def close_browser() -> None:
    """Close this context's browser tab. Called by agents when done."""
    ab.close_session()


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _h_navigate(args: dict, _: dict) -> str:
    return json_result(**ab.navigate(args.get("url", "")))

def _h_snapshot(_: dict, __: dict) -> str:
    return json_result(**ab.snapshot())

def _h_click(args: dict, _: dict) -> str:
    return json_result(**ab.click(args.get("ref", "")))

def _h_type(args: dict, _: dict) -> str:
    return json_result(**ab.type_text(args.get("text", "")))

def _h_press_key(args: dict, _: dict) -> str:
    return json_result(**ab.press_key(args.get("key", "")))

def _h_scroll(args: dict, _: dict) -> str:
    return json_result(**ab.scroll(args.get("direction", "down"), int(args.get("pixels", 600))))

def _h_screenshot(args: dict, _: dict) -> str:
    return json_result(**ab.screenshot(args.get("path")))

def _h_back(_: dict, __: dict) -> str:
    return json_result(**ab.back())

def _h_close(_: dict, __: dict) -> str:
    ab.close_session()
    return json_result(success=True)

def _h_google_search(args: dict, _: dict) -> str:
    return json_result(**ab.google_search(args.get("query", ""), int(args.get("page", 0))))

def _h_bing_search(args: dict, _: dict) -> str:
    return json_result(**ab.bing_search(args.get("query", ""), int(args.get("page", 0))))

def _h_baidu_search(args: dict, _: dict) -> str:
    return json_result(**ab.baidu_search(args.get("query", ""), int(args.get("page", 0))))

def _h_reddit_search(args: dict, _: dict) -> str:
    return json_result(**ab.reddit_search(args.get("query", "")))

def _h_save_research_notes(_: dict, __: dict) -> str:
    return json_result(success=True)


# ---------------------------------------------------------------------------
# Tool registrations
# ---------------------------------------------------------------------------

registry.register("browser_navigate", {
    "description": "Navigate to a URL and return an accessibility snapshot. Use direct search tools for search-engine queries.",
    "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
}, _h_navigate)

registry.register("browser_snapshot", {
    "description": "Return the current page accessibility snapshot with @ref IDs.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}, _h_snapshot)

registry.register("browser_click", {
    "description": "Click an element by its @ref ID from the last snapshot, e.g. e5 or @e5.",
    "parameters": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]},
}, _h_click)

registry.register("browser_type", {
    "description": "Type text into the currently focused element. Use browser_click first to focus an input.",
    "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
}, _h_type)

registry.register("browser_press_key", {
    "description": "Press a named key such as Enter, Tab, Escape, ArrowDown, or ArrowUp.",
    "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
}, _h_press_key)

registry.register("browser_scroll", {
    "description": "Scroll the page up or down.",
    "parameters": {
        "type": "object",
        "properties": {
            "direction": {"type": "string", "enum": ["up", "down"], "default": "down"},
            "pixels": {"type": "integer", "default": 600},
        },
        "required": [],
    },
}, _h_scroll)

registry.register("browser_screenshot", {
    "description": "Save a PNG screenshot of the current page and return the saved file path.",
    "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []},
}, _h_screenshot)

registry.register("browser_back", {
    "description": "Go back to the previous page in browser history.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}, _h_back)

registry.register("browser_close", {
    "description": "Close this agent run's browser instance.",
    "parameters": {"type": "object", "properties": {}, "required": []},
}, _h_close)

registry.register("google_search", {
    "description": (
        "Search Google. Returns a structured list of results with title, URL, and snippet. "
        "Use page=1, 2, ... to fetch additional result pages."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "page": {"type": "integer", "default": 0, "description": "Result page index, 0-based."},
        },
        "required": ["query"],
    },
}, _h_google_search)

registry.register("bing_search", {
    "description": (
        "Search Bing. Returns a structured list of results with title, URL, and snippet. "
        "Prefer for general web search and official pages."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "page": {"type": "integer", "default": 0, "description": "Result page index, 0-based."},
        },
        "required": ["query"],
    },
}, _h_bing_search)

registry.register("baidu_search", {
    "description": (
        "Search Baidu. Returns a structured list of results with title, URL, and snippet. "
        "Use for Chinese-language and mainland China sources."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "page": {"type": "integer", "default": 0, "description": "Result page index, 0-based."},
        },
        "required": ["query"],
    },
}, _h_baidu_search)

registry.register("reddit_search", {
    "description": "Search Reddit for community discussions and first-hand accounts.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
}, _h_reddit_search)

registry.register("save_research_notes", {
    "description": (
        "Save concise notes from the current browser/file result before moving on. "
        "After this tool runs, the previous large tool result is replaced in context "
        "with these notes to reduce token cost while preserving important findings."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "notes": {
                "type": "string",
                "description": "Important findings as concise bullets, including URLs and concrete facts.",
            }
        },
        "required": ["notes"],
    },
}, _h_save_research_notes)
