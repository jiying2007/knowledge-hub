from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/quality.yml")
REQUIRED_QUALITY_EVIDENCE = (
    ".tmp/engineering/knowledge-hub.cdx.json",
    ".cache/knowledge-hub/engineering-quality.json",
    ".cache/knowledge-hub/compliance-eval.json",
    ".cache/knowledge-hub/restore-drill-head.json",
    ".cache/knowledge-hub/final-gate-product-full.json",
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
