"""view_image: lets an agent actually see an image file's real pixel content.

Tool results are text-only by API protocol (a function/tool call cannot itself
carry an image back to the model) -- so this tool reads and base64-encodes the
image, stashes it on `runtime["_pending_images"]`, and returns a plain text
confirmation as its own tool result. The agent loop (see agent.py's
_inject_pending_images, called right after every tool result is appended) then
appends a synthetic user message carrying the actual image content parts, so the
image is delivered as part of the *next* model turn -- not this tool result.
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

from ..safety import resolve_readable_path
from .registry import json_result, registry

_IMAGE_MIME_FALLBACK = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

_MAX_IMAGE_BYTES = 20 * 1024 * 1024  # 20MB -- comfortably under typical provider upload caps


def _view_image(args: dict, runtime: dict) -> str:
    raw_path = args.get("path")
    if not raw_path:
        return json_result(success=False, error="path is required")
    path = resolve_readable_path(raw_path)
    if not path.is_file():
        return json_result(success=False, error=f"File not found: {path}")

    suffix = path.suffix.lower()
    mime = mimetypes.guess_type(str(path))[0] or _IMAGE_MIME_FALLBACK.get(suffix)
    if not mime or not mime.startswith("image/"):
        return json_result(
            success=False,
            error=f"Not a recognized image file: {path} (suffix {suffix!r})",
        )

    data = path.read_bytes()
    if len(data) > _MAX_IMAGE_BYTES:
        return json_result(
            success=False,
            error=f"Image too large ({len(data):,} bytes > {_MAX_IMAGE_BYTES:,} limit): {path}",
        )

    detail = args.get("detail") if args.get("detail") in ("low", "high", "auto") else None
    question = args.get("question")
    b64 = base64.b64encode(data).decode("ascii")

    pending = runtime.setdefault("_pending_images", [])
    label = f"[Image: {path}]" + (f" -- focus: {question}" if question else "")
    pending.append({"type": "text", "text": label})
    pending.append({
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{b64}", **({"detail": detail} if detail else {})},
    })

    return json_result(
        success=True,
        path=str(path),
        bytes=len(data),
        note=(
            "Image loaded. It will be shown to you as an actual image on your next "
            "turn, not in this tool result."
            + (f" Focus question noted: {question}" if question else "")
        ),
    )


registry.register(
    "view_image",
    {
        "description": (
            "Load an image file so you can actually see its real pixel content on "
            "your NEXT turn (tool results are text-only, so the image itself is "
            "delivered as part of the next model turn, not in this tool's return "
            "value). Use this whenever you need to judge or describe what an image "
            "actually shows rather than infer it from a filename, a report's "
            "description, or another participant's claim."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to the image file to load.",
                },
                "question": {
                    "type": "string",
                    "description": (
                        "Optional: what you specifically want to verify or look for "
                        "in this image, echoed back alongside it for your own "
                        "reference when it appears next turn."
                    ),
                },
                "detail": {
                    "type": "string",
                    "enum": ["low", "high", "auto"],
                    "description": "Optional vision detail level to request (defaults to auto).",
                },
            },
            "required": ["path"],
        },
    },
    _view_image,
)
