"""Minimal, deterministic updates for human-readable Knowledge Hub indexes."""

from __future__ import annotations

import re
from typing import Any, Dict, Mapping


CORE_INDEXES = (
    "indexes/by-owner.md",
    "indexes/by-review-date.md",
    "indexes/by-status.md",
)


def _ensure_newline(text: str) -> str:
    return text.rstrip() + "\n"


def _remove_exact_lines(text: str, patterns: tuple) -> str:
    lines = text.splitlines()
    kept = [line for line in lines if not any(pattern.fullmatch(line.strip()) for pattern in patterns)]
    return _ensure_newline("\n".join(kept))


def _insert_under_heading(text: str, heading: str, line: str) -> str:
    lines = text.rstrip().splitlines()
    heading_index = next((index for index, value in enumerate(lines) if value.strip() == heading), None)
    if heading_index is None:
        lines.extend(["", heading, "", line])
        return _ensure_newline("\n".join(lines))
    insert_at = heading_index + 1
    while insert_at < len(lines) and not lines[insert_at].startswith("## "):
        insert_at += 1
    while insert_at > heading_index + 1 and lines[insert_at - 1] == "":
        insert_at -= 1
    lines.insert(insert_at, line)
    return _ensure_newline("\n".join(lines))


def update_core_indexes(contents: Mapping[str, str], item: Mapping[str, Any]) -> Dict[str, str]:
    item_id = str(item["id"])
    escaped = re.escape(item_id)

    owner_text = contents["indexes/by-owner.md"]
    owner_text = _remove_exact_lines(owner_text, (re.compile(r"- `" + escaped + r"`"),))
    owner_text = _insert_under_heading(owner_text, "## {}".format(item["owner"]), "- `{}`".format(item_id))

    review_text = contents["indexes/by-review-date.md"]
    review_text = _remove_exact_lines(review_text, (re.compile(r"- \d{4}-\d{2}-\d{2}: `" + escaped + r"`"),))
    review_text = _ensure_newline(review_text) + "- {}: `{}`\n".format(item["review_after"], item_id)

    status_text = contents["indexes/by-status.md"]
    status_text = _remove_exact_lines(
        status_text,
        (re.compile(r"- (?:draft|active|reviewing|archived|superseded|rejected|personal): `" + escaped + r"`"),),
    )
    status_text = _ensure_newline(status_text) + "- {}: `{}`\n".format(item["status"], item_id)

    return {
        "indexes/by-owner.md": owner_text,
        "indexes/by-review-date.md": review_text,
        "indexes/by-status.md": status_text,
    }


def update_project_index(text: str, item: Mapping[str, Any], project_name: str = "") -> str:
    item_id = str(item["id"])
    exact = re.compile(r"- .*; `" + re.escape(item_id) + r"`")
    text = _remove_exact_lines(text, (exact,))
    domain = str(item.get("domain", ""))
    if not domain.startswith("projects/"):
        return text
    project_id = domain.split("/", 1)[1]
    heading = "## {}".format(project_name or project_id)
    line = "- {}: `{}`; `{}`".format(item.get("title", item_id), item.get("path", ""), item_id)
    return _insert_under_heading(text, heading, line)


def update_topic_index(text: str, item: Mapping[str, Any]) -> str:
    item_id = str(item["id"])
    exact = re.compile(r"- .*; `" + re.escape(item_id) + r"`")
    text = _remove_exact_lines(text, (exact,))
    line = "- {}: `{}`; `{}`".format(item.get("title", item_id), item.get("path", ""), item_id)
    return _insert_under_heading(text, "## 受控生成条目", line)
