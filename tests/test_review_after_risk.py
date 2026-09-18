from __future__ import annotations

import json
import pathlib
import subprocess


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "tools/codex_assets/knowledge_hub/review_after_cli.py"


def test_review_after_risk_classifies_security_and_ordinary(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (tmp_path / "artifacts/manifests").mkdir(parents=True)
    (tmp_path / "SECURITY.md").write_text("# security\n", encoding="utf-8")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes/note.md").write_text("# note\n", encoding="utf-8")
    rows = [
        {
            "id": "security",
            "path": "SECURITY.md",
            "owner": "owner",
            "status": "active",
            "review_after": "2026-09-01",
            "source": {},
        },
        {
            "id": "ordinary",
            "path": "notes/note.md",
            "owner": "owner",
            "status": "active",
            "review_after": "2026-09-01",
            "source": {},
        },
    ]
    (registry / "items.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
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
    (tmp_path / "artifacts/manifests/example-owner-decision-worksheets-1.jsonl").write_text(
        "", encoding="utf-8"
    )

    result = subprocess.run(
        ["rtk", "python3", str(SCRIPT), str(tmp_path), "--json", "--as-of", "2026-09-18"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    by_id = {row["item_id"]: row for row in payload["rows"]}
    assert by_id["security"]["review_class"] == "security-critical"
    assert by_id["security"]["stale_severity"] == "blocked"
    assert by_id["ordinary"]["review_class"] == "ordinary"
    assert payload["groups"]["by_review_class"]["security-critical"]["count"] == 1
