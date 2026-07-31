"""Shared public status and exit-code contract."""

from __future__ import annotations

from typing import Any, Dict


CANONICAL_STATUSES = ("pass", "needs-review", "needs-fix", "blocked")

STATUS_CONTRACT_VERSION = 2


def canonical_status(value: Any) -> str:
    """Validate the single public status vocabulary without alias fallback."""

    status = str(value or "").strip().lower()
    if status not in CANONICAL_STATUSES:
        raise ValueError(
            "public status must be a canonical status: {}".format(
                ", ".join(CANONICAL_STATUSES)
            )
        )
    return status


def status_contract(
    status: Any,
    *,
    terminal_required: bool = False,
    terminal: bool = False,
) -> Dict[str, Any]:
    """Return the stable status/exit projection used by public JSON CLIs."""

    normalized = canonical_status(status)
    default_exit_code = 0 if normalized in {"pass", "needs-review"} else 1
    if terminal_required and not terminal and default_exit_code == 0:
        default_exit_code = 2
    return {
        "contract_version": STATUS_CONTRACT_VERSION,
        "status": normalized,
        "default_exit_code": default_exit_code,
        "strict_exit_code": 0 if normalized == "pass" else 1,
        "terminal_required": terminal_required,
        "terminal": terminal,
        "semantics": {
            "pass": "technical or requested operation passed",
            "needs-review": "readable result exists but human or external evidence remains",
            "needs-fix": "deterministic validation failed",
            "blocked": "result cannot be evaluated safely",
        },
    }
