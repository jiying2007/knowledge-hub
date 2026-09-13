from tools.codex_assets.knowledge_hub import terminal_closure


def _policy():
    return {
        "bounded_legacy": {
            "max_oversized_legacy_modules": 0,
            "max_legacy_artifact_references": 315,
            "growth_allowed": False,
            "require_artifact_terminal_forms": True,
        }
    }


def _complexity():
    return {
        "status": "pass",
        "oversized_module_count": 0,
        "legacy_attention_count": 0,
    }


def _artifacts():
    return {
        "status": "pass",
        "immutable_refs": {"legacy_reference_count": 315},
    }


def test_bounded_legacy_accepts_exact_terminal_form_coverage(tmp_path):
    terminal_forms = {
        "status": "pass",
        "legacy_reference_count": 315,
        "accepted_legacy_reference_count": 315,
        "unaccepted_legacy_reference_count": 0,
        "legacy_reference_set_sha256": "a" * 64,
    }

    report = terminal_closure._bounded_legacy_state(
        tmp_path,
        _policy(),
        _complexity(),
        _artifacts(),
        terminal_forms,
    )

    assert report["status"] == "pass"
    assert report["artifact_terminal_forms_required"] is True
    assert report["artifact_terminal_forms_status"] == "pass"
    assert report["artifact_terminal_forms_match_artifact_governance"] is True
    assert report["legacy_artifact_reference_accepted_count"] == 315
    assert report["legacy_artifact_reference_unaccepted_count"] == 0


def test_bounded_legacy_rejects_unaccepted_historical_refs(tmp_path):
    terminal_forms = {
        "status": "fail",
        "legacy_reference_count": 315,
        "accepted_legacy_reference_count": 0,
        "unaccepted_legacy_reference_count": 315,
        "legacy_reference_set_sha256": "b" * 64,
    }

    report = terminal_closure._bounded_legacy_state(
        tmp_path,
        _policy(),
        _complexity(),
        _artifacts(),
        terminal_forms,
    )

    assert report["status"] == "needs-fix"
    assert report["legacy_artifact_reference_unaccepted_count"] == 315


def test_bounded_legacy_rejects_terminal_form_count_drift(tmp_path):
    terminal_forms = {
        "status": "pass",
        "legacy_reference_count": 314,
        "accepted_legacy_reference_count": 314,
        "unaccepted_legacy_reference_count": 0,
        "legacy_reference_set_sha256": "c" * 64,
    }

    report = terminal_closure._bounded_legacy_state(
        tmp_path,
        _policy(),
        _complexity(),
        _artifacts(),
        terminal_forms,
    )

    assert report["status"] == "needs-fix"
    assert report["artifact_terminal_forms_match_artifact_governance"] is False
