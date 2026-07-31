"""Read-only project-session discovery for reusable tool asset candidates."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
import tempfile
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import yaml

from .common import KnowledgeHubError, file_sha256, load_json, read_utf8_bounded, run_rtk, slugify
from .search_ranking import redact_internal_endpoints
from .security import scan_secret_text
from .tool_asset_import_cli import SCHEMA, VALIDATION_RESULTS


SCAN_PREFIXES = ("codex_assets/", "tools/", "scripts/")
TEXT_SUFFIXES = {".py", ".sh", ".bash", ".pl", ".rb", ".js", ".ts"}
EXCLUDED_PARTS = {".git", ".codex", ".tmp", "tmp", "build", "dist", "logs", "core", "cores"}
MAX_SOURCE_BYTES = 1024 * 1024
FLAG_RE = re.compile(r"(?<![A-Za-z0-9])--[a-z0-9][a-z0-9-]{0,63}")


def _git(repo: pathlib.Path, args: Sequence[str], accepted: Sequence[int] = (0,)) -> Dict[str, Any]:
    return run_rtk(repo, ["git", "-c", "core.quotePath=false", *args], timeout=30, accepted_exit_codes=accepted)


def _changed_paths(repo: pathlib.Path) -> List[str]:
    result = _git(repo, ["status", "--porcelain=v1", "--untracked-files=all"])
    paths = []
    for line in result["stdout"].splitlines():
        if len(line) < 4:
            continue
        value = line[3:].strip()
        if " -> " in value:
            value = value.rsplit(" -> ", 1)[1]
        if value:
            paths.append(value)
    return sorted(set(paths))


def _repository_identity(hub_root: pathlib.Path, repo: pathlib.Path, requested: str) -> Dict[str, Any]:
    registry = load_json(hub_root / "registry/repositories.json", {}) or {}
    rows = [row for row in registry.get("repositories", []) if isinstance(row, dict) and row.get("status") == "registered"]
    if requested:
        matches = [row for row in rows if requested in _row_identities(row)]
    else:
        remote = _git(repo, ["remote", "get-url", "origin"], accepted=(0, 2, 128))
        remote_url = remote["stdout"].strip() if remote["exit_code"] == 0 else ""
        matches = [row for row in rows if _remote_matches(remote_url, row)]
    if len(matches) != 1:
        raise KnowledgeHubError("source repository cannot be uniquely routed; provide --source-repo <registered-id>")
    return dict(matches[0])


def _row_identities(row: Mapping[str, Any]) -> set[str]:
    values = {str(row.get("repo_id", "")), str(row.get("remote_key", ""))}
    values.update(str(value) for value in row.get("aliases", []) if isinstance(value, str))
    return {value for value in values if value}


def _remote_matches(remote_url: str, row: Mapping[str, Any]) -> bool:
    normalized = remote_url.rstrip("/").removesuffix(".git").replace(":", "/")
    return any(normalized.endswith(value.rstrip("/").removesuffix(".git")) for value in _row_identities(row))


def _is_candidate_path(relative: str) -> bool:
    path = pathlib.PurePosixPath(relative)
    if not relative.startswith(SCAN_PREFIXES) or path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    return not any(part.lower() in EXCLUDED_PARTS for part in path.parts)


def _tracked_test_paths(repo: pathlib.Path) -> List[str]:
    result = _git(repo, ["ls-files", "--", "tests", "test"], accepted=(0,))
    return [line.strip() for line in result["stdout"].splitlines() if line.strip()]


def _score(relative: str, text: str, test_paths: Sequence[str], validation: Mapping[str, str]) -> Tuple[int, List[str]]:
    score = 20 if relative.startswith("codex_assets/") else 15
    reasons = ["governed-source-prefix"]
    score += 10
    reasons.append("supported-text-tool")
    if text.startswith("#!"):
        score += 10
        reasons.append("executable-entry")
    if "--help" in text or "ArgumentParser" in text or "click.command" in text:
        score += 10
        reasons.append("cli-help-surface")
    if "--dry-run" in text or "dry_run" in text:
        score += 10
        reasons.append("dry-run-surface")
    stem = pathlib.PurePosixPath(relative).stem.replace("-", "_")
    if any(stem in path.replace("-", "_") for path in test_paths):
        score += 15
        reasons.append("tracked-test-reference")
    if '"""' in text[:2000] or "'''" in text[:2000] or "# " in text[:500]:
        score += 5
        reasons.append("inline-documentation")
    passed = sum(1 for value in validation.values() if value == "pass")
    score += passed * 5
    if passed:
        reasons.append("explicit-validation-pass:{}".format(passed))
    return min(score, 100), reasons


def _capability_signature(relative: str, text: str, test_paths: Sequence[str]) -> Tuple[str, Dict[str, Any]]:
    suffix = pathlib.PurePosixPath(relative).suffix.lower()
    flags = sorted(set(FLAG_RE.findall(text)))[:64]
    stem = pathlib.PurePosixPath(relative).stem.replace("-", "_")
    payload = {
        "schema": "tool-asset-capability.v1",
        "language": suffix.lstrip("."),
        "cli_help": "--help" in text or "ArgumentParser" in text or "click.command" in text,
        "dry_run": "--dry-run" in text or "dry_run" in text,
        "json_output": "json.dumps" in text or "--json" in text,
        "local_file_write": any(marker in text for marker in ("write_text(", "open(", "os.replace(")),
        "subprocess": "subprocess" in text or "run_rtk(" in text,
        "network": any(marker in text for marker in ("requests.", "urllib", "http://", "https://")),
        "tracked_test": len(stem) >= 5 and any(stem in path.replace("-", "_") for path in test_paths),
        "argument_flags": flags,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), payload


def _inspect_file(repo: pathlib.Path, relative: str, test_paths: Sequence[str], validation: Mapping[str, str]) -> Dict[str, Any]:
    path = repo / relative
    try:
        info = path.lstat()
    except OSError:
        return {"path": relative, "eligible": False, "reason": "missing-or-unreadable"}
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_size > MAX_SOURCE_BYTES:
        return {"path": relative, "eligible": False, "reason": "not-regular-or-too-large"}
    try:
        text = read_utf8_bounded(path, MAX_SOURCE_BYTES, "tool candidate source")
    except (KnowledgeHubError, UnicodeError):
        return {"path": relative, "eligible": False, "reason": "not-safe-utf8-text"}
    findings = scan_secret_text(text)
    _, has_endpoint = redact_internal_endpoints(text)
    if findings or has_endpoint:
        return {
            "path": relative,
            "eligible": False,
            "reason": "sanitization-failed",
            "secret_rules": sorted({str(row.get("rule", "unknown")) for row in findings}),
            "private_endpoint_found": has_endpoint,
        }
    score, reasons = _score(relative, text, test_paths, validation)
    capability_signature, capability = _capability_signature(relative, text, test_paths)
    return {
        "path": relative,
        "eligible": True,
        "score": score,
        "score_reasons": reasons,
        "sha256": file_sha256(path),
        "size": info.st_size,
        "capability_signature": capability_signature,
        "capability": capability,
    }


def _safe_output(repo: pathlib.Path, requested: pathlib.Path) -> pathlib.Path:
    output = requested.expanduser().resolve(strict=False)
    if output.suffix.lower() != ".md":
        raise KnowledgeHubError("--hub-candidate-out must be a Markdown path")
    system_tmp = pathlib.Path(tempfile.gettempdir()).resolve()
    try:
        output.relative_to(system_tmp)
        return output
    except ValueError:
        pass
    try:
        relative = output.relative_to(repo)
    except ValueError as exc:
        raise KnowledgeHubError("candidate output must live under system /tmp or repository tmp/.tmp") from exc
    if not relative.parts or relative.parts[0] not in {"tmp", ".tmp"}:
        raise KnowledgeHubError("repository-local candidate output must live under tmp/ or .tmp/")
    return output


def _write_candidate(output: pathlib.Path, metadata: Mapping[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink() or output.parent.is_symlink():
        raise KnowledgeHubError("candidate output path must not be a symlink")
    frontmatter = yaml.safe_dump(dict(metadata), allow_unicode=True, sort_keys=False).rstrip()
    body = "# 工具资产候选\n\n此文件由项目会话扫描器机械生成；Hub 只持久化白名单治理字段，不复制项目源码或会话原文。\n"
    content = "---\n{}\n---\n\n{}".format(frontmatter, body)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tool-candidate-", dir=str(output.parent))
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(output))
    finally:
        if temporary.exists():
            temporary.unlink()


def _candidate_metadata(
    repository: Mapping[str, Any], head: str, selected: Mapping[str, Any], validation: Mapping[str, str]
) -> Dict[str, Any]:
    relative = str(selected["path"])
    return {
        "schema": SCHEMA,
        "source_repo": str(repository["repo_id"]),
        "source_commit": head,
        "source_worktree_dirty": True,
        "source_identity_verified": True,
        "candidate_name": slugify(pathlib.PurePosixPath(relative).stem),
        "candidate_source_path": relative,
        "candidate_sha256": str(selected["sha256"]),
        "candidate_hash_scope": "single-file",
        "candidate_file_count": 1,
        "candidate_score": int(selected["score"]),
        "recommendation": "recommend-promote" if int(selected["score"]) >= 80 else "keep-project-tool",
        "recommended_target": "人工评审项目工具、项目 skill 或全局 Codex 候选归属",
        "validation": dict(validation),
        "sanitization": {"endpoint_removed": True, "credentials_found": False, "raw_logs_archived": False},
        "status": "reviewing",
        "summary_zh": "项目会话发现可复用工具候选 `{}`，等待人工复核维护归属和兼容边界。".format(relative),
        "risks_zh": "候选来自 dirty worktree；source_commit 绑定基线 HEAD，candidate_sha256 绑定当前文件内容。",
        "blockers_zh": "需要人工确认验证证据和 promotion 目标。",
    }


def scan_tool_assets(
    hub_root: pathlib.Path,
    repo_root: pathlib.Path,
    output: pathlib.Path,
    validation: Mapping[str, str],
    source_repo: str = "",
    minimum_score: int = 50,
    session_paths: Sequence[str] = (),
    session_paths_must_be_changed: bool = True,
) -> Dict[str, Any]:
    repo = repo_root.expanduser().resolve()
    if not (repo / ".git").exists():
        raise KnowledgeHubError("--repo-root must be a Git repository")
    if not 0 <= minimum_score <= 100:
        raise KnowledgeHubError("--minimum-score must be between 0 and 100")
    for field, value in validation.items():
        if value not in VALIDATION_RESULTS:
            raise KnowledgeHubError("{} must be one of {}".format(field, ", ".join(sorted(VALIDATION_RESULTS))))
    repository = _repository_identity(hub_root, repo, source_repo)
    head_result = _git(repo, ["rev-parse", "HEAD"])
    head = head_result["stdout"].strip()
    test_paths = _tracked_test_paths(repo)
    changed_paths = _changed_paths(repo)
    requested_paths = {str(pathlib.PurePosixPath(value)) for value in session_paths if value}
    if requested_paths:
        known_scope = set(changed_paths) if session_paths_must_be_changed else {
            path for path in requested_paths if (repo / path).is_file()
        }
        unknown = sorted(requested_paths.difference(known_scope))
        if unknown:
            raise KnowledgeHubError("--session-path is not available in the requested session scope: {}".format(", ".join(unknown)))
        scan_paths = sorted(requested_paths)
    else:
        scan_paths = changed_paths
    inspected = [
        _inspect_file(repo, relative, test_paths, validation)
        for relative in scan_paths
        if _is_candidate_path(relative)
    ]
    eligible = [row for row in inspected if row.get("eligible") and int(row.get("score", 0)) >= minimum_score]
    eligible.sort(key=lambda row: (-int(row["score"]), str(row["path"])))
    result: Dict[str, Any] = {
        "status": "pass",
        "mode": "project-session-tool-asset-scan",
        "read_only_source": True,
        "repo_root": str(repo),
        "source_repo": repository["repo_id"],
        "source_commit": head,
        "source_worktree_dirty": bool(changed_paths),
        "scope_mode": "explicit-session-paths" if requested_paths else "all-dirty-paths",
        "session_paths": sorted(requested_paths),
        "inspected_count": len(inspected),
        "eligible_count": len(eligible),
        "inspected": inspected,
        "hub_candidate_generated": False,
        "archive_conclusion": "本次无可归档工具资产",
    }
    if not eligible:
        return result
    target = _safe_output(repo, output)
    metadata = _candidate_metadata(repository, head, eligible[0], validation)
    _write_candidate(target, metadata)
    result.update(
        {
            "hub_candidate_generated": True,
            "archive_conclusion": "已生成 reviewing 工具资产候选",
            "selected": eligible[0],
            "candidate_output": str(target),
            "candidate_metadata": metadata,
        }
    )
    return result
