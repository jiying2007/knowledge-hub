"""Deterministic, report-only daily and weekly activity summaries."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import tempfile
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, file_sha256, load_json, load_jsonl, pretty_json, read_utf8_bounded
from .security import scan_secret_text


REPORT_SCHEMA_VERSION = 1
REPORT_TIMEZONE = "Asia/Hong_Kong"
MAX_TEXT_LENGTH = 360
MAX_COMMITS_PER_REPOSITORY = 50
MAX_MEMORY_CUES = 100
MAX_SESSION_RECEIPTS = 200
MAX_RECEIPT_ITEMS = 30
MEMORY_ALLOWED_ROOT_FILES = {"MEMORY.md", "memory_summary.md"}
MEMORY_ALLOWED_DIRECTORIES = {"projects", "rollout_summaries"}
MEMORY_EXCLUDED_NAMES = {"raw_memories.md"}
DATE_FIELDS = ("created_at", "updated_at", "captured_at", "ai_generated_at", "last_verified")
OPEN_MARKERS = ("待", "pending", "blocked", "阻塞", "风险", "未完成", "尚未")


def report_timezone() -> dt.tzinfo:
    """Return the fixed Hong Kong offset without requiring Python 3.9 zoneinfo."""
    return dt.timezone(dt.timedelta(hours=8), name=REPORT_TIMEZONE)


def report_period(kind: str, as_of: dt.date) -> Tuple[dt.date, dt.date]:
    if kind == "daily":
        return as_of, as_of
    if kind == "weekly":
        return as_of - dt.timedelta(days=as_of.weekday()), as_of
    raise KnowledgeHubError("activity report kind must be daily or weekly")


def _date_value(value: Any) -> dt.date | None:
    raw = str(value or "").strip()
    if len(raw) < 10:
        return None
    try:
        return dt.date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _within(value: Any, start: dt.date, end: dt.date) -> bool:
    parsed = _date_value(value)
    return bool(parsed and start <= parsed <= end)


def _safe_text(value: Any, maximum: int = MAX_TEXT_LENGTH) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if scan_secret_text(text):
        return "[已脱敏：检测到疑似凭证内容]"
    if len(text) <= maximum:
        return text
    return text[: maximum - 1].rstrip() + "…"


def _selected_dates(row: Mapping[str, Any], start: dt.date, end: dt.date) -> List[str]:
    dates = {
        parsed.isoformat()
        for field in DATE_FIELDS
        for parsed in [_date_value(row.get(field))]
        if parsed and start <= parsed <= end
    }
    return sorted(dates)


def collect_registry_activity(root: pathlib.Path, start: dt.date, end: dt.date) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for row in load_jsonl(root / "registry/items.jsonl"):
        dates = _selected_dates(row, start, end)
        if not dates:
            continue
        selected.append(
            {
                "id": _safe_text(row.get("id"), 160),
                "title": _safe_text(row.get("title")),
                "summary_zh": _safe_text(row.get("summary_zh"), 600),
                "domain": _safe_text(row.get("domain"), 160),
                "kind": _safe_text(row.get("kind"), 80),
                "status": _safe_text(row.get("status"), 80),
                "path": _safe_text(row.get("path"), 260),
                "activity_dates": dates,
                "manual_validation_pending": bool(row.get("manual_validation_pending", False)),
                "authority": "hub-registry",
            }
        )
    return sorted(selected, key=lambda row: (row["domain"], row["title"], row["id"]))


def _receipt_values(value: Any, *, hide_absolute_paths: bool = False) -> List[str]:
    if not isinstance(value, list):
        return []
    selected: List[str] = []
    for item in value[:MAX_RECEIPT_ITEMS]:
        text = _safe_text(item)
        if hide_absolute_paths and (text.startswith(("/", "~/")) or re.match(r"^[A-Za-z]:[\\/]", text)):
            text = "[本地工件路径已省略]"
        selected.append(text)
    return selected


def collect_session_receipts(
    root: pathlib.Path, start: dt.date, end: dt.date
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    receipt_root = root / ".tmp/session-receipts"
    if not receipt_root.is_dir():
        return [], {"available": False, "valid_count": 0, "invalid_count": 0, "truncated": False}
    selected: List[Dict[str, Any]] = []
    invalid_count = 0
    for path in sorted(receipt_root.rglob("*.json")):
        relative_parts = path.relative_to(receipt_root).parts
        if path.is_symlink() or not path.is_file() or any(part.startswith(".") for part in relative_parts):
            continue
        try:
            payload = json.loads(read_utf8_bounded(path, 256 * 1024, "session receipt"))
        except (KnowledgeHubError, json.JSONDecodeError, OSError):
            invalid_count += 1
            continue
        activity_date = _date_value(payload.get("period_date")) if isinstance(payload, dict) else None
        completion_status = str(payload.get("completion_status", "")) if isinstance(payload, dict) else ""
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != 1
            or payload.get("kind") != "codex-session-receipt"
            or payload.get("raw_content_stored") is not False
            or completion_status not in {"complete", "partial", "blocked"}
            or not activity_date
            or not start <= activity_date <= end
        ):
            invalid_count += 1
            continue
        selected.append(
            {
                "receipt_id": _safe_text(path.stem, 160),
                "project": _safe_text(payload.get("project"), 160),
                "period_date": activity_date.isoformat(),
                "goal": _safe_text(payload.get("goal"), 600),
                "outcomes": _receipt_values(payload.get("outcomes")),
                "validation": _receipt_values(payload.get("validation")),
                "risks": _receipt_values(payload.get("risks")),
                "next_actions": _receipt_values(payload.get("next_actions")),
                "artifacts": _receipt_values(payload.get("artifacts"), hide_absolute_paths=True),
                "completion_status": completion_status,
                "sha256": file_sha256(path),
                "authority": "codex-session-receipt",
                "raw_content_stored": False,
            }
        )
        if len(selected) >= MAX_SESSION_RECEIPTS:
            break
    metadata = {
        "available": True,
        "valid_count": len(selected),
        "invalid_count": invalid_count,
        "truncated": len(selected) >= MAX_SESSION_RECEIPTS,
    }
    return sorted(selected, key=lambda row: (row["project"], row["period_date"], row["receipt_id"])), metadata


def _git(repo: pathlib.Path, arguments: Sequence[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.update({"GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C.UTF-8"})
    command = ["git", "-C", str(repo), *arguments]
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, "", "git command timed out")
    except OSError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))


def _repository_candidates(root: pathlib.Path, codex_root: pathlib.Path) -> Tuple[List[Tuple[str, pathlib.Path]], int]:
    candidates: List[Tuple[str, pathlib.Path]] = [("knowledge-hub", root), ("codex", codex_root)]
    local = load_json(root / "local/workspaces.json", {}) or {}
    workspace_rows = local.get("workspaces", []) if isinstance(local, dict) else []
    report_local = load_json(root / "local/activity-report.json", {}) or {}
    explicit_rows = report_local.get("repositories", []) if isinstance(report_local, dict) else []
    for row in workspace_rows:
        if not isinstance(row, dict) or not row.get("present"):
            continue
        candidates.append((str(row.get("repo_id", "workspace")), pathlib.Path(str(row.get("path", "")))))
    for row in explicit_rows:
        if not isinstance(row, dict) or row.get("enabled") is False:
            continue
        candidates.append((str(row.get("repo_id", "local")), pathlib.Path(str(row.get("path", "")))))
    unique: Dict[str, Tuple[str, pathlib.Path]] = {}
    for repo_id, path in candidates:
        resolved = path.expanduser().resolve(strict=False)
        unique.setdefault(str(resolved), (repo_id, resolved))
    return list(unique.values()), len(unique)


def _git_commits(repo: pathlib.Path, start: dt.date, end: dt.date) -> List[Dict[str, str]]:
    until = end + dt.timedelta(days=1)
    result = _git(
        repo,
        [
            "log",
            "--since={}T00:00:00+08:00".format(start.isoformat()),
            "--until={}T00:00:00+08:00".format(until.isoformat()),
            "--max-count={}".format(MAX_COMMITS_PER_REPOSITORY),
            "--date=iso-strict",
            "--pretty=format:%H%x1f%ad%x1f%s",
        ],
    )
    if result.returncode != 0:
        return []
    commits: List[Dict[str, str]] = []
    for line in result.stdout.splitlines():
        fields = line.split("\x1f", 2)
        if len(fields) != 3:
            continue
        commits.append({"commit": fields[0], "committed_at": fields[1], "subject": _safe_text(fields[2])})
    return commits


def _git_state(repo: pathlib.Path) -> Dict[str, Any]:
    head = _git(repo, ["rev-parse", "HEAD"])
    branch = _git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    status = _git(repo, ["status", "--porcelain", "--untracked-files=normal"])
    dirty_rows = status.stdout.splitlines() if status.returncode == 0 else []
    return {
        "head": head.stdout.strip() if head.returncode == 0 else "",
        "branch": _safe_text(branch.stdout.strip(), 120) if branch.returncode == 0 else "",
        "dirty": bool(dirty_rows),
        "dirty_count": len(dirty_rows),
    }


def collect_git_activity(
    root: pathlib.Path, codex_root: pathlib.Path, start: dt.date, end: dt.date
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    repositories: List[Dict[str, Any]] = []
    candidates, registered_count = _repository_candidates(root, codex_root)
    for repo_id, path in candidates:
        if not path.is_dir() or not (path / ".git").exists():
            continue
        commits = _git_commits(path, start, end)
        state = _git_state(path)
        repositories.append(
            {
                "repo_id": _safe_text(repo_id, 120),
                **state,
                "commit_count": len(commits),
                "commits_truncated": len(commits) >= MAX_COMMITS_PER_REPOSITORY,
                "commits": commits,
                "local_path_stored": False,
                "authority": "local-git",
            }
        )
    coverage = {"registered_or_core_count": registered_count, "readable_git_count": len(repositories)}
    return sorted(repositories, key=lambda row: row["repo_id"]), coverage


def _memory_file_date(path: pathlib.Path, timezone: dt.tzinfo) -> dt.date:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", path.name)
    parsed = _date_value(match.group(1) if match else "")
    if parsed:
        return parsed
    return dt.datetime.fromtimestamp(path.stat().st_mtime, tz=timezone).date()


def _memory_files(memory_root: pathlib.Path) -> Iterable[pathlib.Path]:
    for name in sorted(MEMORY_ALLOWED_ROOT_FILES):
        candidate = memory_root / name
        if candidate.is_file() and not candidate.is_symlink():
            yield candidate
    for directory in sorted(MEMORY_ALLOWED_DIRECTORIES):
        base = memory_root / directory
        if not base.is_dir():
            continue
        for candidate in sorted(base.rglob("*.md")):
            relative_parts = candidate.relative_to(memory_root).parts
            if candidate.is_file() and not candidate.is_symlink() and not any(
                part.startswith(".") for part in relative_parts
            ):
                yield candidate


def _memory_title(path: pathlib.Path) -> str:
    text = read_utf8_bounded(path, 256 * 1024, "memory summary")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return _safe_text(stripped[2:])
    return _safe_text(path.stem.replace("_", " ").replace("-", " "))


def _project_memory_matches(path: pathlib.Path, active_keys: Sequence[str]) -> bool:
    if path.parent.name != "projects":
        return False
    normalized = re.sub(r"[^a-z0-9]+", "-", path.stem.casefold()).strip("-")
    return any(normalized and (normalized in key or key in normalized) for key in active_keys)


def collect_memory_cues(
    memory_root: pathlib.Path,
    start: dt.date,
    end: dt.date,
    active_keys: Sequence[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    if not memory_root.is_dir():
        return [], {"available": False, "excluded_raw_memory": True}
    timezone = report_timezone()
    cues: List[Dict[str, Any]] = []
    for path in _memory_files(memory_root):
        if path.name in MEMORY_EXCLUDED_NAMES:
            continue
        activity_date = _memory_file_date(path, timezone)
        in_period = start <= activity_date <= end
        context_match = _project_memory_matches(path, active_keys)
        if not in_period and not context_match:
            continue
        cues.append(
            {
                "path": path.relative_to(memory_root).as_posix(),
                "title": _memory_title(path),
                "activity_date": activity_date.isoformat() if in_period else "",
                "activity_signal": in_period,
                "context_only": not in_period,
                "sha256": file_sha256(path),
                "authority": "auxiliary-memory-only",
                "raw_content_stored": False,
            }
        )
        if len(cues) >= MAX_MEMORY_CUES:
            break
    metadata = {
        "available": True,
        "excluded_raw_memory": True,
        "excluded_sessions_logs_cache": True,
        "truncated": len(cues) >= MAX_MEMORY_CUES,
    }
    return cues, metadata


def _active_keys(
    registry_rows: Sequence[Mapping[str, Any]],
    git_rows: Sequence[Mapping[str, Any]],
    receipt_rows: Sequence[Mapping[str, Any]],
) -> List[str]:
    values: List[str] = []
    for row in registry_rows:
        domain = str(row.get("domain", ""))
        values.extend([domain, domain.rsplit("/", 1)[-1]])
    values.extend(str(row.get("repo_id", "")) for row in git_rows if row.get("commit_count"))
    values.extend(str(row.get("project", "")) for row in receipt_rows)
    return sorted({re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") for value in values if value})


def build_activity_facts(
    root: pathlib.Path,
    kind: str,
    as_of: dt.date,
    codex_root: pathlib.Path,
    memory_root: pathlib.Path,
) -> Dict[str, Any]:
    start, end = report_period(kind, as_of)
    registry_rows = collect_registry_activity(root, start, end)
    git_rows, git_coverage = collect_git_activity(root, codex_root, start, end)
    receipt_rows, receipt_metadata = collect_session_receipts(root, start, end)
    memory_rows, memory_metadata = collect_memory_cues(
        memory_root, start, end, _active_keys(registry_rows, git_rows, receipt_rows)
    )
    status_counts = Counter(row["status"] for row in registry_rows)
    commits = sum(int(row["commit_count"]) for row in git_rows)
    warnings = _coverage_warnings(git_coverage, registry_rows, receipt_metadata, memory_metadata)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_kind": kind,
        "timezone": REPORT_TIMEZONE,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "authority_order": [
            "hub-registry",
            "codex-session-receipt",
            "local-git",
            "codex-archive-provenance",
            "auxiliary-memory-only",
        ],
        "summary": {
            "registry_item_count": len(registry_rows),
            "git_repository_count": len(git_rows),
            "git_commit_count": commits,
            "session_receipt_count": len(receipt_rows),
            "memory_cue_count": len(memory_rows),
            "registry_status_counts": dict(sorted(status_counts.items())),
        },
        "registry_activity": registry_rows,
        "git_activity": git_rows,
        "session_receipts": receipt_rows,
        "memory_cues": memory_rows,
        "source_coverage": {"git": git_coverage, "session_receipts": receipt_metadata, "memory": memory_metadata},
        "privacy": {
            "raw_sessions_stored": False,
            "raw_logs_stored": False,
            "raw_memory_stored": False,
            "credentials_stored": False,
            "absolute_workspace_paths_stored": False,
            "memory_write": False,
            "external_write": False,
        },
        "warnings": warnings,
    }


def _coverage_warnings(
    git_coverage: Mapping[str, int],
    registry_rows: Sequence[Mapping[str, Any]],
    receipt_metadata: Mapping[str, Any],
    memory_metadata: Mapping[str, Any],
) -> List[str]:
    warnings: List[str] = []
    if git_coverage.get("readable_git_count", 0) < git_coverage.get("registered_or_core_count", 0):
        warnings.append("部分登记工作区当前不可读；报告保留 Hub 记录，但 Git 活动覆盖不完整。")
    if not registry_rows:
        warnings.append("本周期没有命中 Hub registry 新增或更新记录。")
    if receipt_metadata.get("invalid_count", 0):
        warnings.append("部分 Codex session receipt 未通过 schema、周期或隐私门禁，已跳过。")
    if not memory_metadata.get("available"):
        warnings.append("Codex memory 目录不可用；报告未包含辅助 memory cue。")
    return warnings


def _render_registry(lines: List[str], rows: Sequence[Mapping[str, Any]]) -> None:
    lines.extend(["## Knowledge Hub 与项目记录", ""])
    if not rows:
        lines.extend(["- 本周期无登记项。", ""])
        return
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("domain", "未分类"))].append(row)
    for domain, items in sorted(grouped.items()):
        lines.extend(["### {}".format(domain), ""])
        for row in items:
            summary = str(row.get("summary_zh") or "无摘要")
            pending = "；人工/外部验证待完成" if row.get("manual_validation_pending") else ""
            lines.append("- [{}] {}：{}{}".format(row.get("status", ""), row.get("title", ""), summary, pending))
        lines.append("")


def _render_git(lines: List[str], rows: Sequence[Mapping[str, Any]]) -> None:
    lines.extend(["## Git 活动", ""])
    active = [row for row in rows if row.get("commit_count") or row.get("dirty")]
    if not active:
        lines.extend(["- 本周期未发现提交或工作树变化。", ""])
        return
    for row in active:
        state = "dirty({})".format(row.get("dirty_count", 0)) if row.get("dirty") else "clean"
        lines.append("### {} · {} commits · {}".format(row.get("repo_id"), row.get("commit_count"), state))
        lines.append("")
        for commit in row.get("commits", []):
            lines.append(
                "- `{}` {}".format(str(commit.get("commit", ""))[:8], commit.get("subject", ""))
            )
        if row.get("commits_truncated"):
            lines.append("- 提交列表已达到单仓上限，事实包标记为 truncated。")
        lines.append("")


def _render_session_receipts(lines: List[str], rows: Sequence[Mapping[str, Any]]) -> None:
    lines.extend(["## Codex session 收口回执", ""])
    if not rows:
        lines.extend(["- 本周期没有可用的结构化 session receipt。", ""])
        return
    for row in rows:
        lines.append("### {} · {} · {}".format(row.get("project") or "未分类", row.get("period_date"), row.get("completion_status")))
        lines.append("")
        if row.get("goal"):
            lines.append("- 目标：{}".format(row.get("goal")))
        for value in row.get("outcomes", []):
            lines.append("- 结果：{}".format(value))
        for value in row.get("validation", []):
            lines.append("- 验证：{}".format(value))
        for value in row.get("risks", []):
            lines.append("- 风险：{}".format(value))
        for value in row.get("next_actions", []):
            lines.append("- 下一步：{}".format(value))
        lines.append("")


def _render_memory(lines: List[str], rows: Sequence[Mapping[str, Any]]) -> None:
    lines.extend(["## Codex memory 辅助上下文", ""])
    if not rows:
        lines.extend(["- 本周期没有可用的受控 memory cue。", ""])
        return
    for row in rows:
        marker = "活动线索" if row.get("activity_signal") else "历史上下文"
        lines.append("- [{}] {}（`{}`）".format(marker, row.get("title", ""), row.get("path", "")))
    lines.extend(["", "> memory 只用于辅助召回，不高于 Hub 当前事实，也不单独证明工作已完成。", ""])


def _render_open_items(lines: List[str], facts: Mapping[str, Any]) -> None:
    candidates: List[str] = []
    for row in facts.get("registry_activity", []):
        text = "{}：{}".format(row.get("title", ""), row.get("summary_zh", ""))
        if row.get("status") in {"draft", "reviewing", "personal"} or any(marker in text.casefold() for marker in OPEN_MARKERS):
            candidates.append(text)
    dirty = [row.get("repo_id", "") for row in facts.get("git_activity", []) if row.get("dirty")]
    lines.extend(["## 风险与待办", ""])
    for value in candidates[:20]:
        lines.append("- {}".format(value))
    if len(candidates) > 20:
        lines.append("- 其余 {} 项请查看 JSON 事实包。".format(len(candidates) - 20))
    if dirty:
        lines.append("- 存在 dirty 工作树：{}；不据此声明 clean delivery。".format("、".join(sorted(dirty))))
    if not candidates and not dirty:
        lines.append("- 未从受控来源提取到显式待办；仍需人工复核报告完整性。")
    lines.append("")


def render_activity_markdown(facts: Mapping[str, Any]) -> str:
    period = facts["period"]
    label = "日报" if facts["report_kind"] == "daily" else "周报"
    summary = facts["summary"]
    lines = [
        "# 自动{}（{}—{}）".format(label, period["start"], period["end"]),
        "",
        "## 摘要",
        "",
        "- Hub 新增/更新记录：{}".format(summary["registry_item_count"]),
        "- 可读 Git 仓库：{}；本周期提交：{}".format(summary["git_repository_count"], summary["git_commit_count"]),
        "- Codex session receipt：{}".format(summary["session_receipt_count"]),
        "- Codex memory cue：{}".format(summary["memory_cue_count"]),
        "- Registry 状态：{}".format(json.dumps(summary["registry_status_counts"], ensure_ascii=False)),
        "",
    ]
    _render_registry(lines, facts["registry_activity"])
    _render_session_receipts(lines, facts["session_receipts"])
    _render_git(lines, facts["git_activity"])
    _render_memory(lines, facts["memory_cues"])
    _render_open_items(lines, facts)
    lines.extend(["## 数据边界", ""])
    for warning in facts.get("warnings", []):
        lines.append("- {}".format(warning))
    lines.extend(
        [
            "- 未读取或保存 raw session、raw log、cache、auth、secret 或 `raw_memories.md`。",
            "- 本报告为 report-only，不自动归档、提交、推送、提升 active、写 memory 或外发。",
            "- 完成与发布结论必须以对应 validation、Git、设备或发布证据为准。",
            "",
        ]
    )
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


def _output_stem(kind: str, as_of: dt.date) -> str:
    if kind == "daily":
        return as_of.isoformat()
    year, week, _ = as_of.isocalendar()
    return "{}-W{:02d}-{}".format(year, week, as_of.isoformat())


def generate_activity_report(
    root: pathlib.Path,
    kind: str,
    as_of: dt.date,
    codex_root: pathlib.Path,
    memory_root: pathlib.Path,
    output_dir: pathlib.Path,
    write: bool = True,
) -> Dict[str, Any]:
    facts = build_activity_facts(root, kind, as_of, codex_root, memory_root)
    timezone = report_timezone()
    generated_at = dt.datetime.now(tz=timezone).isoformat(timespec="seconds")
    facts["generated_at"] = generated_at
    markdown = render_activity_markdown(facts)
    encoded_facts = pretty_json(facts) + "\n"
    stem = _output_stem(kind, as_of)
    report_dir = output_dir.expanduser().resolve(strict=False) / kind
    markdown_path = report_dir / "{}.md".format(stem)
    facts_path = report_dir / "{}.json".format(stem)
    if write:
        _atomic_write(facts_path, encoded_facts)
        _atomic_write(markdown_path, markdown)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "pass",
        "mode": "report-only",
        "report_kind": kind,
        "period": facts["period"],
        "generated_at": generated_at,
        "written": write,
        "report_path": str(markdown_path) if write else "",
        "facts_path": str(facts_path) if write else "",
        "report_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "facts_sha256": hashlib.sha256(encoded_facts.encode("utf-8")).hexdigest(),
        "summary": facts["summary"],
        "source_coverage": facts["source_coverage"],
        "warnings": facts["warnings"],
        "privacy": facts["privacy"],
        "markdown": markdown if not write else "",
    }
