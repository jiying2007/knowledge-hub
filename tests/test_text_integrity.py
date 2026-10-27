"""Explicit truncation residue is not a human review result."""
import pytest

from tools.codex_assets.knowledge_hub.text_integrity import (
    MAX_SCAN_BYTES, has_persisted_tool_truncation,
)


@pytest.mark.parametrize("text", [
    "review_status: delegated…2200 tokens truncated…后续摘要",
    "prefix... 123 tokens truncated ...suffix",
    "…1 token truncated…",
    "...1,234 characters truncated...",
    "…99 chars truncated…",
    "...17 TOKENS TRUNCATED...",
    "---\nreview_status: delegated…2200 tokens truncated…\n---\n正文",
    "```text\n…2200 tokens truncated…\n```",  # Quoted markers still need triage.
])
def test_explicit_counted_tool_markers_require_source_review(text):
    assert has_persisted_tool_truncation(text.encode("utf-8")) is True


@pytest.mark.parametrize("text", [
    "", "正常历史正文", "result flag TRUNCATED", "truncated output",
    "2200 tokens truncated", "…tokens truncated…", "...17 tokens retained...",
    "...17 seconds truncated...", "..17 tokens truncated..",
    "...1234567890123 tokens truncated...",  # Outside the bounded marker syntax.
])
def test_normal_prose_and_incomplete_phrases_are_not_declared_corrupt(text):
    assert has_persisted_tool_truncation(text.encode("utf-8")) is False


@pytest.mark.parametrize("value", [None, "…1 token truncated…", bytearray(b"x"), 1])
def test_requires_explicit_bytes(value):
    with pytest.raises(TypeError, match="bounded bytes"):
        has_persisted_tool_truncation(value)


def test_input_budget_has_exact_boundary_and_no_truncation_fallback():
    assert has_persisted_tool_truncation(b"x" * MAX_SCAN_BYTES) is False
    with pytest.raises(ValueError, match="byte budget"):
        has_persisted_tool_truncation(b"x" * (MAX_SCAN_BYTES + 1))


def test_marker_at_end_of_budget_is_still_seen():
    marker = "…2200 tokens truncated…".encode("utf-8")
    assert has_persisted_tool_truncation(b"x" * (MAX_SCAN_BYTES - len(marker)) + marker)


def test_invalid_utf8_elsewhere_does_not_hide_literal_byte_marker():
    assert has_persisted_tool_truncation(b"\xff...12 tokens truncated...\xfe") is True

def test_truncation_detector_is_security_critical():
    from pathlib import Path
    import json
    policy = json.loads((Path(__file__).resolve().parents[1] /
                         "registry/review-risk-policy.json").read_text(encoding="utf-8"))
    assert {"path": "tools/codex_assets/knowledge_hub/text_integrity.py",
            "review_class": "security-critical"} in policy["rules"]
