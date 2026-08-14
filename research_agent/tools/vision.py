"""view_image: lets an agent actually see an image file's real pixel content.

Tool results are text-only by API protocol (a function/tool call cannot itself
carry an image back to the model) -- so this tool reads the image, downscales/
recompresses it for delivery (see _encode_for_delivery), stashes it on
runtime["_pending_images"], and returns a plain text confirmation as its own tool
result. The agent loop (see agent.py's main tool-call loop, which flushes
_pending_images once after each full batch of tool_calls is processed) then
appends a synthetic user message carrying the actual image content parts, so the
image is delivered as part of the *next* model turn -- not this tool result.

Only the most recently injected batch ever carries live pixel data: as soon as a
newer batch is injected, agent.py's _compress_previous_images() strips the
previous batch's image_url parts down to a text placeholder (the text labels --
path, focus question -- are kept). Otherwise every iteration for the rest of the
turn would resend every image ever viewed, in full, again -- pure repeated token
cost with no new information, and the single biggest driver of a VisualAuditor-
style turn blowing past the compaction threshold on image volume alone.
"""
from __future__ import annotations

import base64
import io
import mimetypes

from PIL import Image, ImageOps

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

_MAX_IMAGE_BYTES = 20 * 1024 * 1024  # refuse to even attempt an absurdly large source file

# Vision APIs tile/downsample internally past a certain resolution -- shipping more
# pixels than this buys no real detail at typical "high" detail settings, only more
# bytes to upload and more tokens to bill, and (since the agent loop resends the
# whole running conversation on every subsequent call within a turn) that cost is
# paid again on every later call in the same turn, not just once.
_MAX_SIDE_PX = 1536
_TARGET_ENCODED_BYTES = 900_000  # soft budget for the encoded (pre-base64) image
_JPEG_QUALITY_STEPS = (85, 75, 65, 55, 45)


_API_SUPPORTED_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _encode_for_delivery(data: bytes) -> tuple[str, str] | None:
    """Returns (mime, base64_str) for the bytes actually handed to the model --
    orientation-corrected, downscaled to _MAX_SIDE_PX, and recompressed to fit
    _TARGET_ENCODED_BYTES where possible. Returns None if the file cannot be
    delivered as one of the vision API's supported formats at all (undecodable by
    Pillow -- an exotic/corrupted file, or one whose extension lies about its real
    content, e.g. this project's own "HTML saved as .png" fixtures)."""
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        img = None

    if img is None:
        # Not decodable by Pillow at all -- there is no safe way to re-encode bytes
        # we can't parse, and shipping them as-is (the old behavior) just traded a
        # clear tool-level error now for a confusing API 400 one or two turns later.
        # The caller must surface this as a failed tool call instead.
        return None

    # Trust Pillow's own detected format over the file extension/suffix -- a
    # mismatched extension (this project's evidence includes real examples of
    # non-image content saved under an image extension) must not decide the MIME
    # type sent to the API.
    detected_mime = f"image/{img.format.lower()}" if img.format else None
    if detected_mime == "image/jpg":
        detected_mime = "image/jpeg"

    if (
        detected_mime in _API_SUPPORTED_MIMES
        and len(data) <= _TARGET_ENCODED_BYTES
        and max(img.size) <= _MAX_SIDE_PX
    ):
        # Already a supported format and within budget -- deliver the original
        # bytes untouched. Re-encoding a small/simple image can sometimes make it
        # *bigger* (e.g. JPEG block overhead on a near-solid-color PNG), and this
        # skips needlessly discarding the original encoding/metadata for images
        # that were never the problem.
        return detected_mime, base64.b64encode(data).decode("ascii")

    img = ImageOps.exif_transpose(img) or img
    if max(img.size) > _MAX_SIDE_PX:
        img.thumbnail((_MAX_SIDE_PX, _MAX_SIDE_PX), Image.LANCZOS)

    # "transparency" can appear in .info for palette/1-bit/grayscale modes too, not
    # just "P" -- e.g. a mode "1" image with a color-key transparency entry, which is
    # exactly the shape of one of this project's own real assets (a blank/placeholder
    # PNG whose *only* meaningful signal is that it's transparent).
    has_alpha = img.mode in ("RGBA", "LA") or "transparency" in img.info
    if has_alpha:
        # Preserve transparency losslessly -- e.g. a blank/placeholder asset is only
        # recognizable as blank because its alpha channel survives; flattening to
        # JPEG onto an opaque background would hide exactly the thing being judged.
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        if buf.tell() <= _TARGET_ENCODED_BYTES:
            return "image/png", base64.b64encode(buf.getvalue()).decode("ascii")
        # Still too big even as PNG at the resolution cap -- fall through to JPEG
        # rather than ship an oversized payload; transparency is lost here, but only
        # for images large enough that this is a rare path.
        img = img.convert("RGB")
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    for quality in _JPEG_QUALITY_STEPS:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        if buf.tell() <= _TARGET_ENCODED_BYTES or quality == _JPEG_QUALITY_STEPS[-1]:
            return "image/jpeg", base64.b64encode(buf.getvalue()).decode("ascii")


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
    encoded = _encode_for_delivery(data)
    if encoded is None:
        return json_result(
            success=False,
            error=(
                f"{path} claims to be an image (by extension) but Pillow could not "
                "decode it as pixel content -- treat this file as unreadable/corrupt "
                "rather than as a real image; do not guess at its visual content."
            ),
        )
    delivered_mime, b64 = encoded

    pending = runtime.setdefault("_pending_images", [])
    label = f"[Image: {path}]" + (f" -- focus: {question}" if question else "")
    pending.append({"type": "text", "text": label})
    pending.append({
        "type": "image_url",
        "image_url": {"url": f"data:{delivered_mime};base64,{b64}", **({"detail": detail} if detail else {})},
    })

    return json_result(
        success=True,
        path=str(path),
        bytes=len(data),
        delivered_bytes=len(b64) * 3 // 4,
        note=(
            "Image loaded (resized/recompressed for delivery if it was large). It "
            "will be shown to you as an actual image on your next turn, not in this "
            "tool result."
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
