"""Shared parsing, registry and path helpers.

The repository intentionally keeps shell wrappers as the public entry points.
This module contains side-effect-free helpers so commands and tests use one
implementation for registry parsing, frontmatter and path handling.
"""

from __future__ import annotations

import datetime as dt
import errno
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

import yaml
from yaml.events import AliasEvent


TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".csv"}
DEFAULT_JSON_MAX_BYTES = 16 * 1024 * 1024
DEFAULT_JSONL_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MARKDOWN_MAX_BYTES = 8 * 1024 * 1024
MAX_FRONTMATTER_BYTES = 256 * 1024
MAX_YAML_ALIASES = 64
MAX_YAML_NODES = 10000
MAX_YAML_DEPTH = 64
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


def load_json(
    path: pathlib.Path,
    default: Any = None,
    maximum_bytes: int = DEFAULT_JSON_MAX_BYTES,
) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(read_utf8_bounded(path, maximum_bytes, "JSON file"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError("invalid JSON {}: {}".format(path, exc)) from exc


def load_jsonl(
    path: pathlib.Path,
    maximum_bytes: int = DEFAULT_JSONL_MAX_BYTES,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    text = read_utf8_bounded(path, maximum_bytes, "JSONL file")
    for line_no, line in enumerate(text.splitlines(), 1):
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
    try:
        file_stat = path.lstat()
    except OSError as exc:
        raise KnowledgeHubError("unable to stat file for SHA256: {}".format(path)) from exc
    if stat.S_ISLNK(file_stat.st_mode):
        raise KnowledgeHubError("file for SHA256 must not be a symlink: {}".format(path))
    if not stat.S_ISREG(file_stat.st_mode):
        raise KnowledgeHubError("file for SHA256 must be regular: {}".format(path))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise KnowledgeHubError("unable to open file for SHA256: {}".format(path)) from exc
    try:
        opened_stat = os.fstat(descriptor)
        if not stat.S_ISREG(opened_stat.st_mode):
            raise KnowledgeHubError("file for SHA256 must be regular: {}".format(path))
        for block in iter(lambda: os.read(descriptor, 1024 * 1024), b""):
            digest.update(block)
    finally:
        os.close(descriptor)
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
    try:
        file_stat = path.lstat()
    except OSError as exc:
        raise KnowledgeHubError("{} must be a regular file".format(label)) from exc
    if stat.S_ISLNK(file_stat.st_mode):
        raise KnowledgeHubError("{} must not be a symlink".format(label))
    if not stat.S_ISREG(file_stat.st_mode):
        raise KnowledgeHubError("{} must be a regular file".format(label))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise KnowledgeHubError("{} must not be a symlink".format(label)) from exc
        raise KnowledgeHubError("{} could not be opened".format(label)) from exc
    try:
        return _read_descriptor_bounded(descriptor, maximum_bytes, label)
    finally:
        os.close(descriptor)


def _read_descriptor_bounded(
    descriptor: int,
    maximum_bytes: int,
    label: str,
) -> bytes:
    file_stat = os.fstat(descriptor)
    if not stat.S_ISREG(file_stat.st_mode):
        raise KnowledgeHubError("{} must be a regular file".format(label))
    if file_stat.st_size > maximum_bytes:
        raise KnowledgeHubError("{} exceeds {} bytes".format(label, maximum_bytes))
    chunks: List[bytes] = []
    total = 0
    while total <= maximum_bytes:
        block = os.read(descriptor, min(1024 * 1024, maximum_bytes + 1 - total))
        if not block:
            break
        chunks.append(block)
        total += len(block)
    if total > maximum_bytes:
        raise KnowledgeHubError("{} exceeds {} bytes".format(label, maximum_bytes))
    return b"".join(chunks)


def read_repository_bytes_bounded(
    root: pathlib.Path,
    relative: str,
    maximum_bytes: int,
    label: str,
) -> bytes:
    """Read a repository-relative regular file without following any symlink component."""

    if maximum_bytes < 1:
        raise KnowledgeHubError("{} byte budget must be positive".format(label))
    safe = normalize_relpath(relative)
    parts = pathlib.PurePosixPath(safe).parts
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_descriptor = -1
    file_descriptor = -1
    try:
        directory_descriptor = os.open(str(pathlib.Path(root).resolve()), directory_flags)
        for component in parts[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=directory_descriptor,
            )
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        file_descriptor = os.open(
            parts[-1],
            file_flags,
            dir_fd=directory_descriptor,
        )
        return _read_descriptor_bounded(file_descriptor, maximum_bytes, label)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise KnowledgeHubError(
                "{} path contains a symlink or invalid directory component".format(label)
            ) from exc
        if exc.errno == errno.ENOENT:
            raise KnowledgeHubError("{} must be a regular file".format(label)) from exc
        raise KnowledgeHubError("{} could not be opened safely".format(label)) from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        if directory_descriptor >= 0:
            os.close(directory_descriptor)


def read_repository_utf8_bounded(
    root: pathlib.Path,
    relative: str,
    maximum_bytes: int,
    label: str,
) -> str:
    raw = read_repository_bytes_bounded(root, relative, maximum_bytes, label)
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise KnowledgeHubError("{} must be valid UTF-8".format(label)) from exc


def ensure_private_directory(path: pathlib.Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise KnowledgeHubError("private cache path must be a real directory: {}".format(path))
    os.chmod(str(path), 0o700)


def ensure_private_directory_tree(anchor: pathlib.Path, target: pathlib.Path) -> None:
    """Create every directory below an existing trusted anchor with mode 0700."""

    anchor_path = pathlib.Path(anchor)
    target_path = pathlib.Path(target)
    try:
        relative = target_path.relative_to(anchor_path)
    except ValueError as exc:
        raise KnowledgeHubError(
            "private directory target must stay below its anchor: {}".format(target_path)
        ) from exc
    if anchor_path.is_symlink() or not anchor_path.is_dir():
        raise KnowledgeHubError(
            "private directory anchor must be a real directory: {}".format(anchor_path)
        )
    current = anchor_path
    for component in relative.parts:
        current = current / component
        ensure_private_directory(current)


def ensure_private_file(path: pathlib.Path) -> None:
    if not path.exists():
        return
    file_stat = path.lstat()
    if stat.S_ISLNK(file_stat.st_mode) or not stat.S_ISREG(file_stat.st_mode):
        raise KnowledgeHubError("private cache file must be regular and not a symlink: {}".format(path))
    os.chmod(str(path), 0o600)


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
    root_resolved = root.resolve()
    current = root_resolved
    for component in pathlib.PurePosixPath(safe).parts:
        current = current / component
        try:
            component_stat = current.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            raise KnowledgeHubError("unable to inspect repository path: {}".format(relative)) from exc
        if stat.S_ISLNK(component_stat.st_mode):
            raise KnowledgeHubError("repository path must not contain a symlink: {}".format(relative))
    target = (root_resolved / safe).resolve(strict=False)
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise KnowledgeHubError("path escapes Knowledge Hub root: {}".format(relative)) from exc
    return target


def user_path_prefixes() -> List[str]:
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/vsdata/{}".format(user_name))
    return [prefix for prefix in prefixes if prefix and prefix != "/"]


def display_path(value: Any) -> str:
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            return "~"
        if text.startswith(prefix + os.sep):
            return "~" + text[len(prefix) :]
    return text


class _BoundedSafeLoader(yaml.SafeLoader):
    def __init__(self, stream: Any) -> None:
        super().__init__(stream)
        self._knowledge_alias_count = 0
        self._knowledge_node_count = 0
        self._knowledge_depth = 0

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(AliasEvent):
            self._knowledge_alias_count += 1
            if self._knowledge_alias_count > MAX_YAML_ALIASES:
                raise yaml.YAMLError(
                    "frontmatter alias budget exceeds {}".format(MAX_YAML_ALIASES)
                )
        self._knowledge_depth += 1
        if self._knowledge_depth > MAX_YAML_DEPTH:
            raise yaml.YAMLError(
                "frontmatter depth exceeds {}".format(MAX_YAML_DEPTH)
            )
        try:
            node = super().compose_node(parent, index)
        finally:
            self._knowledge_depth -= 1
        self._knowledge_node_count += 1
        if self._knowledge_node_count > MAX_YAML_NODES:
            raise yaml.YAMLError(
                "frontmatter node budget exceeds {}".format(MAX_YAML_NODES)
            )
        return node


def split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise KnowledgeHubError("unterminated Markdown frontmatter")
    raw = text[4:marker]
    if len(raw.encode("utf-8")) > MAX_FRONTMATTER_BYTES:
        raise KnowledgeHubError(
            "Markdown frontmatter exceeds {} bytes".format(MAX_FRONTMATTER_BYTES)
        )
    try:
        # _BoundedSafeLoader subclasses SafeLoader and adds alias/depth/node budgets.
        metadata = yaml.load(raw, Loader=_BoundedSafeLoader) or {}  # nosec B506
    except yaml.YAMLError as exc:
        raise KnowledgeHubError("invalid YAML frontmatter: {}".format(exc)) from exc
    if not isinstance(metadata, dict):
        raise KnowledgeHubError("Markdown frontmatter must be a mapping")
    return metadata, text[marker + 5 :].lstrip("\n")


def load_markdown(path: pathlib.Path) -> Tuple[Dict[str, Any], str]:
    try:
        return split_frontmatter(
            read_utf8_bounded(path, DEFAULT_MARKDOWN_MAX_BYTES, "Markdown file")
        )
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
                if entry.is_symlink():
                    continue
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
                file_stat = entry.stat(follow_symlinks=False)
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
    """Content-hash the current Git candidate without trusting size or mtime."""

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
        file_stat = path.lstat()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(stat.S_IFMT(file_stat.st_mode)).encode("ascii"))
        digest.update(b":")
        if stat.S_ISLNK(file_stat.st_mode):
            digest.update(b"symlink:")
            digest.update(os.readlink(str(path)).encode("utf-8", errors="surrogateescape"))
        elif stat.S_ISREG(file_stat.st_mode):
            digest.update(file_sha256(path).encode("ascii"))
        else:
            digest.update(b"unsupported")
        digest.update(b"\n")
    return digest.hexdigest()


def utc_timestamp() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
