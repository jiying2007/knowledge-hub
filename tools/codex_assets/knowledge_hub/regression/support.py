"""Stable regression support facade for generated case modules."""

from .support_fixtures import *  # noqa: F401,F403
from .support_runtime import *  # noqa: F401,F403


_base_expect = expect


def expect(condition, *args, **kwargs):
    """Add bounded diagnostics for the one drifting full-gate contract."""
    positional = list(args)
    result_id = positional[0] if positional else kwargs.get("result_id", "")
    detail = positional[2] if len(positional) >= 3 else kwargs.get("detail")
    if (
        not condition
        and result_id == "final-gate-default-regression-path"
        and isinstance(detail, dict)
    ):
        regression = detail.get("regression", {})
        delivery = detail.get("delivery_readiness", {})
        hard_checks = detail.get("hard_checks", {})
        detail = dict(detail)
        detail["predicate_probe"] = {
            "exit_code_zero": detail.get("exit_code") == 0,
            "status": detail.get("status"),
            "regression_status_pass": regression.get("status") == "pass",
            "full_regression_executed": regression.get("full_regression_executed") is True,
            "result_count_one": regression.get("result_count") == 1,
            "command_uses_full_summary": "--summary-json --suite full --as-of "
            in regression.get("command", ""),
            "hard_check_full_regression": hard_checks.get("full_regression") is True,
            "delivery_full_regression_ready": delivery.get("full_regression_ready") is True,
            "false_hard_checks": sorted(
                key for key, value in hard_checks.items() if value is not True
            ),
            "platform_blockers": list(detail.get("blockers", [])),
        }
        if len(positional) >= 3:
            positional[2] = detail
        else:
            kwargs["detail"] = detail
    return _base_expect(condition, *positional, **kwargs)
