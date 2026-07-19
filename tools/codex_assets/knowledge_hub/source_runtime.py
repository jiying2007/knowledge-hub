"""Registry-driven, report-only source availability checks."""

from __future__ import annotations

import datetime as dt
import pathlib
import shlex
import stat
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import (
    KnowledgeHubError,
    display_path,
    load_json,
    load_jsonl,
    resolve_inside,
    utc_timestamp,
)

BANNED_PATH_CHARS = set(";|&><`$*?[")
ALLOWED_PRIMITIVES = {"-d": "test -d", "-f": "test -f"}


def _registry_sources(root: pathlib.Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    payload = load_json(root / "registry/sources.json", {}) or {}
    current = payload.get("sources", [])
    if not isinstance(current, list):
        raise KnowledgeHubError("registry/sources.json field sources must be a list")
    retired = load_jsonl(root / "registry/retired-sources.jsonl")
    rows: List[Dict[str, Any]] = []
    seen: Dict[str, str] = {}
    for bucket, values in (("current", current), ("retired", retired)):
        for value in values:
            if not isinstance(value, dict):
                errors.append("{} source row must be an object".format(bucket))
                continue
            source_id = str(value.get("id", ""))
            if not source_id:
                errors.append("{} source row is missing id".format(bucket))
                continue
            if source_id in seen:
                errors.append(
                    "duplicate source id across {} and {}: {}".format(
                        seen[source_id], bucket, source_id
                    )
                )
                continue
            seen[source_id] = bucket
            row = dict(value)
            row["registry_bucket"] = bucket
            rows.append(row)
    return sorted(rows, key=lambda row: str(row["id"])), errors


def _parse_check(check: str) -> Tuple[str, str, str]:
    try:
        tokens = shlex.split(check)
    except ValueError as exc:
        return "", "", "invalid shell quoting: {}".format(exc)
    if len(tokens) == 4 and tokens[:2] == ["rtk", "test"]:
        primitive_tokens: Sequence[str] = tokens[2:]
    else:
        return "", "", "only rtk test -d/-f is allowed"
    if len(primitive_tokens) != 2 or primitive_tokens[0] not in ALLOWED_PRIMITIVES:
        return "", "", "only test -d and test -f are allowed"
    target = str(primitive_tokens[1])
    if not target:
        return "", "", "check target must not be empty"
    if any(character in target for character in BANNED_PATH_CHARS):
        return "", "", "check target contains shell control, expansion or glob characters"
    return ALLOWED_PRIMITIVES[str(primitive_tokens[0])], target, ""


def _resolve_registered_path(root: pathlib.Path, value: str) -> pathlib.Path:
    return resolve_inside(root, value)


def _validated_target(
    root: pathlib.Path, check_path: str, source: Mapping[str, Any]
) -> pathlib.Path:
    source_path = str(source.get("path", ""))
    if not source_path:
        raise KnowledgeHubError("source registry path is missing")
    check_target = _resolve_registered_path(root, check_path)
    source_target = _resolve_registered_path(root, source_path)
    if check_target != source_target and source_target not in check_target.parents:
        raise KnowledgeHubError(
            "check target must equal or stay under the registered source path"
        )
    return check_target


def _source_row(
    root: pathlib.Path,
    source: Mapping[str, Any],
    plan: bool,
) -> Dict[str, Any]:
    source_id = str(source.get("id", ""))
    check = str(source.get("check", ""))
    no_check_reason = str(source.get("no_check_reason", ""))
    base = {
        "source_id": source_id,
        "registry_bucket": str(source.get("registry_bucket", "")),
        "source_status": str(source.get("status", "")),
        "executed": False,
        "exit_code": None,
        "check_command": check,
        "primitive": "",
        "path": display_path(source.get("path", "")),
        "source_body_read": False,
    }
    if not check:
        if no_check_reason:
            return dict(
                base,
                status="not-applicable",
                result="documented-no-check-reason",
                reason_zh="该 source 明确记录 no_check_reason；未执行 runtime check。",
            )
        return dict(
            base,
            status="fail",
            result="missing-runtime-check-contract",
            reason_zh="source 同时缺少 check 与 no_check_reason。",
        )
    primitive, check_path, parse_error = _parse_check(check)
    if parse_error:
        return dict(
            base,
            status="fail",
            result="rejected-runtime-check",
            reason_zh="拒绝执行：{}。".format(parse_error),
        )
    base["primitive"] = primitive
    base["path"] = display_path(check_path)
    try:
        target = _validated_target(root, check_path, source)
    except KnowledgeHubError as exc:
        return dict(
            base,
            status="fail",
            result="rejected-runtime-check",
            reason_zh="拒绝执行：{}。".format(str(exc)),
        )
    if plan:
        return dict(
            base,
            status="planned",
            result="planned",
            reason_zh="只读路径类型检查计划；不读取 source 正文。",
        )
    try:
        target_stat = target.lstat()
        if stat.S_ISLNK(target_stat.st_mode):
            raise KnowledgeHubError("runtime check target must not be a symlink")
        matched = (
            stat.S_ISDIR(target_stat.st_mode)
            if primitive == "test -d"
            else stat.S_ISREG(target_stat.st_mode)
        )
    except (KnowledgeHubError, OSError):
        matched = False
    return dict(
        base,
        status="pass" if matched else "fail",
        executed=True,
        exit_code=0 if matched else 1,
        result=(
            "path-exists"
            if matched and primitive == "test -d"
            else "file-exists"
            if matched
            else "path-missing-inaccessible-or-wrong-type"
        ),
        reason_zh="直接执行只读路径类型检查；不启动 shell，不读取 source 正文。",
    )


def run_source_checks(
    root: pathlib.Path,
    today: dt.date,
    scope: str = "all",
    source_id_filter: str = "",
    plan: bool = False,
) -> Dict[str, Any]:
    root = root.resolve()
    if scope not in {"all", "current"}:
        raise KnowledgeHubError("source check scope must be all or current")
    rows, errors = _registry_sources(root)
    current_count = sum(row["registry_bucket"] == "current" for row in rows)
    retired_count = sum(row["registry_bucket"] == "retired" for row in rows)
    if scope == "current":
        selected = [row for row in rows if row["registry_bucket"] == "current"]
    else:
        selected = list(rows)
    if source_id_filter:
        selected_ids = {str(row["id"]) for row in selected}
        if source_id_filter not in selected_ids:
            errors.append(
                "source-id outside selected scope or missing: {}".format(source_id_filter)
            )
            selected = []
        else:
            selected = [row for row in selected if row["id"] == source_id_filter]
    result_rows = [_source_row(root, row, plan) for row in selected]
    failed = [row for row in result_rows if row["status"] == "fail"]
    executed = [row for row in result_rows if row["executed"]]
    rejected = [row for row in result_rows if row["result"] == "rejected-runtime-check"]
    not_applicable = [row for row in result_rows if row["status"] == "not-applicable"]
    status = "fail" if errors or failed else "planned" if plan else "pass"
    expected_ids = [str(row["id"]) for row in selected]
    return {
        "schema_version": 2,
        "status": status,
        "root": display_path(root),
        "read_only": True,
        "report_only": True,
        "scope": scope,
        "source_id_filter": source_id_filter,
        "today": today.isoformat(),
        "generated_at": utc_timestamp(),
        "plan_only": plan,
        "source_check_health_contract": "runtime-all-registered-sources-v1",
        "source_check_health_executed": not plan,
        "source_body_read": False,
        "owner_gate_mutation": False,
        "memory_write": False,
        "automation_write": False,
        "execution_mode": "direct-filesystem-stat-no-shell",
        "allowed_primitives": ["test -d", "test -f"],
        "registry_source_count": len(rows),
        "current_source_count": current_count,
        "retired_source_count": retired_count,
        "expected_source_ids": expected_ids,
        "selected_source_ids": expected_ids,
        "row_count": len(result_rows),
        "executed_count": len(executed),
        "passed_count": sum(row["status"] == "pass" for row in result_rows),
        "failed_count": len(failed),
        "unsupported_count": 0,
        "rejected_count": len(rejected),
        "not_applicable_count": len(not_applicable),
        "rows": result_rows,
        "errors": errors,
        "limitations_zh": "只证明登记路径或文件在执行时存在且类型匹配，不证明内容正确、语义可迁移、owner 已签收或 active promotion 可成立。",
        "must_not": [
            "不得把 path-exists 当作内容正确",
            "不得关闭 owner gate",
            "不得生成 owner decision",
            "不得修改源项目",
            "不得写 memory",
        ],
    }
