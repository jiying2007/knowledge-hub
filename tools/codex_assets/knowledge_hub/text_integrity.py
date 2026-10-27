"""Recognize explicit tool-output truncation markers without exporting text.

A match requires source review. It is not proof of lost bytes, semantic approval,
permission to reconstruct text, or an exception for quoted historical material.
The caller must exclude private content before obtaining the bounded bytes.
"""
from __future__ import annotations

import re

MAX_SCAN_BYTES = 4 * 1024 * 1024
_TOOL_TRUNCATION = re.compile(
    rb"(?:\xe2\x80\xa6|\.{3})[ \t]*[0-9][0-9,]{0,11}[ \t]+"
    rb"(?:tokens?|characters?|chars?)[ \t]+truncated[ \t]*"
    rb"(?:\xe2\x80\xa6|\.{3})",
    re.IGNORECASE,
)


def has_persisted_tool_truncation(data: bytes) -> bool:
    """Return an aggregate risk flag only; never expose matching text/offsets."""
    if not isinstance(data, bytes):
        raise TypeError("text integrity scan requires bounded bytes")
    if len(data) > MAX_SCAN_BYTES:
        raise ValueError("text integrity scan exceeds byte budget")
    return _TOOL_TRUNCATION.search(data) is not None
