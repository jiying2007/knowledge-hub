"""JSON Schema catalog and instance validation."""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

from .common import KnowledgeHubError, load_json, load_jsonl, normalize_relpath


def _error_path(error: Any) -> str:
    path = "$"
    for part in error.absolute_path:
        path += "[{}]".format(part) if isinstance(part, int) else ".{}".format(part)
    return path


def _load_catalog_schemas(
    root: pathlib.Path,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    catalog = load_json(root / "schemas/catalog.json", {}) or {}
    errors: List[str] = []
    rows = catalog.get("contracts", [])
    if not isinstance(rows, list) or not rows:
        errors.append("catalog contracts must be a non-empty array")
        rows = []
    seen: Set[str] = set()
    schemas: Dict[str, Dict[str, Any]] = {}
    validated: List[Dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append("contract {} must be an object".format(index))
            continue
        contract_id = str(row.get("id", ""))
        schema_path = str(row.get("schema", ""))
        if not contract_id:
            errors.append("contract {} missing id".format(index))
            continue
        if contract_id in seen:
            errors.append("duplicate contract id {}".format(contract_id))
            continue
        seen.add(contract_id)
        try:
            relative = normalize_relpath(schema_path)
        except KnowledgeHubError as exc:
            errors.append("{}: {}".format(contract_id, exc))
            continue
        schema_file = root / relative
        if not schema_file.is_file():
            errors.append("{} schema missing: {}".format(contract_id, relative))
            continue
        schema = load_json(schema_file, {}) or {}
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            errors.append("{} must declare JSON Schema 2020-12".format(contract_id))
        if not schema.get("$id") or not schema.get("title"):
            errors.append("{} schema must define $id and title".format(contract_id))
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append("{} invalid schema: {}".format(contract_id, exc.message))
            continue
        schemas[contract_id] = schema
        validated.append(
            {
                "id": contract_id,
                "schema": relative,
                "applies_to": row.get("applies_to", ""),
            }
        )
    return catalog, schemas, validated, errors


def _validate_payload(schema: Mapping[str, Any], payload: Any) -> List[Dict[str, str]]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        {"path": _error_path(error), "message": error.message}
        for error in sorted(
            validator.iter_errors(payload),
            key=lambda row: (list(row.absolute_path), row.message),
        )
    ]


def _load_contract_schema(
    root: pathlib.Path,
    contract_id: str,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Resolve one runtime contract without revalidating every catalog schema.

    Full catalog integrity remains the responsibility of
    :func:`validate_schema_catalog`. Runtime producers only need the selected
    public contract; loading and checking all contracts on every search added a
    large fixed cost and amplified concurrent CLI latency.
    """

    catalog = load_json(root / "schemas/catalog.json", {}) or {}
    rows = catalog.get("contracts", [])
    if not isinstance(rows, list) or not rows:
        return None, ["catalog contracts must be a non-empty array"]

    errors: List[str] = []
    seen: Set[str] = set()
    selected: Optional[Mapping[str, Any]] = None
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            errors.append("contract {} must be an object".format(index))
            continue
        row_id = str(row.get("id", ""))
        if not row_id:
            errors.append("contract {} missing id".format(index))
            continue
        if row_id in seen:
            errors.append("duplicate contract id {}".format(row_id))
            continue
        seen.add(row_id)
        if row_id == contract_id:
            selected = row

    if errors:
        return None, errors
    if selected is None:
        return None, ["unknown contract id"]

    try:
        relative = normalize_relpath(str(selected.get("schema", "")))
    except KnowledgeHubError as exc:
        return None, ["{}: {}".format(contract_id, exc)]
    schema_file = root / relative
    if not schema_file.is_file():
        return None, ["{} schema missing: {}".format(contract_id, relative)]
    schema = load_json(schema_file, {}) or {}
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("{} must declare JSON Schema 2020-12".format(contract_id))
    if not schema.get("$id") or not schema.get("title"):
        errors.append("{} schema must define $id and title".format(contract_id))
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        errors.append("{} invalid schema: {}".format(contract_id, exc.message))
    return (schema if not errors else None), errors


def validate_instance(
    root: pathlib.Path,
    contract_id: str,
    payload: Any,
) -> Dict[str, Any]:
    schema, catalog_errors = _load_contract_schema(root, contract_id)
    if catalog_errors:
        return {
            "status": "fail",
            "contract_id": contract_id,
            "error_count": len(catalog_errors),
            "errors": [{"path": "$catalog", "message": row} for row in catalog_errors],
        }
    if schema is None:
        return {
            "status": "fail",
            "contract_id": contract_id,
            "error_count": 1,
            "errors": [{"path": "$catalog", "message": "unknown contract id"}],
        }
    errors = _validate_payload(schema, payload)
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "error_count": len(errors),
        "errors": errors,
    }


def _static_registry_instances(
    root: pathlib.Path,
) -> Iterable[Tuple[str, str, Any]]:
    contracts = (
        ("command-surface-v1", "registry/command-surface.json"),
        ("engineering-budgets-v1", "registry/engineering-budgets.json"),
        ("artifact-policy-v1", "registry/artifact-policy.json"),
        ("ai-operations-policy-v1", "registry/ai-operations-policy.json"),
        ("contract-compatibility-v1", "registry/contract-compatibility.json"),
        ("review-risk-policy-v1", "registry/review-risk-policy.json"),
    )
    for contract_id, relative in contracts:
        path = root / relative
        if path.is_file():
            yield contract_id, relative, load_json(path, {})
    body_coverage = root / "registry/body-coverage.json"
    if body_coverage.is_file():
        yield (
            "body-coverage-v2",
            "registry/body-coverage.json",
            load_json(body_coverage, {}),
        )


def _registry_item_instances(
    root: pathlib.Path,
) -> Iterable[Tuple[str, str, Any]]:
    for index, row in enumerate(load_jsonl(root / "registry/items.jsonl"), 1):
        source = "registry/items.jsonl:{}".format(index)
        yield "registry-item-v1", source, row
        if row.get("agent_contract"):
            yield (
                "agent-contract-v1",
                source + "#agent_contract",
                row["agent_contract"],
            )
        if row.get("evidence_contract"):
            yield (
                "project-evidence-contract-v1",
                source + "#evidence_contract",
                row["evidence_contract"],
            )


def _registry_jsonl_instances(
    root: pathlib.Path,
) -> Iterable[Tuple[str, str, Any]]:
    rows = (
        ("authorization-v1", "registry/authorizations.jsonl"),
        ("lifecycle-event-v1", "registry/lifecycle-events.jsonl"),
        ("durable-evidence-record-v1", "registry/durable-evidence-ledger.jsonl"),
    )
    for contract_id, relative in rows:
        for index, row in enumerate(load_jsonl(root / relative), 1):
            yield contract_id, "{}:{}".format(relative, index), row


def _manifest_instances(
    root: pathlib.Path,
) -> Iterable[Tuple[str, str, Any]]:
    manifests = root / "artifacts/manifests"
    paths = sorted(manifests.rglob("*.jsonl")) if manifests.exists() else []
    for path in paths:
        for index, row in enumerate(load_jsonl(path), 1):
            if (
                row.get("schema_version")
                == "knowledge-hub.immutable-artifact-ref.v1"
            ):
                yield (
                    "immutable-artifact-ref-v1",
                    "{}:{}".format(path.relative_to(root), index),
                    row,
                )


def _optional_static_instances(
    root: pathlib.Path,
) -> Iterable[Tuple[str, str, Any]]:
    rows = (
        ("local-workspaces-v1", "local/workspaces.json"),
        ("agent-review-policy-v1", "registry/agent-review-policy.json"),
        ("product-policy-v1", "registry/product-policy.json"),
    )
    for contract_id, relative in rows:
        path = root / relative
        if path.is_file():
            yield contract_id, relative, load_json(path, {})


def _static_instances(
    root: pathlib.Path,
) -> Iterable[Tuple[str, str, Any]]:
    for row in _static_registry_instances(root):
        yield row
    for row in _registry_item_instances(root):
        yield row
    for row in _registry_jsonl_instances(root):
        yield row
    for row in _manifest_instances(root):
        yield row
    for row in _optional_static_instances(root):
        yield row

def validate_schema_catalog(root: pathlib.Path) -> Dict[str, Any]:
    catalog, schemas, validated, errors = _load_catalog_schemas(root)
    instance_errors: List[Dict[str, str]] = []
    instance_count = 0
    if not errors:
        for contract_id, source, payload in _static_instances(root):
            instance_count += 1
            schema = schemas.get(contract_id)
            if schema is None:
                instance_errors.append(
                    {
                        "contract_id": contract_id,
                        "source": source,
                        "path": "$catalog",
                        "message": "contract schema is unavailable",
                    }
                )
                continue
            for row in _validate_payload(schema, payload):
                instance_errors.append(
                    {
                        "contract_id": contract_id,
                        "source": source,
                        "path": row["path"],
                        "message": row["message"],
                    }
                )
    split = catalog.get("authority_split", {})
    registry_fields = set(split.get("registry", [])) if isinstance(split, dict) else set()
    markdown_fields = set(split.get("markdown", [])) if isinstance(split, dict) else set()
    overlap = sorted(registry_fields & markdown_fields)
    if overlap:
        errors.append("authority split overlaps fields: {}".format(", ".join(overlap)))
    if not isinstance(split, dict) or not split.get("mirror_rule"):
        errors.append("authority_split.mirror_rule is required")
    errors.extend(
        "{source} {path}: {message}".format(**row)
        for row in instance_errors[:100]
    )
    return {
        "status": "pass" if not errors else "fail",
        "catalog": "schemas/catalog.json",
        "contract_count": len(catalog.get("contracts", [])),
        "validated_count": len(validated),
        "contracts": validated,
        "authority_overlap": overlap,
        "instance_validation": {
            "status": "pass" if not instance_errors else "fail",
            "instance_count": instance_count,
            "error_count": len(instance_errors),
            "errors": instance_errors[:100],
        },
        "errors": errors,
    }
