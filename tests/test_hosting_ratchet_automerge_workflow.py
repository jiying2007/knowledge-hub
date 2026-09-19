from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/hosting-ratchet-automerge.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_hosting_ratchet_automerge_runs_only_after_successful_quality():
    payload = _workflow()
    assert set(payload["on"]) == {"workflow_run"}
    trigger = payload["on"]["workflow_run"]
    assert trigger["workflows"] == ["quality"]
    assert trigger["types"] == ["completed"]

    job = payload["jobs"]["merge"]
    condition = job["if"]
    assert "workflow_run.conclusion == 'success'" in condition
    assert "workflow_run.event == 'pull_request'" in condition
    assert "workflow_run.head_repository.full_name == github.repository" in condition
    assert "automation/hosting-private-" in condition


def test_hosting_ratchet_automerge_never_executes_pr_code():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/checkout" not in text
    assert "git checkout" not in text
    assert "pip install" not in text
    assert "run-mcp-conformance" not in text
    assert "pull_request_target" not in text


def test_hosting_ratchet_automerge_requires_protected_exact_current_master():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'master.get("protected") is not True' in text
    assert "ratchet head must be a direct child of current master" in text
    assert "master protection or source revision changed after ratchet validation" in text
    assert "pull request moved after validation" in text


def test_hosting_ratchet_automerge_has_two_file_and_semantic_allowlists():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "ratchet pull request must change exactly two files" in text
    assert "registry/knowledge-platform-p5-p10.json" in text
    assert "registry/durable-evidence-ledger.jsonl" in text
    assert "candidate registry changed fields outside repository-private-boundary" in text
    assert "ratchet must append exactly one durable evidence record" in text
    assert "durable candidate digest does not match exact registry bytes" in text


def test_hosting_ratchet_automerge_uses_expected_head_squash_and_branch_gc():
    payload = _workflow()
    assert payload["permissions"] == {"contents": "read"}
    job = payload["jobs"]["merge"]
    assert job["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
        "actions": "read",
    }

    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'pulls/${PR_NUMBER}/merge' in text
    assert '-f sha="${HEAD_SHA}"' in text
    assert '-f merge_method="squash"' in text
    assert "--method DELETE" in text
    assert "git push" not in text


def test_hosting_ratchet_automerge_matches_machine_policy_guardrails():
    import json

    policy = json.loads(
        Path("registry/ai-operations-policy.json").read_text(encoding="utf-8")
    )
    guardrails = policy["guardrails"]
    assert guardrails["automatic_merge_requires_protected_branch"] is True
    assert guardrails["automatic_merge_requires_exact_head_quality"] is True
    assert guardrails["automatic_merge_requires_same_repository"] is True
    assert guardrails["automatic_merge_requires_semantic_allowlist"] is True
    assert guardrails["automatic_merge_requires_trusted_origin_run"] is True
    assert guardrails["automatic_merge_executes_pr_code"] is False

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_run.conclusion == 'success'" in text
    assert "workflow_run.head_repository.full_name == github.repository" in text
    assert "master must be protected before autonomous ratchet merge" in text
    assert "changed paths outside the bounded allowlist" in text
    assert "actions/checkout" not in text


def test_hosting_ratchet_automerge_revalidates_live_private_and_trusted_origin():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "live repository is not private at merge time" in text
    assert "Revalidate trusted reconciliation origin" in text
    assert '"name": "hosting-posture-reconcile"' in text
    assert '"path": ".github/workflows/hosting-posture-reconcile.yml"' in text
    assert 'run.get("event") not in {"schedule", "workflow_dispatch"}' in text
    assert "reconciliation origin repository identity mismatch" in text


def test_hosting_ratchet_automerge_declares_actions_read_for_trigger_revalidation():
    payload = _workflow()
    job = payload["jobs"]["merge"]
    assert job["permissions"]["actions"] == "read"
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'actions/runs/${TRIGGER_RUN_ID}' in text


def test_hosting_ratchet_automerge_requires_deterministic_generator_branch_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "^automation/hosting-private-[0-9a-f]{12}-[0-9]+$" in text
    assert '"automation/hosting-private-{}-{}".format(' in text
    assert "ratchet branch identity does not match trusted generator run" in text


def test_hosting_ratchet_automerge_revalidates_exact_reconcile_attempt():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert (
        'actions/runs/${RECONCILE_RUN_ID}/attempts/${RECONCILE_RUN_ATTEMPT}'
        in text
    )
    assert '"run_attempt": int(os.environ["RECONCILE_RUN_ATTEMPT"])' in text
