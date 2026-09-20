from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/quality.yml")
REQUIRED_QUALITY_EVIDENCE = (
    ".tmp/engineering/knowledge-hub.cdx.json",
    ".cache/knowledge-hub/engineering-quality.json",
    ".cache/knowledge-hub/compliance-eval.json",
    ".cache/knowledge-hub/restore-drill-head.json",
    ".cache/knowledge-hub/final-gate-product-full.json",
    ".cache/knowledge-hub/quality-evidence-binding.json",
)


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_quality_runs_for_master_pushes_and_pull_requests_without_duplicate_branch_pushes():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)
    push = triggers.get("push")
    assert isinstance(push, dict)
    assert push.get("branches") == ["master"]
    assert "paths" not in push
    assert "paths-ignore" not in push
    assert "pull_request" in triggers
    assert "workflow_dispatch" in triggers


def test_quality_preserves_every_master_revision():
    payload = _workflow()
    concurrency = payload.get("concurrency")
    assert isinstance(concurrency, dict)
    assert concurrency.get("group") == (
        "quality-${{ github.workflow }}-"
        "${{ github.ref == 'refs/heads/master' && github.sha || github.ref }}"
    )
    assert concurrency.get("cancel-in-progress") == (
        "${{ github.ref != 'refs/heads/master' }}"
    )


def test_quality_still_deduplicates_superseded_non_master_runs():
    payload = _workflow()
    concurrency = payload.get("concurrency")
    assert isinstance(concurrency, dict)
    group = concurrency.get("group")
    cancel = concurrency.get("cancel-in-progress")
    assert "github.sha" in group
    assert "github.ref" in group
    assert "refs/heads/master" in group
    assert "refs/heads/master" in cancel


def test_quality_fails_closed_on_missing_or_empty_evidence():
    payload = _workflow()
    engineering = payload["jobs"]["engineering"]
    steps = engineering["steps"]

    verify = next(step for step in steps if step.get("name") == "Verify required quality evidence")
    assert verify.get("if") == "always()"
    verify_run = verify.get("run", "")
    assert verify_run.startswith("rtk python3 -c ")
    assert "Path(path).is_file()" in verify_run
    assert "Path(path).stat().st_size == 0" in verify_run
    for path in REQUIRED_QUALITY_EVIDENCE:
        assert path in verify_run

    upload = next(step for step in steps if step.get("name") == "Upload quality evidence")
    assert upload.get("if") == "always()"
    upload_with = upload["with"]
    assert upload_with["if-no-files-found"] == "error"
    uploaded = tuple(line.strip() for line in upload_with["path"].splitlines() if line.strip())
    assert uploaded == REQUIRED_QUALITY_EVIDENCE


def test_quality_pr_uses_minimum_runtime_and_engineering_boundaries_while_master_keeps_full_matrix():
    payload = _workflow()
    jobs = payload["jobs"]
    system_runtime = jobs["system-runtime"]
    compatibility = jobs["compatibility"]
    engineering = jobs["engineering"]

    assert "if" not in system_runtime
    assert system_runtime["strategy"]["matrix"]["python-version"] == (
        "${{ fromJSON(github.event_name == 'push' && "
        "'[\"3.8\",\"3.9\"]' || '[\"3.8\"]') }}"
    )
    assert "if" not in compatibility
    assert compatibility["strategy"]["matrix"]["python-version"] == (
        "${{ fromJSON(github.event_name == 'push' && "
        "'[\"3.10\",\"3.11\",\"3.12\",\"3.13\",\"3.14\"]' || '[\"3.10\"]') }}"
    )
    assert "if" not in engineering
    assert engineering["steps"]


def test_quality_publishes_compliance_for_signed_reuse():
    payload = _workflow()
    steps = payload["jobs"]["engineering"]["steps"]
    compliance = next(
        step for step in steps if step.get("name") == "Run deterministic compliance verdict matrix"
    )
    assert "tee .cache/knowledge-hub/compliance-eval.json" in compliance["run"]
    assert ".cache/knowledge-hub/compliance-eval.json" in REQUIRED_QUALITY_EVIDENCE


def test_quality_builds_exact_source_binding_before_upload():
    payload = _workflow()
    steps = payload["jobs"]["engineering"]["steps"]
    binding = next(
        step for step in steps if step.get("name") == "Build exact quality evidence binding"
    )
    run = binding["run"]
    assert "quality_evidence_binding_cli build" in run
    assert '--source-revision "${{ github.event.pull_request.head.sha || github.sha }}"' in run
    verify_index = next(
        index for index, step in enumerate(steps)
        if step.get("name") == "Verify required quality evidence"
    )
    binding_index = steps.index(binding)
    assert binding_index < verify_index


def test_quality_manual_dispatch_is_available_for_trusted_automation_branches():
    payload = _workflow()
    triggers = payload["on"]
    assert "workflow_dispatch" in triggers
    assert triggers["push"]["branches"] == ["master"]

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "github.event.pull_request.head.sha || github.sha" in text


def test_quality_engineering_binds_complexity_to_explicit_git_baseline():
    payload = _workflow()
    engineering = payload["jobs"]["engineering"]
    assert engineering["env"]["KNOWLEDGE_COMPLEXITY_BASE_REF"] == (
        "${{ github.event_name == 'pull_request' && "
        "github.event.pull_request.base.sha || github.event_name == 'push' && "
        "github.event.before || 'origin/master' }}"
    )

    checkout = next(
        step
        for step in engineering["steps"]
        if step.get("name") == "Checkout"
    )
    assert checkout["with"]["fetch-depth"] == "0"
    assert checkout["with"]["persist-credentials"] == "false"
    assert checkout["with"]["ref"] == (
        "${{ github.event.pull_request.head.sha || github.sha }}"
    )


def test_quality_complexity_baseline_matches_engineering_budget_policy():
    import json

    policy = json.loads(
        Path("registry/engineering-budgets.json").read_text(encoding="utf-8")
    )
    baseline = policy["python"]["ci_baseline"]
    assert baseline["required_in_github_actions"] is True
    assert baseline["env"] == "KNOWLEDGE_COMPLEXITY_BASE_REF"
    assert baseline["missing_or_invalid"] == "fail"

    engineering = _workflow()["jobs"]["engineering"]
    assert baseline["env"] in engineering["env"]
    assert engineering["steps"][0]["with"]["fetch-depth"] == "0"
