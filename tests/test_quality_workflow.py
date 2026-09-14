from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/quality.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_quality_runs_for_pushes_and_pull_requests():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)
    assert "push" in triggers
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
