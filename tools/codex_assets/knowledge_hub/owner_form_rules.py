"""Pure owner-decision form validation rules."""

from __future__ import annotations

from typing import Any, Dict


def owner_decision_target_mismatch(
    owner_decision: Any,
    target_decision: Any,
) -> Dict[str, Any] | None:
    owner = str(owner_decision or "")
    target = str(target_decision or "")
    if target.startswith(("domains/projects/", "domains/personal/")):
        return {
            "expected": (
                "projects/<project>/...、notes/personal/... 或终止类字面目标"
            ),
            "reason_zh": (
                "owner target 当前契约不接受 domains/projects 或 "
                "domains/personal 非规范入口。"
            ),
        }
    if owner == "archive-only":
        if target == "archive-only" or "/archive/" in target:
            return None
        return {
            "expected": ["archive-only", "target path containing /archive/"],
            "reason_zh": (
                "archive-only 只能搭配 archive-only 字面目标或明确的 "
                "archive 路径，不能指向 current、validation 或 decisions 目标。"
            ),
        }
    terminal_targets = {
        "reference-only": {"reference-only"},
        "no-migration": {"no-migration"},
        "rejected": {"no-migration"},
    }
    if owner in terminal_targets and target not in terminal_targets[owner]:
        return {
            "expected": sorted(terminal_targets[owner]),
            "reason_zh": (
                "终止类 owner_decision 只能搭配同语义的 target_decision，"
                "不能指向项目落地路径。"
            ),
        }
    if owner not in terminal_targets and target in {
        "reference-only",
        "no-migration",
    }:
        return {
            "expected": "与 owner_decision 构成有效配对的落地目标",
            "reason_zh": (
                "落地类 owner_decision 不能搭配 reference-only 或 "
                "no-migration 目标。"
            ),
        }
    return None
