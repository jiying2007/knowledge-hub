from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/signed-quality-attestation.yml")


def _workflow():
    payload = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(payload, dict)
    return payload


def test_signed_attestation_runs_on_every_master_push():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)
    push = triggers.get("push")
    assert isinstance(push, dict)
    assert push.get("branches") == ["master"]
    assert "paths" not in push
    assert "paths-ignore" not in push


def test_signed_attestation_preserves_every_master_revision():
    payload = _workflow()
    assert "concurrency" not in payload


def test_signed_attestation_keeps_manual_reverification_entrypoint():
    payload = _workflow()
    triggers = payload.get("on")
    assert isinstance(triggers, dict)
    assert "workflow_dispatch" in triggers
