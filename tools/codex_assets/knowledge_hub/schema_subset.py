"""Fail-closed lightweight JSON Schema subset for interactive hot paths.

The full Draft 2020-12 validator remains authoritative in engineering and
schema gates. Interactive producers may use this evaluator only for contracts
whose keywords are entirely covered here; an unknown keyword is an error.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Mapping, Sequence

from .common import KnowledgeHubError, load_json, normalize_relpath


_ANNOTATION_KEYWORDS = {
    "$schema",
    "$id",
    "title",
    "description",
    "default",
}
_VALIDATION_KEYWORDS = {
    "type",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "const",
    "enum",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
}
_SUPPORTED_KEYWORDS = _ANNOTATION_KEYWORDS | _VALIDATION_KEYWORDS


def _schema_keyword_errors(
    schema: Mapping[str, Any],
    path: str = "$schema",
) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    for keyword in schema:
        if keyword not in _SUPPORTED_KEYWORDS:
            errors.append(
                {
                    "path": path,
                    "message": "unsupported schema keyword {}".format(keyword),
                }
            )
    properties = schema.get("properties", {})
    if isinstance(properties, Mapping):
        for key, child in properties.items():
            if isinstance(child, Mapping):
                errors.extend(
                    _schema_keyword_errors(
                        child,
                        "{}.properties.{}".format(path, key),
                    )
                )
    items = schema.get("items")
    if isinstance(items, Mapping):
        errors.extend(_schema_keyword_errors(items, "{}.items".format(path)))
    additional = schema.get("additionalProperties")
    if isinstance(additional, Mapping):
        errors.extend(
            _schema_keyword_errors(
                additional,
                "{}.additionalProperties".format(path),
            )
        )
    return errors


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _validate_common_constraints(
    schema: Mapping[str, Any],
    value: Any,
    path: str,
) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append({"path": path, "message": "value does not match const"})
    enum = schema.get("enum")
    if isinstance(enum, list) and not any(_json_equal(value, row) for row in enum):
        errors.append({"path": path, "message": "value is not in enum"})
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append({"path": path, "message": "value is below minimum"})
        if "maximum" in schema and value > schema["maximum"]:
            errors.append({"path": path, "message": "value is above maximum"})
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append({"path": path, "message": "string is too short"})
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append({"path": path, "message": "string is too long"})
    return errors


def _validate_array(
    schema: Mapping[str, Any],
    value: List[Any],
    path: str,
) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    if "minItems" in schema and len(value) < schema["minItems"]:
        errors.append({"path": path, "message": "array has too few items"})
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        errors.append({"path": path, "message": "array has too many items"})
    items = schema.get("items")
    if isinstance(items, Mapping):
        for index, row in enumerate(value):
            errors.extend(_validate_value(items, row, "{}[{}]".format(path, index)))
    return errors


def _validate_object(
    schema: Mapping[str, Any],
    value: Mapping[str, Any],
    path: str,
) -> List[Dict[str, str]]:
    errors: List[Dict[str, str]] = []
    required = schema.get("required", [])
    if isinstance(required, list):
        for key in required:
            if key not in value:
                errors.append(
                    {
                        "path": path,
                        "message": "missing required property {}".format(key),
                    }
                )
    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        return errors
    for key, child in properties.items():
        if key in value and isinstance(child, Mapping):
            errors.extend(
                _validate_value(child, value[key], "{}.{}".format(path, key))
            )
    additional = schema.get("additionalProperties", True)
    for key in value:
        if key in properties:
            continue
        if additional is False:
            errors.append(
                {
                    "path": path,
                    "message": "additional property {} is not allowed".format(key),
                }
            )
        elif isinstance(additional, Mapping):
            errors.extend(
                _validate_value(
                    additional,
                    value[key],
                    "{}.{}".format(path, key),
                )
            )
    return errors


def _validate_value(
    schema: Mapping[str, Any],
    value: Any,
    path: str,
) -> List[Dict[str, str]]:
    expected = schema.get("type")
    expected_types: Sequence[str] = (
        [expected] if isinstance(expected, str) else expected or []
    )
    if expected_types and not any(
        _matches_type(value, candidate) for candidate in expected_types
    ):
        return [
            {
                "path": path,
                "message": "expected type {}".format("|".join(expected_types)),
            }
        ]
    errors = _validate_common_constraints(schema, value, path)
    if isinstance(value, list):
        errors.extend(_validate_array(schema, value, path))
    if isinstance(value, Mapping):
        errors.extend(_validate_object(schema, value, path))
    return errors


def validate_contract_subset(
    root: pathlib.Path,
    contract_id: str,
    payload: Any,
) -> Dict[str, Any]:
    """Validate one catalog contract with the supported fail-closed subset."""

    catalog = load_json(root / "schemas/catalog.json", {}) or {}
    rows = catalog.get("contracts", [])
    if not isinstance(rows, list):
        rows = []
    matches = [
        row
        for row in rows
        if isinstance(row, Mapping) and row.get("id") == contract_id
    ]
    catalog_errors: List[Dict[str, str]] = []
    if len(matches) != 1:
        catalog_errors.append(
            {
                "path": "$catalog",
                "message": (
                    "unknown contract id"
                    if not matches
                    else "duplicate contract id"
                ),
            }
        )
    if catalog_errors:
        return {
            "status": "fail",
            "contract_id": contract_id,
            "error_count": len(catalog_errors),
            "errors": catalog_errors,
        }
    try:
        relative = normalize_relpath(str(matches[0].get("schema", "")))
    except KnowledgeHubError as exc:
        errors = [{"path": "$catalog", "message": str(exc)}]
        return {
            "status": "fail",
            "contract_id": contract_id,
            "error_count": 1,
            "errors": errors,
        }
    schema = load_json(root / relative, {}) or {}
    if not isinstance(schema, Mapping):
        schema = {}
    errors = _schema_keyword_errors(schema)
    if not errors:
        errors = _validate_value(schema, payload, "$")
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "error_count": len(errors),
        "errors": errors,
    }
