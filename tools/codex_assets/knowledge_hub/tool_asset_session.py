"""Cross-session observation and aggregation for project tool assets."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import stat
import tempfile
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import (
    KnowledgeHubError,
    compact_json,
    ensure_private_directory,
    file_sha256,
    load_markdown,
    read_utf8_bounded,
    render_markdown,
    utc_timestamp,
)
from .tool_asset_scan import (
    _git,
    _is_candidate_path,
    _repository_identity,
    scan_tool_assets,
)


SESSION_SCHEMA = "tool-asset-session-baseline.v1"
OBSERVATION_SCHEMA = "tool-asset-observation.v1"
MAX_STATE_BYTES = 8 * 1024 * 1024
MAX_LEDGER_BYTES = 64 * 1024 * 1024


def _safe_runtime_path(
    hub_root: pathlib.Path, repo: pathlib.Path, requested: pathlib.Path, suffixes: Sequence[str]
) -> pathlib.Path:
    path = requested.expanduser().resolve(strict=False)
    if path.suffix.lower() not in suffixes:
        raise KnowledgeHubError("runtime output has an unsupported suffix: {}".format(path.suffix))
    system_tmp = pathlib.Path(tempfile.gettempdir()).resolve()
    allowed_roots = (system_tmp, repo / "tmp", repo / ".tmp", hub_root / ".cache" / "knowledge-hub")
    for root in allowed_roots:
        try:
            path.relative_to(root.resolve(strict=False))
            return path
        except ValueError:
            continue
    raise KnowledgeHubError("runtime state must live under project tmp/.tmp, Hub .cache, or system /tmp")


def _atomic_text(path: pathlib.Path, content: str) -> None:
    if path.exists() and path.is_symlink():
        raise KnowledgeHubError("runtime state path must not be a symlink")
    system_tmp = pathlib.Path(tempfile.gettempdir()).resolve()
    if path.parent.resolve(strict=False) == system_tmp:
        if path.parent.is_symlink() or not path.parent.is_dir():
            raise KnowledgeHubError("system temporary directory is not a real directory")
    else:
        ensure_private_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tool-session-", dir=str(path.parent))
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            os.chmod(stream.fileno(), 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(path))
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def _candidate_files(repo: pathlib.Path) -> List[str]:
    result = _git(repo, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    return sorted({value for value in result["stdout"].split("\0") if value and _is_candidate_path(value)})


def _snapshot(repo: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for relative in _candidate_files(repo):
        path = repo / relative
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode):
            rows[relative] = {"sha256": file_sha256(path), "size": info.st_size}
    return rows


def _load_json(path: pathlib.Path, maximum: int, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(read_utf8_bounded(path, maximum, label))
    except json.JSONDecodeError as exc:
        raise KnowledgeHubError("invalid {} JSON".format(label)) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("{} must be a JSON object".format(label))
    return payload


def start_tool_asset_session(
    hub_root: pathlib.Path,
    repo_root: pathlib.Path,
    state_out: pathlib.Path,
    source_repo: str = "",
    session_id: str = "",
) -> Dict[str, Any]:
    repo = repo_root.expanduser().resolve()
    if not (repo / ".git").exists():
        raise KnowledgeHubError("--repo-root must be a Git repository")
    repository = _repository_identity(hub_root, repo, source_repo)
    head = _git(repo, ["rev-parse", "HEAD"])["stdout"].strip()
    state_path = _safe_runtime_path(hub_root, repo, state_out, (".json",))
    payload = {
        "schema": SESSION_SCHEMA,
        "session_id": session_id or uuid.uuid4().hex,
        "repo_id": repository["repo_id"],
        "project_id": repository["project_id"],
        "source_commit": head,
        "started_at": utc_timestamp(),
        "files": _snapshot(repo),
        "privacy": {
            "raw_session_stored": False,
            "command_arguments_stored": False,
            "environment_stored": False,
        },
    }
    _atomic_text(state_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return {
        "status": "pass",
        "mode": "tool-asset-session-start",
        "session_id": payload["session_id"],
        "repo_id": payload["repo_id"],
        "source_commit": head,
        "baseline_file_count": len(payload["files"]),
        "session_state": str(state_path),
        "privacy": payload["privacy"],
    }


def _delta(
    baseline: Mapping[str, Mapping[str, Any]], current: Mapping[str, Mapping[str, Any]], used: Sequence[str]
) -> Tuple[Dict[str, str], List[str]]:
    changes: Dict[str, str] = {}
    for path in sorted(set(baseline).union(current)):
        if path not in baseline:
            changes[path] = "created-in-session"
        elif path not in current:
            changes[path] = "deleted-in-session"
        elif baseline[path].get("sha256") != current[path].get("sha256"):
            changes[path] = "modified-in-session"
    for path in sorted(set(used)):
        if path in current and path not in changes:
            changes[path] = "used-unchanged-in-session"
    scannable = [path for path, kind in changes.items() if kind != "deleted-in-session" and _is_candidate_path(path)]
    return changes, scannable


def _canonical_hash(row: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "content_hash"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_ledger(path: pathlib.Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    text = read_utf8_bounded(path, MAX_LEDGER_BYTES, "tool asset observation ledger")
    rows: List[Dict[str, Any]] = []
    previous = None
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise KnowledgeHubError("invalid observation ledger JSON at line {}".format(line_no)) from exc
        if not isinstance(row, dict) or row.get("schema") != OBSERVATION_SCHEMA:
            raise KnowledgeHubError("invalid observation ledger schema at line {}".format(line_no))
        if row.get("previous_hash") != previous or row.get("content_hash") != _canonical_hash(row):
            raise KnowledgeHubError("observation ledger hash chain failed at line {}".format(line_no))
        previous = row["content_hash"]
        rows.append(row)
    return rows


def _observation(
    state: Mapping[str, Any], repository: Mapping[str, Any], inspected: Mapping[str, Any], kind: str, validation: Mapping[str, str]
) -> Dict[str, Any]:
    session_hash = hashlib.sha256(str(state["session_id"]).encode("utf-8")).hexdigest()
    identity = "{}\0{}\0{}\0{}".format(session_hash, repository["repo_id"], inspected["path"], inspected["sha256"])
    return {
        "schema": OBSERVATION_SCHEMA,
        "observation_id": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
        "repo_id": repository["repo_id"],
        "project_id": repository["project_id"],
        "session_id_hash": session_hash,
        "tool_path": inspected["path"],
        "content_sha256": inspected["sha256"],
        "capability_signature": inspected["capability_signature"],
        "source_commit": state["source_commit"],
        "worktree_dirty": kind != "used-unchanged-in-session",
        "observation_type": kind,
        "validation": dict(validation),
        "observed_at": utc_timestamp(),
    }


def _append_observations(path: pathlib.Path, existing: List[Dict[str, Any]], new_rows: Sequence[Mapping[str, Any]]) -> int:
    known = {str(row.get("observation_id", "")) for row in existing}
    previous = existing[-1]["content_hash"] if existing else None
    appended = 0
    for value in new_rows:
        row = dict(value)
        if row["observation_id"] in known:
            continue
        row["previous_hash"] = previous
        row["content_hash"] = _canonical_hash(row)
        existing.append(row)
        known.add(row["observation_id"])
        previous = row["content_hash"]
        appended += 1
    _atomic_text(path, "".join(compact_json(row) + "\n" for row in existing))
    return appended


def _aggregates(rows: Sequence[Mapping[str, Any]], signatures: Sequence[str]) -> Dict[str, Any]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("capability_signature") in signatures:
            grouped[str(row["capability_signature"])].append(row)
    result = {}
    for signature, values in grouped.items():
        sessions = {str(row["session_id_hash"]) for row in values}
        projects = {str(row["project_id"]) for row in values}
        sessions_by_project: Dict[str, set[str]] = defaultdict(set)
        for row in values:
            sessions_by_project[str(row["project_id"])].add(str(row["session_id_hash"]))
        local_repeat = any(len(project_sessions) >= 2 for project_sessions in sessions_by_project.values())
        global_repeat = len(sessions) >= 3 and len(projects) >= 2
        result[signature] = {
            "observation_count": len(values),
            "distinct_session_count": len(sessions),
            "distinct_project_count": len(projects),
            "project_ids": sorted(projects),
            "sessions_by_project": {key: len(value) for key, value in sorted(sessions_by_project.items())},
            "hub_candidate_ready": local_repeat or global_repeat,
            "recommendation": "recommend-global-codex" if global_repeat else "keep-project-tool",
        }
    return result


def _update_candidate_recommendation(path: pathlib.Path, recommendation: str, aggregate: Mapping[str, Any]) -> None:
    metadata, body = load_markdown(path)
    metadata["recommendation"] = recommendation
    metadata["recommended_target"] = (
        "跨项目通用 Codex 源码候选" if recommendation == "recommend-global-codex" else "项目正式工具或项目 skill"
    )
    metadata["cross_session_evidence"] = {
        "distinct_session_count": aggregate["distinct_session_count"],
        "distinct_project_count": aggregate["distinct_project_count"],
        "project_ids": aggregate["project_ids"],
    }
    _atomic_text(path, render_markdown(metadata, body))


def close_tool_asset_session(
    hub_root: pathlib.Path,
    repo_root: pathlib.Path,
    state_path: pathlib.Path,
    candidate_out: pathlib.Path,
    ledger_path: pathlib.Path,
    validation: Mapping[str, str],
    used_paths: Sequence[str] = (),
    minimum_score: int = 50,
) -> Dict[str, Any]:
    repo = repo_root.expanduser().resolve()
    safe_state = _safe_runtime_path(hub_root, repo, state_path, (".json",))
    state = _load_json(safe_state, MAX_STATE_BYTES, "tool asset session state")
    if state.get("schema") != SESSION_SCHEMA:
        raise KnowledgeHubError("invalid tool asset session state schema")
    repository = _repository_identity(hub_root, repo, str(state.get("repo_id", "")))
    current = _snapshot(repo)
    changes, scannable = _delta(state.get("files", {}), current, used_paths)
    scan = scan_tool_assets(
        hub_root,
        repo,
        candidate_out,
        validation,
        source_repo=str(repository["repo_id"]),
        minimum_score=minimum_score,
        session_paths=scannable,
        session_paths_must_be_changed=False,
    ) if scannable else {"status": "pass", "inspected": [], "hub_candidate_generated": False}
    eligible = [row for row in scan.get("inspected", []) if row.get("eligible")]
    observations = [_observation(state, repository, row, changes[str(row["path"])], validation) for row in eligible]
    safe_ledger = _safe_runtime_path(hub_root, repo, ledger_path, (".jsonl",))
    ledger = _load_ledger(safe_ledger)
    appended = _append_observations(safe_ledger, ledger, observations)
    signatures = [str(row["capability_signature"]) for row in eligible]
    aggregates = _aggregates(ledger, signatures)
    selected_signature = str(scan.get("selected", {}).get("capability_signature", ""))
    selected_aggregate = aggregates.get(selected_signature, {})
    ready = bool(selected_aggregate.get("hub_candidate_ready"))
    if ready and scan.get("candidate_output"):
        _update_candidate_recommendation(
            pathlib.Path(str(scan["candidate_output"])),
            str(selected_aggregate["recommendation"]),
            selected_aggregate,
        )
    state["closed_at"] = utc_timestamp()
    state["close_observation_count"] = len(observations)
    _atomic_text(safe_state, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return {
        "status": "pass",
        "mode": "tool-asset-session-close",
        "repo_id": repository["repo_id"],
        "session_id_hash": hashlib.sha256(str(state["session_id"]).encode("utf-8")).hexdigest(),
        "changes": changes,
        "scannable_count": len(scannable),
        "observation_count": len(observations),
        "observation_appended_count": appended,
        "observation_ledger": str(safe_ledger),
        "aggregates": aggregates,
        "hub_candidate_ready": ready,
        "hub_candidate_generated": bool(scan.get("hub_candidate_generated")),
        "candidate_output": scan.get("candidate_output", ""),
        "scan": scan,
        "archive_conclusion": "达到跨会话候选阈值" if ready else "已记录观察，尚未达到 Hub candidate 阈值",
    }
