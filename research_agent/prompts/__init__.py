from __future__ import annotations

from .base import BASE_SYSTEM_PROMPT
from .builder import build_system_prompt
from .compact import COMPACT_MODE_PROMPT
from .roles import ROLE_PROFILES
from .self_review import SELF_REVIEW_PROMPT

__all__ = [
    "BASE_SYSTEM_PROMPT",
    "build_system_prompt",
    "COMPACT_MODE_PROMPT",
    "ROLE_PROFILES",
    "SELF_REVIEW_PROMPT",
]
