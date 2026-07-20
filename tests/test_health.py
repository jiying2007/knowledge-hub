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
                "gate_status": "pass",
                "overall_status": "needs-owner-review",
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
    assert payload["health_status"] == "needs-owner-review"
    assert payload["product_maturity"]["snapshot_suite"] == "full"
    assert payload["product_maturity"]["full_regression_evidence"] is True
    assert "--regression-suite full" in payload["final_gate"]["command"]
