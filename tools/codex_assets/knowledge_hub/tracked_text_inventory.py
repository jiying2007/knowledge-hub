"""Exact-HEAD text census, separate from selected-body and semantic review.

No body text, private identity, owner decision or review claim is exported.
Unclassifiable entries remain counted; they can never silently disappear.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import pathlib
import re
import selectors
import subprocess
import time

import yaml

from .body_privacy import BodyPrivacyError, _header, _identity, _open_body

MAX_METADATA = 8 * 1024 * 1024
MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_ENTRIES = 50000
OID = re.compile(r"[a-f0-9]{40}\Z")
TEXT = frozenset({".md", ".mdx", ".txt"})
PRIVATE = frozenset({"private", "personal-local", "personal"})
PUBLIC = frozenset({"public", "team-internal"})
STATUSES = frozenset({"active", "reviewing", "draft", "archived", "rejected", "deprecated", "superseded", "personal"})
RESERVED = ("notes/personal", "personal", ".private")


class InventoryError(ValueError):
    """Fixed codes only: never a path, content value or subprocess output."""


def _require(condition, code):
    if not condition:
        raise InventoryError(code)


def _canonical(path):
    if not isinstance(path, str) or not path or len(path.encode("utf-8")) > 1024:
        return False
    pure = pathlib.PurePosixPath(path)
    return (not pure.is_absolute() and pure.as_posix() == path and path != "."
            and ".." not in pure.parts and "\\" not in path
            and not any(ord(c) < 32 or ord(c) == 127 for c in path))


def _git(root, arguments):
    """Bound output while reading; no hooks, shell, network or optional locks."""
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
    command = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
               "-c", "core.hooksPath=/dev/null", "-C", str(root)] + arguments
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env) as process:
        chunks, size = [], 0
        deadline = time.monotonic() + 15
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            while True:
                remaining = deadline - time.monotonic()
                _require(remaining > 0 and bool(selector.select(remaining)), "git-read-timeout")
                chunk = os.read(process.stdout.fileno(), min(65536, MAX_METADATA - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                _require(size <= MAX_METADATA, "git-output-budget")
                chunks.append(chunk)
            _require(process.wait(timeout=max(0.01, deadline - time.monotonic())) == 0, "git-read-failed")
            return b"".join(chunks)
        finally:
            selector.close()
            if process.poll() is None:
                process.kill()


def _tree(root):
    top = pathlib.Path(_git(root, ["rev-parse", "--show-toplevel"]).decode().strip())
    _require(top.resolve() == root, "repository-root-required")
    head = _git(root, ["rev-parse", "--verify", "HEAD"]).decode().strip()
    _require(OID.fullmatch(head), "unsupported-git-object-format")
    raw = _git(root, ["ls-tree", "-r", "-z", "--full-tree", head])
    _require(raw.endswith(b"\0"), "empty-or-incomplete-tree")
    result = {}
    for record in raw[:-1].split(b"\0"):
        metadata, name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split(" ")
        path = name.decode("utf-8")
        _require(_canonical(path) and path not in result and OID.fullmatch(oid), "invalid-tree-entry")
        result[path] = {"mode": mode, "kind": kind, "oid": oid}
        _require(len(result) <= MAX_ENTRIES, "tree-entry-budget")
    return head, result


def _blob_sha(data):
    # SHA1 is mandated by this Git object format, not used for security approval.
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()  # nosec B324


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "duplicate-registry-key")
        result[key] = value
    return result


def _registry(root, tree):
    path = "registry/items.jsonl"
    entry = tree.get(path, {})
    _require(entry.get("kind") == "blob" and entry.get("mode") in {"100644", "100755"}, "registry-not-regular")
    with _open_body(root, path) as handle:
        before = _identity(os.fstat(handle.fileno()))
        raw = handle.read(MAX_METADATA + 1)
        _require(before == _identity(os.fstat(handle.fileno())), "registry-changing")
    _require(len(raw) <= MAX_METADATA and _blob_sha(raw) == entry["oid"], "registry-not-exact-head")
    rows, ids, private = {}, set(), set(RESERVED)
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line, object_pairs_hook=_pairs)
        _require(isinstance(row, dict), "invalid-registry-row")
        path, identity = row.get("path"), row.get("id")
        _require(_canonical(path) and path not in rows, "invalid-registry-path")
        _require(isinstance(identity, str) and identity and identity not in ids, "invalid-registry-id")
        _require(row.get("status") in STATUSES and row.get("visibility") in PRIVATE | PUBLIC, "unknown-registry-privacy")
        rows[path] = row
        ids.add(identity)
        if row["status"] == "personal" or row["visibility"] in PRIVATE:
            private.add(path)
    return rows, private


def _inside(path, roots):
    return any(path == prefix or path.startswith(prefix + "/") for prefix in roots)


def _eligible(path, registered):
    """Authorized Hub text scope; source/raw/runtime content is not expanded."""
    if path in registered:
        return pathlib.PurePosixPath(path).suffix.lower() in TEXT | {".sh", ".json"}
    parts = pathlib.PurePosixPath(path).parts
    if parts[0] == "sources":
        return len(parts) in {2, 3} and parts[-1] in {"README.md", "coverage.md", "source-policy.md"}
    if len(parts) == 1:
        return path in {"README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "requirements-dev.txt", "requirements-runtime.txt"}
    return parts[0] in {"docs", "projects", "domains", "governance", "indexes", "templates", "registry", "schemas", "tools", ".github"} or parts[:2] == ("artifacts", "manifests") or path == "artifacts/README.md"


def _public_bytes(root, path, consumed):
    remaining = MAX_TOTAL - consumed[0]
    _require(remaining >= 65536, "global-read-budget")
    with _open_body(root, path) as handle:
        try:
            before = os.fstat(handle.fileno())
            _require(before.st_size <= min(MAX_FILE, remaining), "body-budget")
            private, prefix = _header(handle)
            if private:
                return None
            limit = min(MAX_FILE, remaining)
            _require(len(prefix) <= limit, "body-budget")
            data = prefix + handle.read(limit - len(prefix) + 1)
            after = os.fstat(handle.fileno())
            _require(len(data) <= limit and len(data) == before.st_size, "body-budget-or-size-drift")
            _require(_identity(before) == _identity(after), "body-changed-during-read")
            data.decode("utf-8")  # A text census must not silently accept binary payloads.
            return data
        finally:
            consumed[0] += handle.tell()  # Include failed/changed reads in the budget.


def _role(path, registered):
    if path in registered:
        return "registered-asset"
    if path.startswith("sources/"):
        return "source-control"
    if path.startswith("indexes/"):
        return "navigation-index"
    if path.startswith("templates/"):
        return "template"
    if path in {"requirements-dev.txt", "requirements-runtime.txt"}:
        return "dependency-input"
    return "unregistered-text"


def _scan(root, tree, registry, private):
    counts = collections.Counter({key: 0 for key in (
        "tracked_text", "registered_nontext", "private_excluded", "policy_deferred",
        "unsupported_entry", "classification_or_read_deferred", "worktree_drift",
        "public_exact_head", "registered_public", "unregistered_public", "hashed_bytes")})
    _require(sum(pathlib.PurePosixPath(p).suffix.lower() in TEXT or p in registry for p in tree) <= 5000, "text-entry-budget")
    records, consumed = [], [0]
    for path, entry in sorted(tree.items()):
        text = pathlib.PurePosixPath(path).suffix.lower() in TEXT
        if not text and path not in registry:
            continue
        counts["tracked_text" if text else "registered_nontext"] += 1
        if _inside(path, private):
            counts["private_excluded"] += 1
            continue
        if entry["kind"] != "blob" or entry["mode"] not in {"100644", "100755"}:
            counts["unsupported_entry"] += 1
            continue
        if not _eligible(path, registry):
            counts["policy_deferred"] += 1
            continue
        try:
            data = _public_bytes(root, path, consumed)
        except (BodyPrivacyError, InventoryError, OSError, UnicodeError, ValueError, yaml.YAMLError, RecursionError):
            counts["classification_or_read_deferred"] += 1
            continue
        if data is None:
            counts["private_excluded"] += 1
            continue
        if _blob_sha(data) != entry["oid"]:
            counts["worktree_drift"] += 1
            continue
        counts["hashed_bytes"] += len(data)
        counts["public_exact_head"] += 1
        counts["registered_public" if path in registry else "unregistered_public"] += 1
        records.append({"path": path, "git_blob_sha1": entry["oid"],
                        "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
                        "registered": path in registry, "asset_role": _role(path, registry),
                        "semantic_review_performed": False})
    counts["read_bytes_including_deferred"] = consumed[0]
    return dict(counts), records


def _registry_gaps(tree, registry, private):
    directories = {parent.as_posix() for path in tree for parent in pathlib.PurePosixPath(path).parents}
    missing = directory_roots = 0
    for path in registry:
        if _inside(path, private) or path in tree:
            continue
        if path in directories:
            directory_roots += 1
        else:
            missing += 1
    return missing, directory_roots


def build_tracked_text_inventory(root):
    """Return a fail-closed observation; never alter existing coverage verdicts."""
    try:
        root = pathlib.Path(root)
        _require(root.is_dir() and not root.is_symlink(), "invalid-repository-root")
        root = root.resolve()
        head, tree = _tree(root)
        registry, private = _registry(root, tree)
        counts, records = _scan(root, tree, registry, private)
        _require(_git(root, ["rev-parse", "--verify", "HEAD"]).decode().strip() == head, "head-changed")
        _registry(root, tree)  # Recheck the exact registry bytes after classification.
        missing, directory_roots = _registry_gaps(tree, registry, private)
        counts.update(registered_missing=missing, registered_directory_roots=directory_roots)
        deferred = missing + sum(counts[k] for k in ("policy_deferred", "unsupported_entry", "classification_or_read_deferred", "worktree_drift"))
        return {"contract": "knowledge-hub-tracked-text-inventory/v1", "status": "needs-review" if deferred else "observed",
                "source_revision": head, "head_enumeration_complete": True,
                "all_tracked_entries": len(tree), "declared_private_binding": "worktree-exclusion-before-content-hashing",
                "scope": "all-HEAD-md-mdx-txt-plus-registered-files", "counts": counts,
                "unresolved_count": deferred, "records": records, "read_only": True,
                "canonical_write_performed": False, "private_identity_exported": False,
                "full_content_review_proven": False, "owner_approval_performed": False,
                "notes_zh": "全仓文本身份清单不是语义审读。导航、模板和来源控制不因分类自动豁免；私有及无法分类项仅计数。"}
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError, BodyPrivacyError):
        return {"contract": "knowledge-hub-tracked-text-inventory/v1", "status": "blocked",
                "head_enumeration_complete": False, "records": [], "read_only": True,
                "canonical_write_performed": False, "private_identity_exported": False,
                "full_content_review_proven": False, "owner_approval_performed": False,
                "reason": "unavailable-or-unsafe-exact-head-inventory"}
