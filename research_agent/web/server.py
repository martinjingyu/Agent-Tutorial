"""
Web dashboard server for Agent-Tutorial.

Endpoints:
  GET  /                           — dashboard SPA
  GET  /api/overview               — summary stats
  GET  /api/sessions               — list all sessions
  GET  /api/sessions/{id}          — full session (messages, usage, cost)
  DELETE /api/sessions/{id}        — delete session file
  GET  /api/kanban                 — list boards
  GET  /api/kanban/{board}         — board + tasks + worker outputs
  DELETE /api/kanban/{board}       — delete board and worker files
  GET  /api/meetings               — list meetings
  GET  /api/meetings/{id}          — meeting detail + full transcript
  DELETE /api/meetings/{id}        — delete meeting file
  GET  /api/costs                  — cost breakdown by model / session
  POST /api/chat                   — send message to agent (returns session_id)
  GET  /api/chat/{session_id}/stream — SSE stream for live agent output
  GET  /api/events                 — SSE stream for dashboard live updates
"""
from __future__ import annotations

import json
import queue
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from ..paths import SESSIONS_DIR
from ..state import new_session_id

app = FastAPI(title="Agent Dashboard", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

STATIC_DIR   = Path(__file__).parent / "static"
KANBAN_DIR   = SESSIONS_DIR / "kanban"
MEETINGS_DIR = SESSIONS_DIR / "meetings"

# ── Token pricing (USD per million tokens) ────────────────────────────────

_PRICE: dict[str, dict[str, float]] = {
    "deepseek-v4-flash":    {"in": 0.07,  "out": 0.28},
    "deepseek-chat":        {"in": 0.27,  "out": 1.10},
    "deepseek-v3":          {"in": 0.27,  "out": 1.10},
    "deepseek-reasoner":    {"in": 0.55,  "out": 2.19},
    "deepseek-r1":          {"in": 0.55,  "out": 2.19},
    "claude-haiku-4-5":     {"in": 0.80,  "out": 4.00},
    "claude-sonnet-4-6":    {"in": 3.00,  "out": 15.00},
    "claude-opus-4-8":      {"in": 15.00, "out": 75.00},
    "gpt-4o-mini":          {"in": 0.15,  "out": 0.60},
    "gpt-4o":               {"in": 2.50,  "out": 10.00},
    "gpt-5.4":              {"in": 2.50,  "out": 10.00},
}

def _price_per_million(model: str) -> dict[str, float]:
    m = model.lower()
    for key, p in _PRICE.items():
        if key in m:
            return p
    return {"in": 0.0, "out": 0.0}

def _calc_cost(model: str, in_tok: int, out_tok: int) -> float:
    p = _price_per_million(model)
    return (in_tok * p["in"] + out_tok * p["out"]) / 1_000_000


# ── File helpers ──────────────────────────────────────────────────────────

def _read_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    except Exception:
        pass
    return rows


# ── Usage / cost helpers ──────────────────────────────────────────────────

def _usage_by_session() -> dict[str, dict]:
    rows = _read_jsonl(SESSIONS_DIR / "usage_log.jsonl")
    by_session: dict[str, dict] = {}
    for r in rows:
        sid   = r.get("session_id") or ""
        model = r.get("model") or ""
        in_t  = int(r.get("in") or 0)
        out_t = int(r.get("out") or 0)
        cost  = _calc_cost(model, in_t, out_t)
        s = by_session.setdefault(sid, {"in": 0, "out": 0, "cost": 0.0, "model": model})
        s["in"] += in_t; s["out"] += out_t; s["cost"] += cost
    return by_session


# ── Data readers ──────────────────────────────────────────────────────────

def _session_fingerprint(msgs: list) -> tuple | None:
    """(msg_count, first_user_content_prefix) — unique enough to match a session."""
    if not msgs:
        return None
    user_msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") == "user"]
    if not user_msgs:
        return None
    first = str(user_msgs[0].get("content") or "")[:300]
    return (len(msgs), first)


def _sub_session_ids() -> set[str]:
    """Session IDs that belong to kanban sub-agents or meeting participants."""
    ids: set[str] = set()

    # Kanban worker caches
    if KANBAN_DIR.exists():
        for cache_file in KANBAN_DIR.glob("*/workers/*.json"):
            if ".payload." in cache_file.name:
                continue
            try:
                d = _read_json(cache_file)
                if isinstance(d, dict) and d.get("session_id"):
                    ids.add(str(d["session_id"]))
            except Exception:
                pass

    # Meeting participant sessions
    meetings_dir = SESSIONS_DIR / "meetings"
    if not meetings_dir.exists():
        return ids

    # Collect participant histories that need fingerprint matching
    needs_match: list[list] = []
    for mf in meetings_dir.glob("mtg_*.json"):
        try:
            d = _read_json(mf)
            if not isinstance(d, dict):
                continue
            for p in d.get("participants", {}).values():
                if not isinstance(p, dict):
                    continue
                if p.get("session_id"):
                    # New-style: session_id already stored
                    ids.add(str(p["session_id"]))
                elif p.get("session_history"):
                    # Old-style: need fingerprint match
                    needs_match.append(p["session_history"])
        except Exception:
            pass

    if not needs_match:
        return ids

    # Build fingerprint → session_id map from all session files
    fp_map: dict[tuple, str] = {}
    for sf in SESSIONS_DIR.glob("*.json"):
        try:
            msgs = _read_json(sf)
            if not isinstance(msgs, list):
                continue
            fp = _session_fingerprint(msgs)
            if fp:
                fp_map[fp] = sf.stem
        except Exception:
            pass

    for history in needs_match:
        fp = _session_fingerprint(history)
        if fp and fp in fp_map:
            ids.add(fp_map[fp])

    return ids


def _active_session_ids() -> set[str]:
    """Session IDs that are currently running (web chat or kanban workers)."""
    ids: set[str] = set()
    # Web chat sessions running in this server process
    for sid, data in _chat_sessions.items():
        if data.get("running"):
            ids.add(sid)
    # Kanban workers whose cache reports queued/running
    if KANBAN_DIR.exists():
        for cache_file in KANBAN_DIR.glob("*/workers/*.json"):
            if ".payload." in cache_file.name:
                continue
            try:
                d = _read_json(cache_file)
                if isinstance(d, dict) and d.get("status") in ("queued", "running") and d.get("session_id"):
                    ids.add(str(d["session_id"]))
            except Exception:
                pass
    return ids


def _list_sessions() -> list[dict]:
    sub_ids    = _sub_session_ids()
    active_ids = _active_session_ids()
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.json"), reverse=True):
        data = _read_json(f)
        if not isinstance(data, list):
            continue
        # Detect __meta__ sub_agent marker written by new-style agents
        has_meta = bool(data and isinstance(data[0], dict) and data[0].get("__meta__"))
        is_sub_by_meta = has_meta and bool(data[0].get("sub_agent"))
        msgs = data[1:] if has_meta else data
        session_id = f.stem
        model = next((m.get("model") for m in msgs if isinstance(m, dict) and m.get("model")), "")
        created = f.stat().st_mtime
        sessions.append({
            "id":            session_id,
            "created_at":    datetime.fromtimestamp(created).isoformat(timespec="seconds"),
            "message_count": len(msgs),
            "model":         model,
            "is_sub":        is_sub_by_meta or session_id in sub_ids,
            "is_active":     session_id in active_ids,
        })
    return sessions


def _session_messages(session_id: str) -> list[dict]:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        return []
    data = _read_json(path)
    if not isinstance(data, list):
        return []
    if data and isinstance(data[0], dict) and data[0].get("__meta__"):
        return data[1:]
    return data


def _list_boards() -> list[dict]:
    boards = []
    if not KANBAN_DIR.exists():
        return boards
    for f in sorted(KANBAN_DIR.glob("*.json")):
        data = _read_json(f)
        if not isinstance(data, dict):
            continue
        tasks = list(data.get("tasks", {}).values())
        status_counts: dict[str, int] = {}
        for t in tasks:
            s = t.get("status", "?")
            status_counts[s] = status_counts.get(s, 0) + 1
        boards.append({
            "name":          data.get("board", f.stem),
            "task_count":    len(tasks),
            "status_counts": status_counts,
            "has_active":    any(t.get("status") not in {"done","error","cancelled"} for t in tasks),
        })
    return boards


def _elapsed_seconds(started_at: str | None) -> float | None:
    if not started_at:
        return None
    try:
        t = datetime.fromisoformat(started_at)
        return (datetime.now() - t).total_seconds()
    except Exception:
        return None


def _board_detail(board_name: str) -> dict | None:
    path = KANBAN_DIR / f"{board_name}.json"
    if not path.exists():
        return None
    data = _read_json(path)
    if not isinstance(data, dict):
        return None
    tasks = list(data.get("tasks", {}).values())
    workers_dir = KANBAN_DIR / board_name / "workers"
    for task in tasks:
        tid = task.get("id") or ""
        cache = workers_dir / f"{tid}.json"
        if cache.exists():
            worker_data = _read_json(cache)
            if isinstance(worker_data, dict):
                task["worker_output"] = worker_data.get("output") or worker_data.get("final") or ""
                task["started_at"]    = worker_data.get("started_at") or task.get("created_at")
                task["elapsed_s"]     = _elapsed_seconds(task.get("started_at"))
    return {**data, "tasks": tasks}


def _list_meetings() -> list[dict]:
    meetings = []
    if not MEETINGS_DIR.exists():
        return meetings
    for f in sorted(MEETINGS_DIR.glob("mtg_*.json"), reverse=True):
        data = _read_json(f)
        if not isinstance(data, dict):
            continue
        mid = data.get("meeting_id") or ""
        meetings.append({
            "meeting_id":        mid,
            "name":              data.get("name") or mid,
            "created_at":        data.get("created_at"),
            "closed_at":         data.get("closed_at"),
            "agenda":            data.get("agenda") or "",
            "participant_count": len(data.get("participants") or {}),
            "participants":      list((data.get("participants") or {}).keys()),
            "has_conclusion":    bool(data.get("conclusion")),
        })
    return meetings


def _meeting_detail(meeting_id: str) -> dict | None:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        return None
    return _read_json(path)


def _cost_summary() -> dict:
    rows = _read_jsonl(SESSIONS_DIR / "usage_log.jsonl")
    total_in = total_out = 0
    total_cost = 0.0
    by_model: dict[str, dict] = {}
    by_session: dict[str, dict] = {}
    for r in rows:
        model = r.get("model") or "unknown"
        in_t  = int(r.get("in") or 0)
        out_t = int(r.get("out") or 0)
        cost  = _calc_cost(model, in_t, out_t)
        sid   = r.get("session_id") or ""
        total_in += in_t; total_out += out_t; total_cost += cost
        m = by_model.setdefault(model, {"in": 0, "out": 0, "cost": 0.0, "calls": 0})
        m["in"] += in_t; m["out"] += out_t; m["cost"] += cost; m["calls"] += 1
        s = by_session.setdefault(sid, {"in": 0, "out": 0, "cost": 0.0, "model": model})
        s["in"] += in_t; s["out"] += out_t; s["cost"] += cost
    return {
        "total_in":   total_in,
        "total_out":  total_out,
        "total_cost": round(total_cost, 6),
        "by_model":   by_model,
        "by_session": by_session,
        "prices":     _PRICE,
    }


# ── Chat (web sessions) ───────────────────────────────────────────────────

class _WebStreamUI:
    """Streams agent events to a SimpleQueue for SSE delivery.
    Compatible with ConsoleUI's interface — unknown methods are silently ignored.
    """
    label   = "web"
    enabled = False

    def __init__(self, q: "queue.SimpleQueue[dict]") -> None:
        self._q = q

    def _push(self, **kwargs: Any) -> None:
        try:
            self._q.put_nowait(kwargs)
        except Exception:
            pass

    def session_start(self, session_id: str, task_id: str) -> None:
        self._push(type="session_start", session_id=session_id)

    def model_start(self, iteration: int) -> None:
        self._push(type="iteration", i=iteration)

    def tool_start(self, name: str, args: dict) -> None:
        self._push(type="tool_start", name=name,
                   args=json.dumps(args, ensure_ascii=False, indent=2))

    def tool_end(self, name: str, result: str) -> None:
        self._push(type="tool_end", name=name)

    def event(self, label: str, detail: str = "") -> None:
        self._push(type="event", label=label, detail=detail)

    def compact(self, reason: str = "") -> None:
        self._push(type="compact", reason=reason)

    def final_answer(self, text: str, iterations: int) -> None:
        self._push(type="final_answer", text=text, iterations=iterations)

    def saved(self, path: str) -> None:
        self._push(type="saved", path=path)

    def println(self, line: str) -> None:
        self._push(type="print", text=line)

    def stop(self) -> None:
        pass

    def __getattr__(self, name: str):
        return lambda *a, **kw: None


# {session_id: {"history": [...], "q": SimpleQueue, "running": bool}}
_chat_sessions: dict[str, dict] = {}


# ── API routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/api/overview")
async def overview() -> dict:
    sessions = _list_sessions()
    boards   = _list_boards()
    meetings = _list_meetings()
    costs    = _cost_summary()
    return {
        "session_count":      len(sessions),
        "active_board_count": sum(1 for b in boards if b["has_active"]),
        "board_count":        len(boards),
        "meeting_count":      len(meetings),
        "open_meeting_count": sum(1 for m in meetings if not m["closed_at"]),
        "total_cost":         costs["total_cost"],
        "total_in_tokens":    costs["total_in"],
        "total_out_tokens":   costs["total_out"],
        "recent_sessions":    sessions[:8],
        "active_boards":      [b for b in boards if b["has_active"]],
        "open_meetings":      [m for m in meetings if not m["closed_at"]],
    }


# ── Sessions ──────────────────────────────────────────────────────────────

@app.get("/api/sessions")
async def list_sessions() -> list:
    usage = _usage_by_session()
    sessions = _list_sessions()
    for s in sessions:
        u = usage.get(s["id"], {})
        s["in_tokens"]  = u.get("in", 0)
        s["out_tokens"] = u.get("out", 0)
        s["cost"]       = round(u.get("cost", 0.0), 6)
    return sessions


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    msgs  = _session_messages(session_id)
    usage = _usage_by_session().get(session_id, {})
    return {
        "session_id": session_id,
        "messages":   msgs,
        "in_tokens":  usage.get("in", 0),
        "out_tokens": usage.get("out", 0),
        "cost":       round(usage.get("cost", 0.0), 6),
        "model":      usage.get("model", ""),
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    path = SESSIONS_DIR / f"{session_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    path.unlink()
    # Also clean up spill cache
    spill = SESSIONS_DIR / ".tool_cache" / session_id
    if spill.exists():
        shutil.rmtree(spill, ignore_errors=True)
    # Remove from in-memory chat sessions
    _chat_sessions.pop(session_id, None)
    return {"ok": True}


# ── Kanban ────────────────────────────────────────────────────────────────

@app.get("/api/kanban")
async def list_boards() -> list:
    return _list_boards()


@app.get("/api/kanban/{board_name}")
async def get_board(board_name: str) -> dict:
    d = _board_detail(board_name)
    if d is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return d


@app.delete("/api/kanban/{board_name}")
async def delete_board(board_name: str) -> dict:
    board_file = KANBAN_DIR / f"{board_name}.json"
    if not board_file.exists():
        raise HTTPException(status_code=404, detail="Board not found")
    board_file.unlink()
    board_dir = KANBAN_DIR / board_name
    if board_dir.exists():
        shutil.rmtree(board_dir, ignore_errors=True)
    return {"ok": True}


# ── Meetings ──────────────────────────────────────────────────────────────

@app.get("/api/meetings")
async def list_meetings() -> list:
    return _list_meetings()


@app.get("/api/meetings/{meeting_id}")
async def get_meeting(meeting_id: str) -> dict:
    d = _meeting_detail(meeting_id)
    if d is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return d


@app.delete("/api/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str) -> dict:
    path = MEETINGS_DIR / f"{meeting_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Meeting not found")
    path.unlink()
    return {"ok": True}


# ── Costs ─────────────────────────────────────────────────────────────────

@app.get("/api/costs")
async def costs() -> dict:
    return _cost_summary()


# ── Chat ──────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_send(body: dict) -> dict:
    sid     = body.get("session_id") or new_session_id()
    message = (body.get("message") or "").strip()
    model   = body.get("model") or None
    provider = body.get("provider") or None

    if not message:
        raise HTTPException(status_code=400, detail="message required")

    sess = _chat_sessions.get(sid)
    if sess and sess.get("running"):
        raise HTTPException(status_code=409, detail="session busy")

    q: "queue.SimpleQueue[dict]" = queue.SimpleQueue()
    history = (sess or {}).get("history", [])
    _chat_sessions[sid] = {"history": history, "q": q, "running": True}

    def _run() -> None:
        try:
            from ..agent import GeneralAgent
            ui = _WebStreamUI(q)
            agent = GeneralAgent(
                model=model,
                provider=provider,
                max_iterations=30,
                self_review=False,
                ui=ui,
                session_id=sid,
            )
            result = agent.run(message, history=history)
            _chat_sessions[sid]["history"] = result.get("messages", [])
            q.put({"type": "done", "final": result.get("final", "")})
        except Exception as exc:
            q.put({"type": "error", "error": str(exc)})
        finally:
            _chat_sessions[sid]["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return {"session_id": sid, "status": "running"}


@app.get("/api/chat/{session_id}/stream")
async def chat_stream(session_id: str) -> StreamingResponse:
    """SSE stream for a running chat session. Closes when agent finishes."""
    def generate() -> Generator[str, None, None]:
        # Wait up to 30s for the session to appear
        for _ in range(60):
            if session_id in _chat_sessions:
                break
            time.sleep(0.5)

        sess = _chat_sessions.get(session_id)
        if not sess:
            yield 'data: {"type":"error","error":"session not found"}\n\n'
            return

        q = sess["q"]
        while True:
            try:
                event = q.get(timeout=60)
            except queue.Empty:
                yield 'data: {"type":"heartbeat"}\n\n'
                continue

            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if event.get("type") in ("done", "error"):
                break

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Dashboard live events ─────────────────────────────────────────────────

@app.get("/api/events")
async def sse_events() -> StreamingResponse:
    def generate() -> Generator[str, None, None]:
        while True:
            try:
                boards   = _list_boards()
                meetings = _list_meetings()
                costs    = _cost_summary()
                active_board_details = []
                for b in boards:
                    if b["has_active"]:
                        d = _board_detail(b["name"])
                        if d:
                            active_board_details.append(d)
                data = {
                    "boards":   active_board_details,
                    "meetings": [_meeting_detail(m["meeting_id"]) for m in meetings
                                 if not m["closed_at"] and m["meeting_id"]],
                    "cost":     costs["total_cost"],
                }
                yield f"data: {json.dumps(data)}\n\n"
            except Exception:
                yield "data: {}\n\n"
            time.sleep(3)

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Dev server launcher ───────────────────────────────────────────────────

def run(port: int = 7654, host: str = "127.0.0.1") -> None:
    import uvicorn
    print(f"  Agent Dashboard → http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")
