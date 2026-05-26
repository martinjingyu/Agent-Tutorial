from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from .registry import json_result, registry

_SESSION_NAMES: dict[str, str] = {}


def _session_name(task_id: str) -> str:
    if task_id not in _SESSION_NAMES:
        _SESSION_NAMES[task_id] = f"tutorial_{uuid.uuid4().hex[:10]}"
    return _SESSION_NAMES[task_id]


def _agent_browser_cmd() -> list[str]:
    direct = shutil.which("agent-browser")
    if direct:
        return [direct]
    npx = shutil.which("npx")
    if npx:
        return [npx, "agent-browser"]
    return ["npx", "agent-browser"]


def _run_browser(task_id: str, command: str, args: list[str], timeout: int = 60) -> dict:
    session = _session_name(task_id)
    socket_dir = Path(tempfile.gettempdir()) / f"agent-browser-{session}"
    socket_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["AGENT_BROWSER_SOCKET_DIR"] = str(socket_dir)
    env.setdefault("AGENT_BROWSER_IDLE_TIMEOUT_MS", "300000")
    cmd = _agent_browser_cmd() + ["--session", session, "--json", command, *args]
    stdout_path = socket_dir / f"_stdout_{command}_{uuid.uuid4().hex[:6]}"
    stderr_path = socket_dir / f"_stderr_{command}_{uuid.uuid4().hex[:6]}"
    try:
        stdout_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            popen_extra: dict = {}
            if os.name == "nt":
                create_no_window = 0x08000000
                popen_extra["creationflags"] = create_no_window
                popen_extra["close_fds"] = True
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
                popen_extra["startupinfo"] = startupinfo
            proc = subprocess.Popen(
                cmd,
                stdout=stdout_fd,
                stderr=stderr_fd,
                stdin=subprocess.DEVNULL,
                env=env,
                **popen_extra,
            )
        finally:
            os.close(stdout_fd)
            os.close(stderr_fd)

        try:
            proc.wait(timeout=timeout)
        except KeyboardInterrupt:
            proc.kill()
            proc.wait(timeout=5)
            raise
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            return {"success": False, "error": f"browser command timed out after {timeout}s"}

        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"browser command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": "agent-browser/npx not found. Run npm install first."}
    finally:
        for path in (stdout_path, stderr_path):
            try:
                path.unlink()
            except OSError:
                pass

    if stdout.strip():
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"success": False, "error": f"Non-JSON browser output: {stdout[:1000]}"}
    if proc.returncode != 0:
        return {"success": False, "error": stderr.strip() or f"exit code {proc.returncode}"}
    return {"success": True, "data": {}}


def _truncate_snapshot(text: str, max_chars: int = 10000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[truncated: call browser_snapshot(full=true) or continue navigating]"


def _browser_navigate(args: dict, runtime: dict) -> str:
    url = str(args.get("url") or "")
    if not url:
        return json_result(success=False, error="url is required")
    task_id = runtime.get("task_id", "default")
    result = _run_browser(task_id, "open", [url], timeout=90)
    if not result.get("success"):
        return json.dumps(result, ensure_ascii=False)
    response = {
        "success": True,
        "url": result.get("data", {}).get("url", url),
        "title": result.get("data", {}).get("title", ""),
    }
    snap = _run_browser(task_id, "snapshot", ["-c"], timeout=60)
    if snap.get("success"):
        data = snap.get("data", {})
        response["snapshot"] = _truncate_snapshot(data.get("snapshot", ""))
        response["element_count"] = len(data.get("refs", {}) or {})
    return json.dumps(response, ensure_ascii=False)


def _browser_snapshot(args: dict, runtime: dict) -> str:
    task_id = runtime.get("task_id", "default")
    full = bool(args.get("full", False))
    result = _run_browser(task_id, "snapshot", [] if full else ["-c"], timeout=60)
    if result.get("success"):
        data = result.get("data", {})
        return json_result(
            success=True,
            snapshot=_truncate_snapshot(data.get("snapshot", ""), 20000 if full else 10000),
            element_count=len(data.get("refs", {}) or {}),
        )
    return json.dumps(result, ensure_ascii=False)


def _browser_click(args: dict, runtime: dict) -> str:
    ref = str(args.get("ref") or "")
    if ref and not ref.startswith("@"):
        ref = "@" + ref
    result = _run_browser(runtime.get("task_id", "default"), "click", [ref], timeout=60)
    return json.dumps(result if not result.get("success") else {"success": True, "clicked": ref}, ensure_ascii=False)


def _browser_type(args: dict, runtime: dict) -> str:
    ref = str(args.get("ref") or "")
    if ref and not ref.startswith("@"):
        ref = "@" + ref
    text = str(args.get("text") or "")
    result = _run_browser(runtime.get("task_id", "default"), "fill", [ref, text], timeout=60)
    return json.dumps(result if not result.get("success") else {"success": True, "typed": len(text), "ref": ref}, ensure_ascii=False)


def _browser_scroll(args: dict, runtime: dict) -> str:
    direction = str(args.get("direction") or "down")
    result = _run_browser(runtime.get("task_id", "default"), "scroll", [direction, "700"], timeout=60)
    return json.dumps(result if not result.get("success") else {"success": True, "direction": direction}, ensure_ascii=False)


def _browser_back(args: dict, runtime: dict) -> str:
    result = _run_browser(runtime.get("task_id", "default"), "back", [], timeout=60)
    return json.dumps(result if not result.get("success") else {"success": True}, ensure_ascii=False)


_BROWSER_SCHEMAS = {
    "browser_navigate": {
        "description": "Navigate to a URL and return a compact accessibility snapshot with clickable refs.",
        "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    "browser_snapshot": {
        "description": "Get a compact or full accessibility snapshot of the current page.",
        "parameters": {"type": "object", "properties": {"full": {"type": "boolean", "default": False}}, "required": []},
    },
    "browser_click": {
        "description": "Click an element by ref from a browser snapshot, such as @e5.",
        "parameters": {"type": "object", "properties": {"ref": {"type": "string"}}, "required": ["ref"]},
    },
    "browser_type": {
        "description": "Fill an input element by ref.",
        "parameters": {"type": "object", "properties": {"ref": {"type": "string"}, "text": {"type": "string"}}, "required": ["ref", "text"]},
    },
    "browser_scroll": {
        "description": "Scroll the current page up or down.",
        "parameters": {"type": "object", "properties": {"direction": {"type": "string", "enum": ["up", "down"]}}, "required": ["direction"]},
    },
    "browser_back": {
        "description": "Go back in browser history.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


registry.register("browser_navigate", _BROWSER_SCHEMAS["browser_navigate"], _browser_navigate)
registry.register("browser_snapshot", _BROWSER_SCHEMAS["browser_snapshot"], _browser_snapshot)
registry.register("browser_click", _BROWSER_SCHEMAS["browser_click"], _browser_click)
registry.register("browser_type", _BROWSER_SCHEMAS["browser_type"], _browser_type)
registry.register("browser_scroll", _BROWSER_SCHEMAS["browser_scroll"], _browser_scroll)
registry.register("browser_back", _BROWSER_SCHEMAS["browser_back"], _browser_back)
