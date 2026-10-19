"""Single SHA-bound unfilled-body predicate for audit and ordinary retrieval.

Does not approve, edit, or change ownership of any Knowledge Hub document.
Hash is over exact stripped body text, *not* the registry summary/title.
"""
from __future__ import annotations

from typing import Any

UNFILLED_TEMPLATE_BODY_SHA256 = {
    "debug-record": "0ce0544666f87ebc77160928058f3db9e43ef4c3733491b0f54e61744abcae90",
    "validation": "adcfb01659087381a2b96473bcfa32bf32c097c82379feaacefa76320936059d",
    "decision": "0795d90035702f6a5c18fd62a77d102f1727d650b0baabe0e6efaff501986d90",
}


def is_registered_unfilled_template(kind: Any, status: Any, body_sha256: Any) -> bool:
    """Fail conservatively: a known exact template is never proof of a claim."""
    if not isinstance(kind, str) or status not in {"reviewing", "active"}:
        return False
    expected = UNFILLED_TEMPLATE_BODY_SHA256.get(kind)
    return bool(expected and type(body_sha256) is str and body_sha256 == expected)
