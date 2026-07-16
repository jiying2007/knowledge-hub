"""Shared parsing, registry and path helpers.

The repository intentionally keeps shell wrappers as the public entry points.
This module contains side-effect-free helpers so commands and tests use one
implementation for registry parsing, frontmatter and path handling.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
from typing import Any, Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import yaml


TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".csv"}
ALLOWED_STATUSES = {"draft", "active", "reviewing", "archived", "superseded", "rejected", "personal"}
CURRENT_KINDS = {"project-current", "architecture", "decision", "runbook", "standard", "validation"}
RECENT_KINDS = {"debug-record", "project-archive", "codex-session"}


class KnowledgeHubError(RuntimeError):
    """Expected command failure with a user-actionable message."""


def repository_root(explicit: Optional[str] = None) -> pathlib.Path:
    if explicit:
        root = pathlib.Path(explicit).expanduser().resolve()
    else:
        root = pathlib.Path(__file__).resolve().parents[3]
    if not (root / "registry" / "items.jsonl").exists():
        raise KnowledgeHubError("not a Knowledge Hub root: {}".format(root))
    return root


def resolve_today(value: str = "") -> Tuple[dt.date, str]:
    if value:
        source = "arg:--as-of"
        raw = value
    else:
        raw = os.environ.get("KNOWLEDGE_TODAY", "")
        source = "env:KNOWLEDGE_TODAY" if raw else "system-date"
    if not raw:
        return dt.date.today(), source
    try:
        return dt.date.fromisoformat(raw), source
    except ValueError as exc:
        raise KnowledgeHubError("date must use YYYY-MM-DD: {}".format(raw)) from exc


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def pretty_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False)


def load_json(path: pathlib.Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("invalid JSON {}: {}".format(path, exc)) from exc


def load_jsonl(path: pathlib.Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise KnowledgeHubError("invalid JSONL {}:{}: {}".format(path, line_no, exc)) from exc
        if not isinstance(value, dict):
            raise KnowledgeHubError("JSONL row must be an object: {}:{}".format(path, line_no))
        rows.append(value)
    return rows


def encode_jsonl(rows: Iterable[Mapping[str, Any]]) -> str:
    encoded = "\n".join(compact_json(dict(row)) for row in rows)
    return encoded + ("\n" if encoded else "")


def file_sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_bytes_bounded(
    path: pathlib.Path,
    maximum_bytes: int,
    label: str,
) -> bytes:
    """Read one regular file without a stat/read race bypassing its byte budget."""

    if maximum_bytes < 1:
        raise KnowledgeHubError("{} byte budget must be positive".format(label))
    if not path.is_file():
        raise KnowledgeHubError("{} must be a regular file".format(label))
    with path.open("rb") as handle:
        raw = handle.read(maximum_bytes + 1)
    if len(raw) > maximum_bytes:
        raise KnowledgeHubError(
            "{} exceeds {} bytes".format(label, maximum_bytes)
        )
    return raw


def read_utf8_bounded(
    path: pathlib.Path,
    maximum_bytes: int,
    label: str,
) -> str:
    """Read one bounded regular UTF-8 file."""

    raw = read_bytes_bounded(path, maximum_bytes, label)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise KnowledgeHubError("{} must be valid UTF-8".format(label)) from exc


def normalize_relpath(value: str) -> str:
    text = str(value or "").replace("\\", "/").strip()
    candidate = pathlib.PurePosixPath(text)
    if not text or candidate.is_absolute() or text.startswith(("~/", "./", "../")) or ".." in candidate.parts:
        raise KnowledgeHubError("path must be a safe repository-relative path: {}".format(value))
    return candidate.as_posix()


def resolve_inside(root: pathlib.Path, relative: str) -> pathlib.Path:
    safe = normalize_relpath(relative)
    target = (root / safe).resolve(strict=False)
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise KnowledgeHubError("path escapes Knowledge Hub root: {}".format(relative)) from exc
    return target


def display_path(value: Any) -> str:
    text = str(value)
    home = str(pathlib.Path.home())
    if text == home:
        return "~"
    if text.startswith(home + os.sep):
        return "~" + text[len(home) :]
    user_name = os.environ.get("USER", "")
    if user_name:
        alternate = "/vsdata/{}".format(user_name)
        if text == alternate:
            return "~"
        if text.startswith(alternate + "/"):
            return "~" + text[len(alternate) :]
    return text


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise KnowledgeHubError("unterminated Markdown frontmatter")
    raw = text[4:marker]
    try:
        metadata = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise KnowledgeHubError("invalid YAML frontmatter: {}".format(exc)) from exc
    if not isinstance(metadata, dict):
        raise KnowledgeHubError("Markdown frontmatter must be a mapping")
    return metadata, text[marker + 5 :].lstrip("\n")


def load_markdown(path: pathlib.Path) -> Tuple[Dict[str, Any], str]:
    try:
        return split_frontmatter(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise KnowledgeHubError("unable to read Markdown {}: {}".format(path, exc)) from exc


def render_markdown(metadata: Mapping[str, Any], body: str) -> str:
    frontmatter = yaml.safe_dump(
        dict(metadata),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    ).rstrip()
    return "---\n{}\n---\n\n{}".format(frontmatter, body.lstrip())


def registry_items(root: pathlib.Path) -> List[Dict[str, Any]]:
    return load_jsonl(root / "registry" / "items.jsonl")


def registry_items_by_id(root: pathlib.Path) -> Dict[str, Dict[str, Any]]:
    return {str(row.get("id")): row for row in registry_items(root) if row.get("id")}


def registry_items_by_path(root: pathlib.Path) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {}
    for row in registry_items(root):
        path = str(row.get("path", ""))
        if path:
            result.setdefault(path, []).append(row)
    return result


def project_rows(root: pathlib.Path) -> List[Dict[str, Any]]:
    return list((load_json(root / "registry" / "projects.json", {}) or {}).get("projects", []))


def repository_rows(root: pathlib.Path) -> List[Dict[str, Any]]:
    return list((load_json(root / "registry" / "repositories.json", {}) or {}).get("repositories", []))


def route_rows(root: pathlib.Path) -> List[Dict[str, Any]]:
    return list((load_json(root / "registry" / "project-routes.json", {}) or {}).get("routes", []))


def source_id(item: Mapping[str, Any]) -> str:
    source = item.get("source")
    return str(source.get("source_id", "")) if isinstance(source, dict) else ""


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "item"


def iter_text_file_records(
    root: pathlib.Path,
    include_control: bool = True,
) -> Iterator[Tuple[pathlib.Path, str, os.stat_result]]:
    excluded_parts = {".git", ".tmp", ".cache", "__pycache__", ".pytest_cache"}
    control_roots = {"registry", "tools", "artifacts"}
    root = pathlib.Path(root)
    pending = [(root, "")]
    while pending:
        directory, directory_relative = pending.pop()
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError:
            continue
        child_directories = []
        for entry in entries:
            try:
                is_directory = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if is_directory:
                if entry.name in excluded_parts:
                    continue
                if not include_control and not directory_relative and entry.name in control_roots:
                    continue
                relative = (
                    "{}/{}".format(directory_relative, entry.name)
                    if directory_relative
                    else entry.name
                )
                child_directories.append((pathlib.Path(entry.path), relative))
                continue
            if pathlib.Path(entry.name).suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                file_stat = entry.stat()
            except OSError:
                continue
            if not stat.S_ISREG(file_stat.st_mode):
                continue
            relative = (
                "{}/{}".format(directory_relative, entry.name)
                if directory_relative
                else entry.name
            )
            yield pathlib.Path(entry.path), relative, file_stat
        pending.extend(reversed(child_directories))


def iter_text_files(root: pathlib.Path, include_control: bool = True) -> Iterator[pathlib.Path]:
    for path, _, _ in iter_text_file_records(root, include_control=include_control):
        yield path


def run_rtk(
    root: pathlib.Path,
    command: Sequence[str],
    timeout: Optional[int] = None,
    accepted_exit_codes: Sequence[int] = (0,),
    extra_env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    full = ["rtk"] + list(command)
    started = dt.datetime.now()
    environment = os.environ.copy()
    if extra_env:
        environment.update({str(key): str(value) for key, value in extra_env.items()})
    completed = subprocess.run(
        full,
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=environment,
    )
    duration = (dt.datetime.now() - started).total_seconds()
    result = {
        "command": " ".join(full),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "duration_sec": round(duration, 3),
    }
    if completed.returncode not in accepted_exit_codes:
        raise KnowledgeHubError(
            "command failed ({}): {}\n{}".format(completed.returncode, result["command"], completed.stderr.strip())
        )
    return result


def parse_json_output(result: Mapping[str, Any]) -> Dict[str, Any]:
    raw = str(result.get("stdout", ""))
    if not raw.strip():
        raise KnowledgeHubError("empty JSON output: {}".format(result.get("command", "")))
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise KnowledgeHubError("command returned invalid JSON: {}".format(result.get("command", ""))) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("command JSON must be an object: {}".format(result.get("command", "")))
    return payload


def working_tree_signature(root: pathlib.Path) -> str:
    """Fingerprint the current Git candidate without hashing large tracked assets."""

    result = run_rtk(
        root,
        ["git", "-c", "core.quotePath=false", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        timeout=30,
    )
    paths = sorted(set(value for value in result["stdout"].split("\0") if value))
    digest = hashlib.sha256()
    for relative in paths:
        path = root / relative
        if not path.exists():
            digest.update(("missing\0{}\n".format(relative)).encode("utf-8"))
            continue
        stat = path.lstat()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b":")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def utc_timestamp() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
