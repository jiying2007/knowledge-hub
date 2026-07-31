"""Artifact capacity and immutable-reference governance."""

from __future__ import annotations

import json
import pathlib
import urllib.parse
from typing import Any, Dict, List, Mapping

from .common import KnowledgeHubError, load_jsonl, run_rtk


IMMUTABLE_ARTIFACT_REF_SCHEMA = "knowledge-hub.immutable-artifact-ref.v1"


def validate_immutable_artifact_ref(row: Mapping[str, Any]) -> List[str]:
    errors = []
    required = ("schema_version", "id", "uri", "size", "sha256", "owner")
    for field in required:
        if field not in row or row.get(field) in {"", None}:
            errors.append("missing {}".format(field))
    if row.get("schema_version") != IMMUTABLE_ARTIFACT_REF_SCHEMA:
        errors.append("invalid schema_version")
    sha256 = str(row.get("sha256", ""))
    if len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256):
        errors.append("invalid sha256")
    size = row.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        errors.append("invalid size")
    uri = str(row.get("uri", ""))
    try:
        parsed_uri = urllib.parse.urlsplit(uri)
    except ValueError:
        parsed_uri = urllib.parse.SplitResult("", "", "", "", "")
        errors.append("invalid uri")
    if parsed_uri.scheme not in {"source", "artifact", "https", "s3"}:
        errors.append("invalid uri scheme")
    if (
        parsed_uri.username
        or parsed_uri.password
        or parsed_uri.query
        or parsed_uri.fragment
        or any(ord(character) < 32 for character in uri)
    ):
        errors.append("unsafe uri")
    immutability = row.get("immutability")
    if not isinstance(immutability, Mapping):
        errors.append("missing immutability")
    else:
        if immutability.get("content_addressed") is not True:
            errors.append("immutability must be content addressed")
        if immutability.get("identity") != "sha256:{}".format(sha256):
            errors.append("immutability identity mismatch")
    restore = row.get("restore")
    if not isinstance(restore, Mapping):
        errors.append("missing restore")
    else:
        if restore.get("mode") not in {
            "source-registry-hash-verified",
            "external-uri-hash-verified",
        }:
            errors.append("invalid restore mode")
        if restore.get("network_required") not in {True, False}:
            errors.append("restore network_required must be boolean")
        external = restore.get("mode") == "external-uri-hash-verified"
        if external != bool(restore.get("network_required")):
            errors.append("restore mode/network mismatch")
        if external != (parsed_uri.scheme != "source"):
            errors.append("restore mode/uri mismatch")
    return errors


def _load_policy(root: pathlib.Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(
            (root / "registry/artifact-policy.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema_version": 0, "error": str(exc)}
    return payload if isinstance(payload, Mapping) else {}


def _tracked_artifacts(root: pathlib.Path) -> List[pathlib.Path]:
    if not (root / ".git").exists():
        return sorted(path for path in (root / "artifacts").rglob("*") if path.is_file())
    try:
        result = run_rtk(root, ["git", "ls-files", "artifacts"], timeout=30)
    except (KnowledgeHubError, OSError):
        result = {"stdout": ""}
    tracked = [
        root / line
        for line in result["stdout"].splitlines()
        if line and (root / line).is_file()
    ]
    if tracked:
        return tracked
    return sorted(path for path in (root / "artifacts").rglob("*") if path.is_file())


def _immutable_refs(root: pathlib.Path) -> Dict[str, Any]:
    valid_count = 0
    invalid = []
    legacy_count = 0
    manifests = root / "artifacts/manifests"
    for path in sorted(manifests.rglob("*.jsonl")) if manifests.exists() else []:
        for line_no, row in enumerate(load_jsonl(path), 1):
            if not isinstance(row, Mapping):
                continue
            if row.get("schema_version") == IMMUTABLE_ARTIFACT_REF_SCHEMA:
                row_errors = validate_immutable_artifact_ref(row)
                if row_errors:
                    invalid.append(
                        {
                            "path": str(path.relative_to(root)),
                            "line": line_no,
                            "id": str(row.get("id", "")),
                            "errors": row_errors,
                        }
                    )
                else:
                    valid_count += 1
            elif (
                (row.get("uri") or row.get("artifact_uri"))
                and (row.get("sha256") or row.get("source_sha256"))
                and row.get("size") is not None
            ):
                legacy_count += 1
    return {
        "valid_count": valid_count,
        "invalid_count": len(invalid),
        "invalid": invalid[:20],
        "legacy_reference_count": legacy_count,
        "legacy_policy": "report-only; new producer emits strict v1",
    }


def _artifact_inventory(
    root: pathlib.Path,
    policy: Mapping[str, Any],
) -> Dict[str, Any]:
    tracked_paths = _tracked_artifacts(root)
    total_bytes = sum(path.stat().st_size for path in tracked_paths)
    vault_paths = [
        path for path in tracked_paths if str(path.relative_to(root)).startswith("artifacts/vault/")
    ]
    vault_bytes = sum(path.stat().st_size for path in vault_paths)
    largest = max((path.stat().st_size for path in tracked_paths), default=0)
    allowed_manifest_suffixes = set(
        str(value).lower()
        for value in policy.get("manifest_text_suffixes", [])
    )
    binary_manifests = sorted(
        str(path.relative_to(root))
        for path in tracked_paths
        if str(path.relative_to(root)).startswith("artifacts/manifests/")
        and path.suffix.lower() not in allowed_manifest_suffixes
    )
    symlinks = sorted(
        str(path.relative_to(root))
        for path in (root / "artifacts").rglob("*")
        if path.is_symlink()
    )
    return {
        "paths": tracked_paths,
        "total_bytes": total_bytes,
        "vault_paths": vault_paths,
        "vault_bytes": vault_bytes,
        "largest": largest,
        "binary_manifests": binary_manifests,
        "symlinks": symlinks,
    }


def _growth_snapshot(
    baseline: Mapping[str, Any],
    budget: Mapping[str, Any],
    *,
    file_count: int,
    total_bytes: int,
) -> Dict[str, Any]:
    return {
        "baseline": dict(baseline),
        "tracked_bytes_since_baseline": (
            total_bytes - int(baseline.get("tracked_total_bytes", 0) or 0)
        ),
        "tracked_files_since_baseline": (
            file_count - int(baseline.get("tracked_file_count", 0) or 0)
        ),
        "annual_growth_max_bytes": int(
            budget.get("annual_growth_max_bytes", 0) or 0
        ),
    }


def _capacity_checks(
    budget: Mapping[str, Any],
    baseline: Mapping[str, Any],
    *,
    file_count: int,
    total_bytes: int,
    vault_bytes: int,
    largest: int,
) -> tuple[tuple[str, int, int], ...]:
    return (
        ("tracked-file-count", file_count, int(budget.get("tracked_max_files", 0) or 0)),
        ("tracked-total-bytes", total_bytes, int(budget.get("tracked_max_bytes", 0) or 0)),
        ("vault-total-bytes", vault_bytes, int(budget.get("vault_max_bytes", 0) or 0)),
        ("single-file-bytes", largest, int(budget.get("single_file_max_bytes", 0) or 0)),
        (
            "annual-growth-bytes",
            max(0, total_bytes - int(baseline.get("tracked_total_bytes", 0) or 0)),
            int(budget.get("annual_growth_max_bytes", 0) or 0),
        ),
    )


def evaluate_artifact_governance(root: pathlib.Path) -> Dict[str, Any]:
    policy = _load_policy(root)
    budget = policy.get("budget", {}) if isinstance(policy, Mapping) else {}
    baseline = policy.get("baseline", {}) if isinstance(policy, Mapping) else {}
    inventory = _artifact_inventory(root, policy)
    tracked_paths = inventory["paths"]
    total_bytes = inventory["total_bytes"]
    vault_paths = inventory["vault_paths"]
    vault_bytes = inventory["vault_bytes"]
    largest = inventory["largest"]
    binary_manifests = inventory["binary_manifests"]
    symlinks = inventory["symlinks"]
    immutable_refs = _immutable_refs(root)
    violations = []
    checks = _capacity_checks(
        budget,
        baseline,
        file_count=len(tracked_paths),
        total_bytes=total_bytes,
        vault_bytes=vault_bytes,
        largest=largest,
    )
    for name, actual, limit in checks:
        if limit <= 0 or actual > limit:
            violations.append({"id": name, "actual": actual, "limit": limit})
    if binary_manifests:
        violations.append(
            {
                "id": "binary-in-manifests",
                "actual": len(binary_manifests),
                "limit": 0,
            }
        )
    if symlinks:
        violations.append({"id": "artifact-symlink", "actual": len(symlinks), "limit": 0})
    if immutable_refs["invalid_count"]:
        violations.append(
            {
                "id": "invalid-immutable-artifact-ref",
                "actual": immutable_refs["invalid_count"],
                "limit": 0,
            }
        )
    errors = []
    if policy.get("schema_version") != 1:
        errors.append("artifact policy schema_version must be 1")
    return {
        "schema_version": 1,
        "status": "pass" if not errors and not violations else "fail",
        "read_only": True,
        "report_only": True,
        "automatic_delete": False,
        "policy": "registry/artifact-policy.json",
        "budget": dict(budget),
        "growth": _growth_snapshot(
            baseline,
            budget,
            file_count=len(tracked_paths),
            total_bytes=total_bytes,
        ),
        "tracked": {
            "file_count": len(tracked_paths),
            "total_bytes": total_bytes,
            "vault_file_count": len(vault_paths),
            "vault_bytes": vault_bytes,
            "largest_file_bytes": largest,
        },
        "binary_manifest_count": len(binary_manifests),
        "binary_manifest_sample": binary_manifests[:20],
        "symlink_count": len(symlinks),
        "symlink_sample": symlinks[:20],
        "immutable_refs": immutable_refs,
        "violation_count": len(violations),
        "violations": violations,
        "errors": errors,
    }
