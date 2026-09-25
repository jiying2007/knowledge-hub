import yaml
from pathlib import Path


WORKFLOW = Path(".github/workflows/ai-maintenance-sweep.yml")


def _workflow_text():
    return WORKFLOW.read_text(encoding="utf-8")


def _steps():
    payload = yaml.safe_load(_workflow_text())
    return payload["jobs"]["sweep"]["steps"]


def _step(name):
    return next(row for row in _steps() if row.get("name") == name)


def test_decision_uses_canonical_notification_fingerprint_helper():
    run = _step("Build bounded AI maintenance decision")["run"]
    assert "critical_notification_decision" in run
    assert 'notification_fingerprint = notification["notification_fingerprint"]' in run
    assert 'handle.write("notification_fingerprint={}' in run


def test_critical_route_binds_fingerprint_from_decision_output():
    step = _step("Route only critical maintenance to a human")
    assert step["env"]["NOTIFICATION_FINGERPRINT"] == (
        "${{ steps.decision.outputs.notification_fingerprint }}"
    )
    run = step["run"]
    assert "contains(\"${NOTIFICATION_FINGERPRINT}\")" in run
    assert 'if [[ -z "${seen}" ]]' in run
    assert "Critical maintenance state ${NOTIFICATION_FINGERPRINT}" in run


def test_existing_issue_is_only_commented_when_fingerprint_is_new():
    run = _step("Route only critical maintenance to a human")["run"]
    existing = run.index('if [[ -n "${number}" ]]')
    seen = run.index('seen="$(', existing)
    guard = run.index('if [[ -z "${seen}" ]]', seen)
    comment = run.index('gh issue comment "${number}"', guard)
    create = run.index("gh issue create", comment)
    assert existing < seen < guard < comment < create


def test_new_issue_body_contains_state_identity():
    run = _step("Route only critical maintenance to a human")["run"]
    assert 'body="Critical maintenance state ${NOTIFICATION_FINGERPRINT}.' in run


def test_recovery_close_semantics_are_not_relaxed():
    run = _step("Close stale critical maintenance issue when recovered")["run"]
    assert "steps.decision.outputs.human_required == 'false'" in str(
        _step("Close stale critical maintenance issue when recovered").get("if")
    )
    assert "gh issue close" in run
