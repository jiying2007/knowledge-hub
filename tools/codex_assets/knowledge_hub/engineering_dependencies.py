"""Dependency manifest and hash-lock parsing for the Engineering contract."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


PIN_PATTERN = re.compile(
    r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?==([^\s;\\]+)(?:\s*;\s*(.+?))?(?:\s+\\.*)?$"
)
HASH_PATTERN = re.compile(r"--hash=sha256:([0-9a-f]{64})(?:\s|$)")


def _normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def direct_pins(text: str, allow_include: bool = False) -> Tuple[Dict[str, str], List[str]]:
    rows: Dict[str, str] = {}
    errors: List[str] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if allow_include and line.startswith("-r "):
            continue
        match = PIN_PATTERN.match(line)
        if not match:
            errors.append("line {} is not an exact dependency pin".format(line_no))
            continue
        name = _normalized_name(match.group(1))
        if name in rows:
            errors.append("line {} duplicates dependency {}".format(line_no, name))
        rows[name] = match.group(2)
    return rows, errors


def _logical_lock_entries(text: str) -> List[str]:
    entries: List[str] = []
    current: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("--") and not current:
            entries.append(line)
            continue
        continuation = line.endswith("\\")
        current.append(line[:-1].strip() if continuation else line)
        if not continuation:
            entries.append(" ".join(current))
            current = []
    if current:
        entries.append(" ".join(current))
    return entries


def lock_health(text: str) -> Dict[str, Any]:
    entries = _logical_lock_entries(text)
    requirement_entries = [row for row in entries if not row.startswith("--")]
    invalid_options = [row for row in entries if row.startswith("--")]
    unhashed: List[str] = []
    unpinned: List[str] = []
    package_names: List[str] = []
    package_versions: Dict[str, Set[str]] = {}
    for row in requirement_entries:
        head = row.split(" --hash=", 1)[0].strip()
        match = PIN_PATTERN.match(head)
        if not match:
            unpinned.append(head)
            continue
        name = _normalized_name(match.group(1))
        package_names.append(name)
        package_versions.setdefault(name, set()).add(match.group(2))
        if not HASH_PATTERN.findall(row):
            unhashed.append(head)
    hash_complete = bool(requirement_entries) and not unhashed and not unpinned
    return {
        "entry_count": len(requirement_entries),
        "package_count": len(set(package_names)),
        "packages": sorted(set(package_names)),
        "versions": {
            name: sorted(values)
            for name, values in sorted(package_versions.items())
        },
        "hash_complete": hash_complete,
        "unhashed_entries": unhashed[:20],
        "unpinned_entries": unpinned[:20],
        "unsupported_global_options": invalid_options[:20],
    }


def lock_version_mismatches(
    direct: Mapping[str, str],
    versions: Mapping[str, Sequence[str]],
) -> List[Dict[str, Any]]:
    mismatches: List[Dict[str, Any]] = []
    for name, expected in sorted(direct.items()):
        observed = sorted(set(str(value) for value in versions.get(name, [])))
        if expected not in observed:
            mismatches.append(
                {
                    "package": name,
                    "expected": expected,
                    "observed": observed,
                }
            )
    return mismatches
