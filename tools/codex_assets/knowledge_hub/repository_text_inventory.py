"""Complete tracked-text scope, not semantic approval or a new registry.

Observe exact HEAD Markdown/MDX/TXT with the caller's registry privacy roots.
Exclude private identities before hashing or projection. Ambiguous/changed
files are counted, not named. No external source, network or write is used.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import selectors
import subprocess
import time
from collections import Counter
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from .body_privacy import BodyPrivacyError, declared_private, digest_public_body

CONTRACT = "knowledge-hub-repository-text-inventory/v1"
MAX_METADATA_BYTES = 8 * 1024 * 1024
MAX_TREE_ENTRIES = 50000
MAX_TEXT_FILES = 5000
MAX_BODY_BYTES = 4 * 1024 * 1024
MAX_TOTAL_BODY_BYTES = 64 * 1024 * 1024
TEXT_SUFFIXES = frozenset({".md", ".mdx", ".txt"})
SHA1 = re.compile(r"[a-f0-9]{40}\Z")
WITHHELD_CODES = frozenset({
    "invalid-body-path", "reserved-private-body", "unsupported-safe-file-open",
    "not-a-regular-body", "ambiguous-header-byte-order-mark",
    "header-event-or-alias-budget", "header-depth-budget", "header-must-be-a-mapping",
    "unsupported-header-key", "duplicate-header-key", "ambiguous-privacy-value",
    "unknown-privacy-classification", "first-line-budget", "ambiguous-header-delimiter",
    "header-incomplete-or-over-budget", "invalid-expected-git-blob", "invalid-body-budget",
    "body-byte-budget", "private-body-must-not-be-hashed", "body-changed-during-read",
    "body-not-at-expected-git-blob",
})


def _withheld_reason(error: BaseException) -> str:
    """Return only fixed codes; suppressed exception details remain private."""
    seen = set()
    current: Optional[BaseException] = error
    for _ in range(8):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        if isinstance(current, BodyPrivacyError) and current.args:
            code = current.args[0]
            if type(code) is str and code in WITHHELD_CODES:
                return code
        if type(current).__module__.startswith("yaml."):
            return "invalid-header-yaml"
        if isinstance(current, UnicodeError):
            return "invalid-header-encoding"
        if isinstance(current, OSError):
            return "body-io-unavailable"
        current = current.__cause__ or current.__context__
    return "unclassified-body-failure"


class InventoryError(ValueError):
    """Only non-identifying fixed error codes may leave this module."""


def _git(root: pathlib.Path, args: Sequence[str]) -> bytes:
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
    command = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
               "-c", "core.hooksPath=/dev/null", "-C", str(root)] + list(args)
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          env=env) as process:
        if process.stdout is None:
            raise InventoryError("git-output-unavailable")
        chunks, size = [], 0
        deadline = time.monotonic() + 15
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise InventoryError("git-observation-timeout")
                part = os.read(process.stdout.fileno(), min(65536, MAX_METADATA_BYTES - size + 1))
                if not part:
                    break
                size += len(part)
                if size > MAX_METADATA_BYTES:
                    raise InventoryError("git-metadata-byte-budget")
                chunks.append(part)
            if process.wait(timeout=max(0.001, deadline - time.monotonic())):
                raise InventoryError("git-observation-unavailable")
            return b"".join(chunks)
        finally:
            selector.close()
            if process.poll() is None:
                process.kill()
                process.wait()


def _relative(value: str) -> bool:
    path = pathlib.PurePosixPath(value)
    return bool(value and value != "." and not path.is_absolute()
                and path.as_posix() == value and ".." not in path.parts
                and "\\" not in value
                and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def _head_texts(root: pathlib.Path):
    top = _git(root, ["rev-parse", "--show-toplevel"]).decode("utf-8").strip()
    if pathlib.Path(top).resolve() != root:
        raise InventoryError("root-is-not-checkout-root")
    revision = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode("ascii").strip()
    if not SHA1.fullmatch(revision):
        raise InventoryError("unexpected-git-object-format")
    raw = _git(root, ["ls-tree", "-r", "-z", "--full-tree", revision])
    if raw and not raw.endswith(b"\0"):
        raise InventoryError("incomplete-git-tree")
    entries = raw.split(b"\0")[:-1]
    if len(entries) > MAX_TREE_ENTRIES:
        raise InventoryError("git-tree-entry-budget")
    rows, seen, tracked_entries = [], set(), {}
    for entry in entries:
        identity, name = entry.split(b"\t", 1)
        mode, kind, blob = identity.decode("ascii").split()
        relative = name.decode("utf-8")
        if not _relative(relative) or relative in seen or not SHA1.fullmatch(blob):
            raise InventoryError("invalid-git-tree-entry")
        seen.add(relative)
        tracked_entries[relative] = (mode, kind)
        if pathlib.PurePosixPath(relative).suffix.lower() in TEXT_SUFFIXES:
            rows.append((relative, mode, kind, blob))
    if len(rows) > MAX_TEXT_FILES:
        raise InventoryError("tracked-text-file-budget")
    return revision, rows, tracked_entries


def _registered_asset_counts(registered: Mapping, tracked: Mapping, roots: Set[str]) -> Dict[str, int]:
    """Bounded metadata-only census of registered non-text files and absent paths."""
    if not isinstance(registered, Mapping):
        raise InventoryError("invalid-registry-mapping")
    directories: Set[str] = set()
    for path in tracked:
        directories.update(parent.as_posix() for parent in pathlib.PurePosixPath(path).parents
                           if parent.as_posix() != ".")
    counts = {"registered_nontext_regular_count": 0,
              "registered_nontext_unsafe_count": 0,
              "registered_missing_path_count": 0,
              "registered_directory_root_count": 0}
    for path in registered:
        if not isinstance(path, str) or not _relative(path):
            raise InventoryError("invalid-registered-path")
        if any(path == root or path.startswith(root + "/") for root in roots):
            continue
        entry = tracked.get(path)
        if entry is not None:
            if pathlib.PurePosixPath(path).suffix.lower() not in TEXT_SUFFIXES:
                if entry in {("100644", "blob"), ("100755", "blob")}:
                    counts["registered_nontext_regular_count"] += 1
                else:
                    counts["registered_nontext_unsafe_count"] += 1
        elif path in directories:
            counts["registered_directory_root_count"] += 1
        else:
            counts["registered_missing_path_count"] += 1
    return counts


def _result(status: str, **values) -> Dict:
    return {"contract": CONTRACT, "status": status, "read_only": True,
            "semantic_review_performed": False, "owner_approval_performed": False,
            "canonical_write_performed": False, "private_identities_exported": False,
            "unlabelled_text_is_not_a_sanitization_certificate": True,
            "full_external_migration_proven": False, "terminal": False, **values}


def build_repository_text_inventory(root: pathlib.Path, private_roots: Set[str],
                                    registry_ids_by_path: Mapping) -> Dict:
    """Partition every committed text into observed, private, or withheld.

    Non-Git synthetic fixtures are explicitly unavailable, never complete.
    Every exported SHA256 is checked against the exact Git blob in the same
    descriptor pass. Withheld identities and raw body text are never exported.
    """
    root = root.resolve()
    try:
        revision, entries, tracked_entries = _head_texts(root)
        roots = set(private_roots) | {"notes/personal", "personal", ".private"}
        if not all(isinstance(path, str) and _relative(path) for path in roots):
            raise InventoryError("invalid-private-root")
        registered_asset_counts = _registered_asset_counts(registry_ids_by_path, tracked_entries, roots)
        rows: List[Dict[str, Any]] = []
        withheld_reasons: Dict[str, int] = Counter()
        private_count = withheld_count = total_bytes = 0
        for relative, mode, kind, blob in entries:
            if any(relative == path or relative.startswith(path + "/") for path in roots):
                private_count += 1
                continue
            if mode not in {"100644", "100755"} or kind != "blob":
                withheld_count += 1
                withheld_reasons["unsupported-git-entry"] += 1
                continue
            try:
                if declared_private(root, relative):
                    private_count += 1
                    continue
                budget = min(MAX_BODY_BYTES, MAX_TOTAL_BODY_BYTES - total_bytes)
                sha, size = digest_public_body(root, relative, budget, expected_git_blob=blob)
            except BodyPrivacyError as error:
                withheld_count += 1
                withheld_reasons[_withheld_reason(error)] += 1
                continue
            total_bytes += size
            rows.append({"path": relative, "git_blob": blob, "sha256": sha,
                         "size_bytes": size, "exact_registered": relative in registry_ids_by_path})
        current = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"]).decode("ascii").strip()
        if current != revision:
            raise InventoryError("head-changed-during-observation")
        result = _result(
            "needs-review" if (withheld_count or registered_asset_counts["registered_missing_path_count"]
                               or registered_asset_counts["registered_nontext_unsafe_count"]) else "observed",
            source_revision=revision, head_inventory_complete=True,
            tracked_text_count=len(entries), observed_count=len(rows),
            private_excluded_count=private_count, withheld_count=withheld_count,
            withheld_reason_counts=dict(sorted(withheld_reasons.items())),
            observed_body_bytes=total_bytes, body_records=rows,
            registered_count=sum(row["exact_registered"] for row in rows),
            unregistered_count=sum(not row["exact_registered"] for row in rows),
            registered_asset_counts=registered_asset_counts,
            registered_nontext_metadata_only=True,
            registered_nontext_content_verified=False,
        )
        encoded = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > MAX_METADATA_BYTES:
            raise InventoryError("inventory-output-byte-budget")
        result["report_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return result
    except (InventoryError, OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        # Even exception context may identify a private path. Project no details.
        return _result("unavailable", head_inventory_complete=False,
                       tracked_text_count=None, body_records=[])
