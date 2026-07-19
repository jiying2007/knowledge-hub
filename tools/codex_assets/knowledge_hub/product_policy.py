"""Validated manifest-driven product and project-readiness policy."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, load_json, normalize_relpath
from .schemas import validate_instance


PRODUCT_POLICY_PATH = "registry/product-policy.json"


def load_product_policy(root: pathlib.Path) -> Tuple[Dict[str, Any], List[str]]:
    payload = load_json(root / PRODUCT_POLICY_PATH, {}) or {}
    validation = validate_instance(root, "product-policy-v1", payload)
    errors = [
        "{}: {}".format(row.get("path", "$"), row.get("message", "invalid policy"))
        for row in validation.get("errors", [])
    ]
    return payload, errors


def readiness_extensions_by_project(
    policy: Mapping[str, Any], project_ids: Sequence[str]
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    known = set(str(value) for value in project_ids)
    result: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    seen_extension_ids = set()
    for extension in policy.get("project_readiness_extensions", []):
        extension_id = str(extension.get("id", ""))
        if extension_id in seen_extension_ids:
            errors.append("duplicate project readiness extension id: {}".format(extension_id))
        seen_extension_ids.add(extension_id)
        for project_id in extension.get("project_ids", []):
            project_id = str(project_id)
            if project_id not in known:
                errors.append(
                    "project readiness extension {} references missing project {}".format(
                        extension_id, project_id
                    )
                )
                continue
            row = result.setdefault(
                project_id,
                {"validation_expectations_zh": [], "related_links": [], "policy_ids": []},
            )
            row["policy_ids"].append(extension_id)
            row["validation_expectations_zh"].extend(
                str(value) for value in extension.get("validation_expectations_zh", [])
            )
            for link in extension.get("related_links", []):
                try:
                    safe_path = normalize_relpath(str(link.get("path", "")))
                except KnowledgeHubError as exc:
                    errors.append(
                        "project readiness extension {} has unsafe related link: {}".format(
                            extension_id, str(exc)
                        )
                    )
                    continue
                row["related_links"].append(
                    {"path": safe_path, "label_zh": str(link.get("label_zh", ""))}
                )
    return result, errors


def evaluate_specialized_owner_requirements(
    policy: Mapping[str, Any], items_by_id: Mapping[str, Mapping[str, Any]]
) -> Dict[str, Any]:
    rows: Dict[str, Dict[str, Any]] = {}
    policy_rows: List[Dict[str, Any]] = []
    ready_ids: List[str] = []
    pending_ids: List[str] = []
    errors: List[str] = []
    seen_policy_ids = set()
    seen_item_ids = set()
    for requirement in policy.get("specialized_owner_requirements", []):
        policy_id = str(requirement.get("id", ""))
        if policy_id in seen_policy_ids:
            errors.append("duplicate specialized owner policy id: {}".format(policy_id))
        seen_policy_ids.add(policy_id)
        policy_item_ids: List[str] = []
        for item_requirement in requirement.get("item_requirements", []):
            item_id = str(item_requirement.get("item_id", ""))
            policy_item_ids.append(item_id)
            if item_id in seen_item_ids:
                errors.append("duplicate specialized owner item requirement: {}".format(item_id))
            seen_item_ids.add(item_id)
            expected = dict(item_requirement.get("expected", {}))
            item = items_by_id.get(item_id, {})
            if not item:
                errors.append(
                    "specialized owner policy {} references missing item {}".format(
                        policy_id, item_id
                    )
                )
            mismatches = [
                field for field, expected_value in expected.items()
                if item.get(field) != expected_value
            ]
            ready = bool(item) and not mismatches
            row = {
                "policy_id": policy_id,
                "status": item.get("status", "missing"),
                "path": item.get("path", ""),
                "expected": expected,
                "actual": {field: item.get(field) for field in expected},
                "mismatch_fields": mismatches,
                "owner_ready": ready,
                "manual_validation_pending": item.get("manual_validation_pending", True),
            }
            rows[item_id] = row
            (ready_ids if ready else pending_ids).append(item_id)
        policy_rows.append(
            {
                "policy_id": policy_id,
                "label_zh": requirement.get("label_zh", ""),
                "item_ids": policy_item_ids,
                "ready": all(rows[item_id]["owner_ready"] for item_id in policy_item_ids),
            }
        )
    return {
        "status": "fail" if errors else "pass",
        "errors": errors,
        "policy_count": len(policy_rows),
        "policies": policy_rows,
        "item_count": len(rows),
        "items": rows,
        "ready_ids": sorted(ready_ids),
        "pending_ids": sorted(pending_ids),
        "required_evidence_zh": list(policy.get("specialized_required_evidence_zh", [])),
        "evidence_priority_messages_zh": list(policy.get("evidence_priority_messages_zh", [])),
    }
