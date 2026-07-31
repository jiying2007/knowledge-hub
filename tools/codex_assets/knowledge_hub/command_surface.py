"""Machine-verifiable five-plane command surface."""

from __future__ import annotations

import json
import pathlib
import re
from collections import Counter
from typing import Any, Dict, List, Mapping


PLANES = (
    "experience",
    "query",
    "governance",
    "content-artifact",
    "evidence-operations",
)
TIERS = ("daily", "maintenance", "governance", "engineering", "internal")
DAILY_COMMANDS = (
    "knowledge-check",
    "knowledge-health-summary",
    "knowledge-new",
    "knowledge-review-after",
    "knowledge-search",
)
_MODULE_PATTERN = re.compile(r"-m\s+(tools\.codex_assets\.knowledge_hub\.[A-Za-z0-9_.]+)")


def _load_catalog(root: pathlib.Path) -> Mapping[str, Any]:
    path = root / "registry/command-surface.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": 0, "commands": [], "error": str(exc)}
    return payload if isinstance(payload, Mapping) else {}


def _wrapper_names(root: pathlib.Path) -> Dict[str, pathlib.Path]:
    return {
        path.stem: path
        for path in sorted((root / "tools").glob("knowledge-*.sh"))
        if path.is_file()
    }


def _module_path(root: pathlib.Path, wrapper: pathlib.Path) -> pathlib.Path | None:
    try:
        text = wrapper.read_text(encoding="utf-8")
    except OSError:
        return None
    match = _MODULE_PATTERN.search(text)
    if not match:
        return None
    return root.joinpath(*match.group(1).split(".")).with_suffix(".py")


def _supports_summary_json(root: pathlib.Path, wrapper: pathlib.Path) -> bool:
    module = _module_path(root, wrapper)
    if module is None or not module.is_file():
        return False
    try:
        return "--summary-json" in module.read_text(encoding="utf-8")
    except OSError:
        return False


def _command_rows(catalog: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    rows = catalog.get("commands", [])
    return [row for row in rows if isinstance(row, Mapping)]


def evaluate_command_surface(root: pathlib.Path) -> Dict[str, Any]:
    """Compare the declarative catalog with the executable wrapper surface."""

    catalog = _load_catalog(root)
    rows = _command_rows(catalog)
    wrappers = _wrapper_names(root)
    by_name = {str(row.get("name", "")): row for row in rows if row.get("name")}
    catalog_names = set(by_name)
    wrapper_names = set(wrappers)
    uncataloged = sorted(wrapper_names - catalog_names)
    missing = sorted(catalog_names - wrapper_names)
    duplicate_count = len(rows) - len(by_name)
    invalid_rows = []
    summary_contract_errors = []
    for name, row in sorted(by_name.items()):
        if row.get("plane") not in PLANES or row.get("tier") not in TIERS:
            invalid_rows.append(name)
        wrapper = wrappers.get(name)
        if wrapper and bool(row.get("summary_json")) != _supports_summary_json(
            root, wrapper
        ):
            summary_contract_errors.append(name)
    daily = sorted(
        [dict(row) for row in rows if row.get("tier") == "daily"],
        key=lambda row: str(row.get("name", "")),
    )
    daily_names = sorted(str(row.get("name", "")) for row in daily)
    baseline = int(catalog.get("wrapper_baseline", 0) or 0)
    wrapper_growth = max(0, len(wrappers) - baseline)
    errors = []
    if catalog.get("schema_version") != 1:
        errors.append("command surface schema_version must be 1")
    if duplicate_count:
        errors.append("duplicate command names")
    if uncataloged:
        errors.append("uncataloged wrappers")
    if missing:
        errors.append("catalog wrappers missing")
    if invalid_rows:
        errors.append("invalid plane or tier")
    if daily_names != sorted(DAILY_COMMANDS):
        errors.append("daily command set drift")
    if not all(row.get("summary_json") is True for row in daily):
        errors.append("daily commands must support summary-json")
    if summary_contract_errors:
        errors.append("summary-json declaration differs from implementation")
    if wrapper_growth:
        errors.append("wrapper surface grew beyond baseline")
    by_plane = Counter(str(row.get("plane", "")) for row in rows)
    by_tier = Counter(str(row.get("tier", "")) for row in rows)
    return {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "read_only": True,
        "catalog": "registry/command-surface.json",
        "wrapper_count": len(wrappers),
        "wrapper_baseline": baseline,
        "wrapper_growth": wrapper_growth,
        "catalog_count": len(rows),
        "daily_count": len(daily),
        "daily_commands": daily_names,
        "daily": daily,
        "by_plane": {plane: by_plane.get(plane, 0) for plane in PLANES},
        "by_tier": {tier: by_tier.get(tier, 0) for tier in TIERS},
        "uncataloged_wrappers": uncataloged,
        "missing_wrappers": missing,
        "invalid_rows": invalid_rows,
        "summary_contract_errors": summary_contract_errors,
        "errors": errors,
    }
