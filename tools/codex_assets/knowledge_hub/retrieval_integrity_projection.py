"""Benchmark integrity projection; preserves counts, rates and status gates."""

from typing import Any, Dict


def benchmark_integrity(result_count, unregistered_result_count, control_result_count,
                        duplicate_result_count, compatibility_hit_count, internal_endpoint_exposure_count,
                        forbidden_hit_count, zero_hit_failure_count):
    integrity: Dict[str, Any] = {
        "result_count": result_count,
        "unregistered_result_count": unregistered_result_count,
        "unregistered_result_rate": round(
            unregistered_result_count / result_count if result_count else 0.0,
            4,
        ),
        "control_result_count": control_result_count,
        "control_result_rate": round(
            control_result_count / result_count if result_count else 0.0,
            4,
        ),
        "duplicate_result_count": duplicate_result_count,
        "duplicate_result_rate": round(
            duplicate_result_count / result_count if result_count else 0.0,
            4,
        ),
        "compatibility_hit_count": compatibility_hit_count,
        "internal_endpoint_exposure_count": internal_endpoint_exposure_count,
        "forbidden_hit_count": forbidden_hit_count,
        "zero_hit_failure_count": zero_hit_failure_count,
    }
    integrity["status"] = (
        "pass"
        if all(
            integrity[key] == 0
            for key in (
                "unregistered_result_count",
                "control_result_count",
                "duplicate_result_count",
                "compatibility_hit_count",
                "internal_endpoint_exposure_count",
                "forbidden_hit_count",
                "zero_hit_failure_count",
            )
        )
        else "fail"
    )
    return integrity
