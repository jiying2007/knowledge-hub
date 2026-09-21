import datetime as dt
import json

import pytest

from tools.codex_assets.knowledge_hub import health
from tools.codex_assets.knowledge_hub.health import _is_body_markdown
from tools.codex_assets.knowledge_hub.health_cli import build_parser


def test_fast_body_coverage_matches_orphan_body_boundary():
    assert _is_body_markdown("projects/xcrz-sigmastar-demo/current/runbooks/debug.md") is True
    assert _is_body_markdown("projects/pcr02-ssc305/README.md") is False
    assert _is_body_markdown("templates/inbox-note.md") is False
    assert _is_body_markdown("docs/goals/knowledge-hub-final-state.md") is False


def test_health_review_queue_consumes_canonical_projection(monkeypatch, tmp_path):
    canonical = {
        "indexes": {
            "by_review_queue": {
                "summary": {
                    "row_count": 2,
                    "ai_generated_pending_count": 1,
                    "external_source_pending_count": 1,
                    "active_or_promotion_blocker_count": 0,
                }
            }
        }
    }
    monkeypatch.setattr(
        health,
        "run_rtk",
        lambda *_args, **_kwargs: {
            "command": "canonical review queue",
            "exit_code": 0,
            "stdout": json.dumps(canonical),
            "stderr": "",
        },
    )

    payload = health._review_queue(tmp_path)

    assert payload["pending_total"] == 2
    assert payload["ai_generated_pending"] == 1
    assert payload["external_source_pending"] == 1
    assert payload["active_or_promotion_blocker_count"] == 0
    assert payload["source"] == "canonical-index-plan"
    assert payload["status"] == "pass"


def test_fast_body_coverage_ignores_deleted_markdown(monkeypatch, tmp_path):
    new_body = tmp_path / "projects/new/current.md"
    new_body.parent.mkdir(parents=True)
    new_body.write_text("# current\n", encoding="utf-8")

    def fake_run_rtk(_root, args, **_kwargs):
        stdout = (
            " D projects/retired/runbook.md\0?? projects/new/current.md\0"
            if "status" in args
            else "projects/retired/runbook.md\0"
        )
        return {
            "command": " ".join(args),
            "exit_code": 0,
            "stdout": stdout,
            "stderr": "",
        }

    monkeypatch.setattr(health, "run_rtk", fake_run_rtk)

    payload = health._body_coverage(tmp_path, [])

    assert payload["checked_count"] == 1
    assert payload["deleted_body_count"] == 1
    assert payload["deleted_body_sample"] == ["projects/retired/runbook.md"]
    assert payload["missing_registry"] == ["projects/new/current.md"]


def test_health_cli_rejects_removed_skip_gate_option():
    with pytest.raises(SystemExit) as error:
        build_parser().parse_args(["--skip-final-gate"])

    assert error.value.code == 2


def test_health_cli_defaults_to_auto_snapshot_selection():
    args = build_parser().parse_args([])

    assert args.gate_suite == "auto"


def test_health_summary_prefers_full_snapshot_and_refreshes_quick_in_auto_mode(
    monkeypatch, tmp_path
):
    refresh_suites = []
    monkeypatch.setattr(health, "registry_items", lambda _root: [])
    monkeypatch.setattr(
        health,
        "_body_coverage",
        lambda _root, _items: {"missing_registry_count": 0},
    )
    monkeypatch.setattr(
        health,
        "_review_queue",
        lambda _root: {
            "status": "pass",
            "active_or_promotion_blocker_count": 0,
        },
    )
    monkeypatch.setattr(health, "_review_after", lambda *_args: {})
    monkeypatch.setattr(health, "_reviewing_triage", lambda *_args: {})
    monkeypatch.setattr(health, "incomplete_transactions", lambda _root: [])
    monkeypatch.setattr(
        health,
        "run_product_gate",
        lambda _root, _as_of, regression_suite: refresh_suites.append(
            regression_suite
        ),
    )
    monkeypatch.setattr(
        health,
        "_load_snapshot",
        lambda *_args, **_kwargs: (
            {
                "schema_version": 5,
                "status": "needs-review",
                "terminal": False,
                "maturity_axes": {
                    "schema_version": 2,
                    "status": "needs-review",
                    "terminal": False,
                    "content": {"status": "needs-review"},
                    "delivery": {"status": "needs-review"},
                    "adoption": {"status": "needs-review"},
                },
                "platform_status": {"status": "pass", "blockers": []},
                "owner_and_real_evidence": {"pending_project_ids": ["p1"]},
                "blockers": [],
                "gap_map": [],
            },
            {
                "state": "fresh",
                "path": ".cache/knowledge-hub/final-gate-product-full.json",
                "fresh": True,
                "suite": "full",
            },
        ),
    )

    payload = health.health_summary(
        tmp_path,
        dt.date(2026, 7, 19),
        refresh_gate=True,
        gate_suite="auto",
    )

    assert refresh_suites == ["quick"]
    assert payload["schema_version"] == 3
    assert payload["status"] == "needs-review"
    assert "health_status" not in payload
    assert payload["health_axes"] == {
        "control_plane": "pass",
        "evidence_freshness": "pass",
        "content_governance": "needs-review",
        "runtime_hygiene": "pass",
    }
    assert payload["runtime_maintenance"]["apply_requires_explicit_request"] is True
    assert payload["product_maturity"]["snapshot_suite"] == "full"
    assert payload["product_maturity"]["full_regression_evidence"] is True
    assert "--regression-suite full" in payload["final_gate"]["command"]


def test_health_review_after_reports_ai_first_risk_classes(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "sources.json").write_text('{"sources": []}\n', encoding="utf-8")
    (registry / "review-risk-policy.json").write_text(
        json.dumps(
            {
                "default_class": "ordinary",
                "classes": {
                    "ordinary": {
                        "stale_severity": "warning",
                        "ai_first_action": "auto-triage",
                    },
                    "security-critical": {
                        "stale_severity": "blocked",
                        "ai_first_action": "human-review-required",
                    },
                },
                "rules": [
                    {"path": "SECURITY.md", "review_class": "security-critical"}
                ],
            }
        ),
        encoding="utf-8",
    )
    items = [
        {"path": "SECURITY.md", "review_after": "2026-09-01"},
        {"path": "notes/a.md", "review_after": "2026-09-01"},
    ]

    payload = health._review_after(items, tmp_path, dt.date(2026, 9, 18))

    assert payload["stale_item_count"] == 2
    assert payload["security_critical_stale_count"] == 1
    assert payload["by_review_class"] == {
        "ordinary": 1,
        "security-critical": 1,
    }
    assert payload["risk_policy_status"] == "pass"
    assert payload["ai_first_default"] is True
