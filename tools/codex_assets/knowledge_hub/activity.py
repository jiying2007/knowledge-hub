"""Deterministic v2 work-activity collection and reporting."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, load_json, load_jsonl, pretty_json, read_utf8_bounded
from .security import scan_secret_text


FACTS_SCHEMA_VERSION = 2
ITEM_SCHEMA_VERSION = 2
TIMEZONE_NAME = "Asia/Hong_Kong"
MAX_TEXT = 600
MAX_ITEMS = 300
MAX_COMMITS = 50
VALID_SCOPES = {"personal", "project", "portfolio"}
VALID_STATUSES = {"planned", "in_progress", "done", "blocked"}
VALID_VERIFICATION = {"verified", "reported", "missing"}


def report_timezone() -> dt.tzinfo:
    return dt.timezone(dt.timedelta(hours=8), name=TIMEZONE_NAME)


def report_period(
    period: str,
    as_of: dt.date,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> Tuple[dt.date, dt.date]:
    if period == "daily":
        return as_of, as_of
    if period == "weekly":
        return as_of - dt.timedelta(days=as_of.weekday()), as_of
    if period == "custom" and start and end and start <= end:
        return start, end
    raise KnowledgeHubError("custom period requires an inclusive start not after end")


def _safe(value: Any, maximum: int = MAX_TEXT) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if scan_secret_text(text):
        return "[已脱敏：检测到疑似凭证内容]"
    return text if len(text) <= maximum else text[: maximum - 1].rstrip() + "…"


def _safe_values(value: Any, *, hide_paths: bool = False, limit: int = 30) -> List[str]:
    if not isinstance(value, list):
        return []
    selected: List[str] = []
    for item in value[:limit]:
        text = _safe(item)
        if hide_paths and (text.startswith(("/", "~/")) or re.match(r"^[A-Za-z]:[\\/]", text)):
            text = "[本地路径已省略]"
        selected.append(text)
    return selected


def _date(value: Any) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def load_activity_config(root: pathlib.Path) -> Dict[str, Any]:
    payload = load_json(root / "local/activity-report.json", {}) or {}
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        return {"valid": False, "reason": "missing-or-non-v2-config"}
    scope = str(payload.get("default_scope", ""))
    return {
        "valid": bool(payload.get("enabled") is True and scope in VALID_SCOPES),
        "enabled": payload.get("enabled") is True,
        "subject_id": _safe(payload.get("subject_id"), 160),
        "display_name": _safe(payload.get("display_name"), 160),
        "default_scope": scope,
        "timezone": _safe(payload.get("timezone"), 80) or TIMEZONE_NAME,
        "receipt_persistence": payload.get("receipt_persistence") is True,
        "retention_days": int(payload.get("retention_days", 45)) if str(payload.get("retention_days", 45)).isdigit() else 45,
    }


def normalize_item(payload: Mapping[str, Any], *, source_kind: str, source_ref: str) -> Dict[str, Any]:
    if payload.get("schema_version") != ITEM_SCHEMA_VERSION or payload.get("kind") != "work-activity-item":
        raise KnowledgeHubError("work item must be work-activity-item schema v2")
    item_id = _safe(payload.get("item_id"), 160)
    subject_id = _safe(payload.get("subject_id"), 160)
    project_id = _safe(payload.get("project_id"), 160)
    activity_date = _date(payload.get("activity_date"))
    status = str(payload.get("status", ""))
    verification = str(payload.get("verification", ""))
    title = _safe(payload.get("title"), 360)
    if not item_id or not subject_id or not activity_date or not title:
        raise KnowledgeHubError("work item requires item_id, subject_id, activity_date and title")
    if status not in VALID_STATUSES or verification not in VALID_VERIFICATION:
        raise KnowledgeHubError("work item status or verification is invalid")
    if payload.get("raw_content_stored") is not False:
        raise KnowledgeHubError("work item must declare raw_content_stored=false")
    evidence = _safe_values(payload.get("evidence_refs"), hide_paths=True)
    if status == "done" and verification == "verified" and not evidence:
        raise KnowledgeHubError("verified done item requires evidence_refs")
    return {
        "schema_version": ITEM_SCHEMA_VERSION,
        "kind": "work-activity-item",
        "item_id": item_id,
        "subject_id": subject_id,
        "project_id": project_id,
        "activity_date": activity_date.isoformat(),
        "title": title,
        "status": status,
        "verification": verification,
        "outcomes": _safe_values(payload.get("outcomes")),
        "evidence_refs": evidence,
        "blockers": _safe_values(payload.get("blockers")),
        "next_actions": _safe_values(payload.get("next_actions")),
        "source": {"kind": source_kind, "ref": _safe(source_ref, 200)},
        "raw_content_stored": False,
    }


def _json_files(root: pathlib.Path) -> Iterable[pathlib.Path]:
    if not root.is_dir():
        return []
    return (
        path
        for path in sorted(root.rglob("*.json"))
        if path.is_file() and not path.is_symlink() and not any(part.startswith(".") for part in path.relative_to(root).parts)
    )


def collect_work_items(
    root: pathlib.Path,
    start: dt.date,
    end: dt.date,
    *,
    subject_id: str = "",
    project_id: str = "",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    selected: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    invalid_count = 0
    receipt_count = 0
    receipt_root = root / ".tmp/activity/receipts"
    for path in _json_files(receipt_root):
        try:
            payload = json.loads(read_utf8_bounded(path, 256 * 1024, "activity receipt"))
            if (
                not isinstance(payload, dict)
                or payload.get("schema_version") != 2
                or payload.get("kind") != "activity-session-receipt"
                or payload.get("raw_content_stored") is not False
                or not isinstance(payload.get("work_items"), list)
            ):
                raise KnowledgeHubError("invalid activity receipt")
            receipt_count += 1
            for raw in payload["work_items"][:30]:
                item = normalize_item(raw, source_kind="session-wrap", source_ref=path.stem)
                item_date = _date(item["activity_date"])
                if item_date and start <= item_date <= end:
                    selected[(item["subject_id"], item["project_id"], item["item_id"])] = item
        except (KnowledgeHubError, json.JSONDecodeError, OSError):
            invalid_count += 1
    item_root = root / ".tmp/activity/items"
    explicit_count = 0
    for path in _json_files(item_root):
        try:
            payload = json.loads(read_utf8_bounded(path, 128 * 1024, "work item"))
            item = normalize_item(payload, source_kind="explicit-item", source_ref=path.stem)
            item_date = _date(item["activity_date"])
            if item_date and start <= item_date <= end:
                selected[(item["subject_id"], item["project_id"], item["item_id"])] = item
                explicit_count += 1
        except (KnowledgeHubError, json.JSONDecodeError, OSError):
            invalid_count += 1
    rows = [
        item
        for item in selected.values()
        if (not subject_id or item["subject_id"] == subject_id)
        and (not project_id or item["project_id"] == project_id)
    ]
    rows.sort(key=lambda row: (row["activity_date"], row["project_id"], row["item_id"]))
    return rows[:MAX_ITEMS], {
        "available": item_root.is_dir() or receipt_root.is_dir(),
        "valid_count": len(rows),
        "invalid_count": invalid_count,
        "explicit_count": explicit_count,
        "receipt_count": receipt_count,
        "truncated": len(rows) > MAX_ITEMS,
    }


def _selected_dates(row: Mapping[str, Any], start: dt.date, end: dt.date) -> List[str]:
    fields = ("created_at", "updated_at", "captured_at", "ai_generated_at", "last_verified")
    return sorted({parsed.isoformat() for field in fields for parsed in [_date(row.get(field))] if parsed and start <= parsed <= end})


def collect_registry(root: pathlib.Path, start: dt.date, end: dt.date, project_id: str = "") -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for raw in load_jsonl(root / "registry/items.jsonl"):
        dates = _selected_dates(raw, start, end)
        domain = _safe(raw.get("domain"), 160)
        if not dates or (project_id and project_id not in domain):
            continue
        rows.append({
            "id": _safe(raw.get("id"), 160),
            "title": _safe(raw.get("title"), 360),
            "summary_zh": _safe(raw.get("summary_zh")),
            "domain": domain,
            "kind": _safe(raw.get("kind"), 80),
            "status": _safe(raw.get("status"), 80),
            "activity_dates": dates,
            "manual_validation_pending": bool(raw.get("manual_validation_pending", False)),
            "authority": "hub-registry",
        })
    return sorted(rows, key=lambda row: (row["domain"], row["title"]))


def _git(repo: pathlib.Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C.UTF-8"})
    try:
        return subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True, timeout=15, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess([], 127, "", str(exc))


def _repository_candidates(root: pathlib.Path, codex_root: pathlib.Path) -> Tuple[List[Tuple[str, pathlib.Path]], int]:
    candidates: List[Tuple[str, pathlib.Path]] = [("knowledge-hub", root), ("codex", codex_root)]
    local = load_json(root / "local/workspaces.json", {}) or {}
    for row in local.get("workspaces", []) if isinstance(local, dict) else []:
        if isinstance(row, dict) and row.get("present"):
            candidates.append((str(row.get("repo_id", "workspace")), pathlib.Path(str(row.get("path", "")))))
    report_local = load_json(root / "local/activity-report.json", {}) or {}
    for row in report_local.get("repositories", []) if isinstance(report_local, dict) else []:
        if isinstance(row, dict) and row.get("enabled") is not False:
            candidates.append((str(row.get("repo_id", "local")), pathlib.Path(str(row.get("path", "")))))
    unique: Dict[str, Tuple[str, pathlib.Path]] = {}
    for repo_id, path in candidates:
        resolved = path.expanduser().resolve(strict=False)
        unique.setdefault(str(resolved), (repo_id, resolved))
    return list(unique.values()), len(unique)


def collect_git(
    root: pathlib.Path,
    codex_root: pathlib.Path,
    start: dt.date,
    end: dt.date,
    project_id: str = "",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    candidates, registered = _repository_candidates(root, codex_root)
    for repo_id, path in candidates:
        if project_id and project_id not in repo_id:
            continue
        if not path.is_dir() or not (path / ".git").exists():
            continue
        until = end + dt.timedelta(days=1)
        result = _git(path, [
            "log", "--since={}T00:00:00+08:00".format(start.isoformat()),
            "--until={}T00:00:00+08:00".format(until.isoformat()),
            "--max-count={}".format(MAX_COMMITS), "--date=iso-strict",
            "--pretty=format:%H%x1f%ad%x1f%s",
        ])
        commits = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                fields = line.split("\x1f", 2)
                if len(fields) == 3:
                    commits.append({"commit": fields[0], "committed_at": fields[1], "subject": _safe(fields[2], 360)})
        status = _git(path, ["status", "--porcelain", "--untracked-files=normal"])
        dirty_rows = status.stdout.splitlines() if status.returncode == 0 else []
        rows.append({
            "repo_id": _safe(repo_id, 120),
            "commit_count": len(commits),
            "commits": commits,
            "commits_truncated": len(commits) >= MAX_COMMITS,
            "dirty": bool(dirty_rows),
            "dirty_count": len(dirty_rows),
            "local_path_stored": False,
            "authority": "local-git",
        })
    return sorted(rows, key=lambda row: row["repo_id"]), {"registered_count": registered, "readable_count": len(rows)}


def build_facts(
    root: pathlib.Path,
    *,
    period: str,
    scope: str,
    as_of: dt.date,
    start: dt.date | None,
    end: dt.date | None,
    subject_id: str,
    project_id: str,
    codex_root: pathlib.Path,
    detail: str,
) -> Dict[str, Any]:
    if scope not in VALID_SCOPES:
        raise KnowledgeHubError("scope must be personal, project or portfolio")
    range_start, range_end = report_period(period, as_of, start, end)
    config = load_activity_config(root)
    effective_subject = subject_id or str(config.get("subject_id", ""))
    if scope == "personal" and not effective_subject:
        status = "needs-input"
        warnings = ["个人报告缺少显式 subject_id；请配置 local/activity-report.json v2 或传入 --subject-id。"]
    else:
        status = "pass"
        warnings = []
    items, item_coverage = collect_work_items(
        root, range_start, range_end,
        subject_id=effective_subject if scope == "personal" else "",
        project_id=project_id if scope == "project" else "",
    )
    if item_coverage["invalid_count"]:
        warnings.append("部分 v2 活动事项或回执未通过 schema、周期或隐私门禁，已跳过。")
    if scope == "personal":
        registry_rows: List[Dict[str, Any]] = []
        git_rows: List[Dict[str, Any]] = []
        git_coverage = {"registered_count": 0, "readable_count": 0, "not_collected": True}
        if not item_coverage["available"]:
            warnings.append("未发现 v2 事项或 session receipt；请先 capture 或启用 session-wrap v2 回执持久化。")
    else:
        registry_rows = collect_registry(root, range_start, range_end, project_id if scope == "project" else "")
        git_rows, git_coverage = collect_git(root, codex_root, range_start, range_end, project_id if scope == "project" else "")
        if git_coverage["readable_count"] < git_coverage["registered_count"]:
            warnings.append("部分登记仓库不可读；Git 覆盖不完整。")
    counts = Counter((item["status"], item["verification"]) for item in items)
    return {
        "schema_version": FACTS_SCHEMA_VERSION,
        "kind": "knowledge-hub.activity-facts-v2",
        "status": status,
        "period_kind": period,
        "scope": scope,
        "detail": detail,
        "timezone": TIMEZONE_NAME,
        "period": {"start": range_start.isoformat(), "end": range_end.isoformat()},
        "subject": {"id": effective_subject, "display_name": config.get("display_name", "")},
        "project_id": project_id,
        "summary": {
            "item_count": len(items),
            "done_verified": counts[("done", "verified")],
            "done_pending_verification": counts[("done", "reported")] + counts[("done", "missing")],
            "in_progress": sum(value for (state, _), value in counts.items() if state == "in_progress"),
            "blocked": sum(value for (state, _), value in counts.items() if state == "blocked"),
            "planned": sum(value for (state, _), value in counts.items() if state == "planned"),
            "registry_count": len(registry_rows),
            "git_repository_count": len(git_rows),
            "git_commit_count": sum(row["commit_count"] for row in git_rows),
        },
        "work_items": items,
        "registry_activity": registry_rows,
        "git_activity": git_rows,
        "source_coverage": {"work_items": item_coverage, "git": git_coverage, "config": config},
        "warnings": warnings,
        "privacy": {
            "raw_sessions_stored": False,
            "raw_logs_stored": False,
            "credentials_stored": False,
            "absolute_workspace_paths_stored": False,
            "identity_inferred_from_git": False,
            "memory_write": False,
            "external_write": False,
        },
    }


def _item_section(lines: List[str], title: str, items: Sequence[Mapping[str, Any]]) -> None:
    lines.extend(["## {}".format(title), ""])
    if not items:
        lines.extend(["- 无。", ""])
        return
    for item in items:
        project = " · {}".format(item["project_id"]) if item.get("project_id") else ""
        lines.append("### {}{}".format(item["title"], project))
        lines.append("")
        for outcome in item.get("outcomes", []):
            lines.append("- 产出：{}".format(outcome))
        for evidence in item.get("evidence_refs", []):
            lines.append("- 证据：{}".format(evidence))
        for blocker in item.get("blockers", []):
            lines.append("- 阻塞：{}".format(blocker))
        for action in item.get("next_actions", []):
            lines.append("- 下一步：{}".format(action))
        lines.append("")


def render_markdown(facts: Mapping[str, Any]) -> str:
    period = facts["period"]
    label = {"daily": "日报", "weekly": "周报", "custom": "周期报告"}[facts["period_kind"]]
    scope_label = {"personal": "个人工作", "project": "项目活动", "portfolio": "跨项目活动"}[facts["scope"]]
    summary = facts["summary"]
    lines = [
        "# {}{}".format(scope_label, label), "",
        "周期：{}—{} · 时区：{}".format(period["start"], period["end"], facts["timezone"]), "",
        "## 总览", "",
        "- 事项：{}；完成：{}；待验证：{}；推进中：{}；阻塞：{}；计划：{}".format(
            summary["item_count"], summary["done_verified"], summary["done_pending_verification"],
            summary["in_progress"], summary["blocked"], summary["planned"],
        ),
    ]
    if facts["scope"] == "personal":
        lines.append("- 报告人：{}".format(facts["subject"]["display_name"] or facts["subject"]["id"] or "未声明"))
    else:
        lines.append("- Hub 记录：{}；仓库：{}；提交：{}".format(
            summary["registry_count"], summary["git_repository_count"], summary["git_commit_count"]
        ))
    lines.append("")
    items = facts["work_items"]
    _item_section(lines, "已完成", [row for row in items if row["status"] == "done" and row["verification"] == "verified"])
    _item_section(lines, "已完成待验证", [row for row in items if row["status"] == "done" and row["verification"] != "verified"])
    _item_section(lines, "推进中", [row for row in items if row["status"] == "in_progress"])
    _item_section(lines, "阻塞与协同", [row for row in items if row["status"] == "blocked"])
    _item_section(lines, "后续计划", [row for row in items if row["status"] == "planned"])
    if facts["scope"] != "personal":
        lines.extend(["## Knowledge Hub 活动", ""])
        for row in facts["registry_activity"][:20]:
            lines.append("- [{}] {}：{}".format(row["status"], row["title"], row["summary_zh"]))
        if not facts["registry_activity"]:
            lines.append("- 无周期内 Hub 记录。")
        lines.extend(["", "## Git 活动", ""])
        for row in facts["git_activity"]:
            state = "dirty({})".format(row["dirty_count"]) if row["dirty"] else "clean"
            lines.append("- {}：{} commits · {}".format(row["repo_id"], row["commit_count"], state))
        if not facts["git_activity"]:
            lines.append("- 无可读仓库活动。")
        lines.append("")
    lines.extend(["## 数据覆盖", ""])
    if facts["warnings"]:
        for warning in facts["warnings"]:
            lines.append("- {}".format(warning))
    else:
        lines.append("- 未发现覆盖警告。")
    lines.extend([
        "- 仅接受 v2 事项和回执；不读取旧格式。",
        "- 未读取 raw session、日志、认证、密钥或 raw memory。",
        "- Git 不用于推断个人身份或事项完成状态。",
        "- 本报告为本地 report-only，不写 memory、不提升事实、不提交、不发布、不外发。",
        "",
    ])
    return "\n".join(lines)


def _atomic_write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".{}-".format(path.name), dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def report_stem(period: str, start: dt.date, end: dt.date) -> str:
    if period == "daily":
        return end.isoformat()
    if period == "weekly":
        year, week, _ = end.isocalendar()
        return "{}-W{:02d}-{}".format(year, week, end.isoformat())
    return "{}--{}".format(start.isoformat(), end.isoformat())


def generate_report(
    root: pathlib.Path,
    *,
    period: str,
    scope: str,
    as_of: dt.date,
    start: dt.date | None,
    end: dt.date | None,
    subject_id: str,
    project_id: str,
    codex_root: pathlib.Path,
    detail: str,
    output_root: pathlib.Path,
    write: bool,
) -> Dict[str, Any]:
    facts = build_facts(
        root, period=period, scope=scope, as_of=as_of, start=start, end=end,
        subject_id=subject_id, project_id=project_id, codex_root=codex_root, detail=detail,
    )
    facts["generated_at"] = dt.datetime.now(tz=report_timezone()).isoformat(timespec="seconds")
    markdown = render_markdown(facts)
    facts_text = pretty_json(facts) + "\n"
    range_start = dt.date.fromisoformat(facts["period"]["start"])
    range_end = dt.date.fromisoformat(facts["period"]["end"])
    stem = report_stem(period, range_start, range_end)
    report_path = output_root / "reports" / period / scope / "{}.md".format(stem)
    facts_path = output_root / "facts" / period / scope / "{}.json".format(stem)
    if write:
        _atomic_write(facts_path, facts_text)
        _atomic_write(report_path, markdown)
    return {
        "schema_version": FACTS_SCHEMA_VERSION,
        "status": facts["status"],
        "mode": "report-only",
        "period_kind": period,
        "scope": scope,
        "period": facts["period"],
        "written": write,
        "report_path": str(report_path) if write else "",
        "facts_path": str(facts_path) if write else "",
        "report_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "facts_sha256": hashlib.sha256(facts_text.encode("utf-8")).hexdigest(),
        "summary": facts["summary"],
        "source_coverage": facts["source_coverage"],
        "warnings": facts["warnings"],
        "privacy": facts["privacy"],
        "markdown": markdown if not write else "",
    }


def capture_item(root: pathlib.Path, input_path: pathlib.Path, *, apply: bool) -> Dict[str, Any]:
    payload = json.loads(read_utf8_bounded(input_path, 128 * 1024, "work item input"))
    if not isinstance(payload, dict):
        raise KnowledgeHubError("work item input must be an object")
    item = normalize_item(payload, source_kind="explicit-item", source_ref=input_path.stem)
    target = root / ".tmp/activity/items" / item["activity_date"] / "{}.json".format(item["item_id"])
    encoded = pretty_json(item) + "\n"
    if apply:
        _atomic_write(target, encoded)
    return {
        "schema_version": 2,
        "status": "pass",
        "applied": apply,
        "item_id": item["item_id"],
        "target": str(target) if apply else "",
        "sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "privacy": {"raw_content_stored": False, "external_write": False},
    }
