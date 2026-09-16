"""Read-only Operator projection for observed governed binding lifecycle artifacts."""

from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .common import KnowledgeHubError
from .operator_binding_apply_receipt import build_governed_apply_receipt
from .operator_binding_rollback_receipt import build_governed_rollback_receipt

LIFECYCLE_PROJECTION = "knowledge-operator-binding-lifecycle-v1"
PROPOSAL_PROJECTION = "knowledge-operator-binding-proposal-v1"
REVIEW_PROJECTION = "knowledge-operator-binding-review-bundle-v1"
AUTHORIZATION_PROJECTION = "knowledge-operator-binding-authorization-v1"
APPLY_PROJECTION = "knowledge-operator-binding-governed-apply-v1"
ROLLBACK_PROJECTION = "knowledge-operator-binding-governed-rollback-v1"

_INPUT_ORDER = (
    "proposal",
    "review_bundle",
    "authorization",
    "apply",
    "rollback",
)
_EXPECTED_PROJECTIONS = {
    "proposal": PROPOSAL_PROJECTION,
    "review_bundle": REVIEW_PROJECTION,
    "authorization": AUTHORIZATION_PROJECTION,
    "apply": APPLY_PROJECTION,
    "rollback": ROLLBACK_PROJECTION,
}


def _load_json_object(root: pathlib.Path, value: str, label: str) -> Mapping[str, Any]:
    path = pathlib.Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KnowledgeHubError(
            "cannot load {} lifecycle JSON {}: {}".format(label, path, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise KnowledgeHubError("{} lifecycle JSON must be an object".format(label))
    return payload


def _observed_contract_reasons(stage: str, payload: Mapping[str, Any]) -> List[str]:
    reasons: List[str] = []
    if payload.get("schema_version") != 1:
        reasons.append("{}-schema-version-invalid".format(stage))
    if str(payload.get("projection", "")) != _EXPECTED_PROJECTIONS[stage]:
        reasons.append("{}-projection-invalid".format(stage))
    if payload.get("automatic_execution_enabled") is not False:
        reasons.append("{}-automatic-execution-boundary-invalid".format(stage))
    if stage in {"proposal", "review_bundle", "authorization"}:
        if payload.get("read_only") is not True:
            reasons.append("{}-read-only-boundary-invalid".format(stage))
        if payload.get("canonical_write_performed") is not False:
            reasons.append("{}-canonical-write-boundary-invalid".format(stage))
        if payload.get("automatic_binding_enabled") is not False:
            reasons.append("{}-automatic-binding-boundary-invalid".format(stage))
    return reasons


def _stage_row(
    stage: str,
    payload: Mapping[str, Any],
    *,
    trust_state: str,
    status_override: str = "",
    reason_codes: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    source_reasons = payload.get("reason_codes", [])
    if not isinstance(source_reasons, list):
        source_reasons = []
    reasons = list(reason_codes) if reason_codes is not None else source_reasons[:10]
    return {
        "stage": stage,
        "observed": True,
        "projection": str(payload.get("projection", "")),
        "source_status": str(payload.get("status", "")),
        "status": status_override or str(payload.get("status", "")),
        "trust_state": trust_state,
        "reason_codes": [str(value) for value in reasons if str(value)][:10],
    }


def _next_responsibility(stage: str, status: str) -> Tuple[str, str]:
    if stage == "proposal":
        if status == "needs-governed-review":
            return "governance-review", "审核 proposal 与 canonical target；不得自动绑定 evidence。"
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 proposal 上游 contract/冲突后再继续。"
    if stage == "review_bundle":
        if status == "needs-governed-authorization":
            return "human-authorization", "由真实 owner 提供显式 binding authorization；UI 不生成授权。"
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 review bundle/patch plan 一致性后再继续。"
    if stage == "authorization":
        if status == "ready-for-governed-apply":
            return (
                "human-authorization",
                "通过独立 apply CLI 重新验证完整链并显式确认 fingerprint、registry SHA 与身份边界。",
            )
        if status in {"blocked", "upstream-error"}:
            return "governance-review", "审计 authorization contract/owner coverage 后再继续。"
    if stage == "apply":
        if status in {"post-apply-state-drift", "blocked"}:
            return "governance-review", "审计 apply receipt 或当前 registry drift；不得覆盖现状。"
    if stage == "rollback":
        if status == "ready-for-governed-rollback":
            return (
                "human-authorization",
                "通过独立 rollback CLI 显式确认 receipt、authorization fingerprint、当前 SHA 与身份边界。",
            )
        if status in {"post-rollback-state-drift", "blocked"}:
            return "governance-review", "审计 rollback receipt 或当前 registry drift；不得自动 reapply。"
    return "", ""


def _observation_error(
    stages: Sequence[Mapping[str, Any]],
    reasons: Sequence[str],
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": LIFECYCLE_PROJECTION,
        "status": "observation-error",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "observed_stage_count": len(stages),
        "current_stage": str(stages[-1].get("stage", "")) if stages else "",
        "trust_state": "fail-closed-observation",
        "next_execution_class": "governance-review",
        "next_summary_zh": "生命周期观测输入无法安全解释；先审计保存的 JSON/链路，不执行 apply 或 rollback。",
        "stages": [dict(row) for row in stages],
        "reason_codes": list(dict.fromkeys(str(value) for value in reasons if str(value)))[:20],
    }


def _not_observed() -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "projection": LIFECYCLE_PROJECTION,
        "status": "not-observed",
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "observed_stage_count": 0,
        "current_stage": "",
        "trust_state": "not-observed",
        "next_execution_class": "",
        "next_summary_zh": "",
        "stages": [],
        "reason_codes": ["no-explicit-lifecycle-observation-input"],
    }


def _load_inputs(
    root: pathlib.Path,
    inputs: Mapping[str, str],
) -> Tuple[Dict[str, Mapping[str, Any]], List[Dict[str, Any]], List[str]]:
    payloads: Dict[str, Mapping[str, Any]] = {}
    stages: List[Dict[str, Any]] = []
    reasons: List[str] = []
    for stage in _INPUT_ORDER:
        value = str(inputs.get(stage, "")).strip()
        if not value:
            continue
        try:
            payload = _load_json_object(root, value, stage)
        except KnowledgeHubError as exc:
            reasons.append("{}-input-unavailable:{}".format(stage, exc))
            continue
        payloads[stage] = payload
        contract_reasons = _observed_contract_reasons(stage, payload)
        stages.append(
            _stage_row(
                stage,
                payload,
                trust_state=(
                    "observed-output-not-revalidated"
                    if not contract_reasons
                    else "contract-invalid"
                ),
                reason_codes=contract_reasons or None,
            )
        )
        reasons.extend(contract_reasons)
    return payloads, stages, reasons


def _revalidate_latest(
    root: pathlib.Path,
    payloads: Mapping[str, Mapping[str, Any]],
    stages: List[Dict[str, Any]],
) -> Tuple[str, str, List[str]]:
    if "rollback" in payloads:
        if "apply" not in payloads:
            return "rollback", "blocked", ["rollback-observation-requires-apply-result"]
        rollback = payloads["rollback"]
        if rollback.get("status") == "rolled-back":
            receipt = build_governed_rollback_receipt(root, payloads["apply"], rollback)
            stages.append(
                _stage_row(
                    "rollback_receipt",
                    receipt,
                    trust_state="revalidated-by-rollback-receipt",
                )
            )
            return "rollback", str(receipt.get("status", "blocked")), []
        return "rollback", str(rollback.get("status", "")), []
    if "apply" in payloads:
        apply_payload = payloads["apply"]
        if apply_payload.get("status") == "applied":
            receipt = build_governed_apply_receipt(root, apply_payload)
            stages.append(
                _stage_row(
                    "apply_receipt",
                    receipt,
                    trust_state="revalidated-by-apply-receipt",
                )
            )
            return "apply", str(receipt.get("status", "blocked")), []
        return "apply", str(apply_payload.get("status", "")), []
    for stage in reversed(_INPUT_ORDER[:3]):
        if stage in payloads:
            return stage, str(payloads[stage].get("status", "")), []
    return "", "not-observed", []


def build_binding_lifecycle_projection(
    root: pathlib.Path,
    inputs: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """Project explicitly supplied lifecycle outputs without executing any lifecycle action."""

    normalized = {
        str(key): str(value)
        for key, value in (inputs or {}).items()
        if str(value).strip()
    }
    if not normalized:
        return _not_observed()
    payloads, stages, reasons = _load_inputs(root, normalized)
    if reasons:
        return _observation_error(stages, reasons)
    current_stage, status, revalidation_reasons = _revalidate_latest(
        root, payloads, stages
    )
    if revalidation_reasons:
        return _observation_error(stages, revalidation_reasons)
    execution_class, summary = _next_responsibility(current_stage, status)
    trust_state = str(stages[-1].get("trust_state", "")) if stages else "not-observed"
    return {
        "schema_version": 1,
        "projection": LIFECYCLE_PROJECTION,
        "status": status,
        "read_only": True,
        "network_performed": False,
        "canonical_write_performed": False,
        "automatic_binding_enabled": False,
        "automatic_execution_enabled": False,
        "observed_stage_count": len(stages),
        "current_stage": current_stage,
        "trust_state": trust_state,
        "next_execution_class": execution_class,
        "next_summary_zh": summary,
        "stages": stages,
        "reason_codes": [],
    }
