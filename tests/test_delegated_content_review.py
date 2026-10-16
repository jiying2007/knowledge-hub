import copy
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys

import pytest

from tools.codex_assets.knowledge_hub.delegated_content_review import (
    FIELD, LEDGER, SCHEMA, content_digest, expected_record, item_digest,
    review_counts, review_state,
    load_ledger,
)
from tools.codex_assets.knowledge_hub import index_plan_review_queue as queue
from tools.codex_assets.knowledge_hub.status_review import build_review_queues
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction, WriteConflict, snapshot_inputs
from tools.codex_assets.knowledge_hub.review_semantic import OWNER_BLOCKED
from tools.codex_assets.knowledge_hub.delegated_content_review import eligible


@pytest.fixture
def case(tmp_path):
    root = tmp_path / "hub"
    (root / "registry").mkdir(parents=True)
    (root / "projects/p").mkdir(parents=True)
    (root / "projects/p/note.md").write_text("# 历史记录\n未证明设备放行。\n")
    (root / "registry/owners.json").write_text(json.dumps({"owners": [{"id": "leiwenjun"}]}))
    (root / "registry/review-risk-policy.json").write_text(json.dumps({"default_class": "ordinary", "classes": {}, "rules": []}))
    item = {"id": "one", "path": "projects/p/note.md", "kind": "validation", "owner": "leiwenjun",
            "status": "reviewing", "visibility": "team-internal", "generated_by_ai": True,
            "promotion": "none", "human_reviewed_by": "", "human_reviewed_at": "", "review_basis": ""}
    entry = {"id": "one", "path": item["path"], "owner": "leiwenjun", "item_sha256": item_digest(item),
             "content_sha256": content_digest(root, item["path"]), "decision": "accept-as-review-record",
             "basis": "完整审读：仅接受历史范围，设备/发布未验证。"}
    evidence = tmp_path / "authorization.md"
    evidence.write_text("用户明确授权自动复核。")
    independent = tmp_path / "independent.md"
    independent.write_text("独立内容审查完成；接受历史记录不代表设备证据。")
    auth = {"schema_version": SCHEMA, "authorization_id": "pilot-1", "authorized_by": "leiwenjun",
            "authorized_at": dt.datetime.now(dt.timezone.utc).date().isoformat(),
            "thread_id": "01a11fea-080f-7931-806a-65c547d9d1c0", "authorization_statement": "授权自动复核",
            "authorization_evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
            "executor": "Codex", "scope": "ordinary-reviewing-content-only",
            "independent_review_sha256": hashlib.sha256(independent.read_bytes()).hexdigest(), "entries": [entry],
            "request_proof": {"state": "verified", "request_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                              "intake_attestation_sha256": "a" * 64, "actor_identity_verified": False}}
    return root, item, auth, evidence, independent


def install(case):
    root, item, auth, _, _ = case
    item[FIELD] = expected_record(auth, auth["entries"][0])
    (root / LEDGER).write_text(json.dumps(auth) + "\n")
    return root, item, auth


def run_cli(case, *, apply=False, env_thread=None, attested=True):
    root, item, auth, evidence, independent = case
    items_path = root / "registry/items.jsonl"
    if not items_path.exists() or json.loads(items_path.read_text()) != item:
        items_path.write_text(json.dumps(item) + "\n")
    auth_path = evidence.parent / "scope.json"
    auth_path.write_text(json.dumps(auth))
    env = dict(os.environ, CODEX_THREAD_ID=env_thread or auth["thread_id"],
               PYTHONPATH=str(pathlib.Path(__file__).resolve().parents[1]))
    # Mock only the external Runtime transport in contract tests; production
    # has no environment switch or supplied-proof bypass.
    bootstrap = ("import json,sys; from tools.codex_assets.knowledge_hub import provider_grants; "
                 "proof=json.load(open(sys.argv[sys.argv.index('--authorization')+1]))['request_proof']; "
                 "provider_grants.attested_request=lambda *args:(proof['request_sha256'],proof['intake_attestation_sha256']); "
                 "from tools.codex_assets.knowledge_hub.delegated_content_review_cli import main; sys.exit(main())")
    entrypoint = ["-c", bootstrap] if attested else ["-m", "tools.codex_assets.knowledge_hub.delegated_content_review_cli"]
    cmd = ["rtk", sys.executable, *entrypoint,
           "--root", str(root), "--authorization", str(auth_path),
           "--authorization-sha256", hashlib.sha256(auth_path.read_bytes()).hexdigest(),
           "--authorization-evidence", str(evidence), "--request-file", str(evidence), "--independent-review", str(independent),
           "--apply" if apply else "--dry-run"]
    result = subprocess.run(cmd, cwd=evidence.parent, env=env, capture_output=True, text=True)
    return result, json.loads(result.stdout)


def test_apply_preserves_body_human_lifecycle_and_is_idempotent(case):
    root, before, _, _, _ = case
    before = copy.deepcopy(before)
    body = (root / before["path"]).read_bytes()
    result, payload = run_cli(case, apply=True)
    assert result.returncode == 0 and payload["updated_count"] == 1
    item = json.loads((root / "registry/items.jsonl").read_text())
    assert {k: v for k, v in item.items() if k != FIELD} == before
    assert (root / before["path"]).read_bytes() == body
    assert review_state(root, item)["closed"]
    counts = review_counts(root, [item])
    assert counts["ai_delegated_closed_count"] == 1
    assert counts["human_reviewed_count"] == 0
    assert counts["human_review_current_body_bound_count"] == 0
    assert counts["human_review_historical_unbound_count"] == 0
    second_case = (root, item, *case[2:])
    result, payload = run_cli(second_case, apply=True)
    assert result.returncode == 0 and payload["updated_count"] == 0
    assert payload["transaction_plan"]["changed_count"] == 0


def test_dry_run_has_no_registry_or_body_writes(case):
    root, item, _, _, _ = case
    result, payload = run_cli(case)
    assert result.returncode == 0 and not payload["applied"]
    assert json.loads((root / "registry/items.jsonl").read_text()) == item
    assert not (root / LEDGER).exists()


def test_agent_fabricated_evidence_without_runtime_intake_never_writes(case):
    root, item, _, _, _ = case
    result, payload = run_cli(case, apply=True, attested=False)
    assert result.returncode == 1 and not payload["applied"]
    assert payload["reason"] == "DECLARATION_UNATTESTED"
    assert json.loads((root / "registry/items.jsonl").read_text()) == item
    assert not (root / LEDGER).exists()


def test_historical_unverified_request_never_closes_queue(case):
    root, item, auth, _, _ = case
    auth["request_proof"].update(state="unverified", request_sha256=None, intake_attestation_sha256=None)
    root, item, _ = install(case)
    state = review_state(root, item)
    assert state["status"] == "needs-review" and state["closed"] is False
    assert review_counts(root, [item])["ai_delegated_closed_count"] == 0


@pytest.mark.parametrize("change", ["active", "owner", "kind", "visibility", "promotion", "readiness", "owner-decision", "owner-gate", "human", "risk", "content", "object"])
def test_cli_rejects_outside_scope_or_drift(case, change):
    root, item, _, _, _ = case
    if change in {"active", "owner", "kind", "visibility", "promotion"}:
        key, value = {"active": ("status", "active"), "owner": ("owner", "team-core"),
                      "kind": ("kind", "decision"), "visibility": ("visibility", "personal-local"),
                      "promotion": ("promotion", "approved")}[change]
        item[key] = value
    elif change == "readiness":
        item["path"] = "projects/p/project-readiness.md"
    elif change == "owner-decision":
        item["owner_decision"] = "accept"
    elif change == "owner-gate":
        item["owner_gate_verified"] = True
    elif change == "human":
        item["human_reviewed_by"] = "Codex"
    elif change == "risk":
        (root / "registry/review-risk-policy.json").write_text(json.dumps({"default_class": "security-critical"}))
    elif change == "content":
        (root / item["path"]).write_text("修改内容")
    else:
        item["summary_zh"] = "变化"
    result, payload = run_cli(case, apply=True)
    assert result.returncode == 1 and not payload["applied"]
    assert not (root / LEDGER).exists()


@pytest.mark.parametrize("change", ["thread", "evidence", "independent", "statement", "unknown", "duplicate", "extra-human", "lifecycle-decision"])
def test_cli_rejects_invalid_authorization(case, change):
    _, _, auth, evidence, independent = case
    thread = None
    if change == "thread":
        thread = "01a11fea-080f-7931-806a-65c547d9d1c1"
    elif change == "evidence":
        evidence.write_text("授权证据发生变化")
    elif change == "independent":
        independent.write_text("复核证据发生变化")
    elif change == "statement":
        auth["authorization_statement"] = "未经用户授权"
    elif change == "unknown":
        auth["entries"][0]["id"] = "outside-scope"
    elif change == "duplicate":
        auth["entries"].append(copy.deepcopy(auth["entries"][0]))
    elif change == "extra-human":
        auth["entries"][0]["human_reviewed_by"] = "Codex"
    else:
        auth["entries"][0]["decision"] = "archive-only"
    result, payload = run_cli(case, apply=True, env_thread=thread)
    assert result.returncode == 1 and not payload["applied"]


@pytest.mark.parametrize("change", ["content", "object", "record", "ledger", "revoke", "active", "risk"])
def test_queue_reopens_on_drift_tampering_or_revocation(case, change):
    root, item, auth = install(case)
    assert review_state(root, item)["closed"]
    if change == "content":
        (root / item["path"]).write_text("新内容")
    elif change == "object":
        item["review_after"] = "2030-01-01"
    elif change == "record":
        item[FIELD]["basis"] = "伪造"
    elif change == "ledger":
        auth["entries"][0]["basis"] = "篡改凭据"
        (root / LEDGER).write_text(json.dumps(auth))
    elif change == "revoke":
        (root / LEDGER).unlink()
    elif change == "active":
        item["status"] = "active"
    else:
        (root / "registry/review-risk-policy.json").write_text(json.dumps({"default_class": "security-critical"}))
    assert review_state(root, item)["status"] == "invalid"
    queue.configure_review_queue(root, None, lambda path: content_digest(root, path))
    view = queue.build_review_queue_view([item], [])
    status = build_review_queues(root, [item], [], dt.date.today(), "product", 10)
    assert view["summary"]["ai_generated_pending_count"] == status["summary"]["ai_generated_pending_count"] == 1
    assert view["summary"]["ai_delegated_closed_count"] == 0


@pytest.mark.parametrize("decision", ["accept-as-review-record", "needs-edits", "defer"])
def test_index_and_status_have_same_transparent_review_counts(case, decision):
    case[2]["entries"][0]["decision"] = decision
    root, item, _ = install(case)
    queue.configure_review_queue(root, None, lambda path: content_digest(root, path))
    view = queue.build_review_queue_view([item], [])
    status = build_review_queues(root, [item], [], dt.date.today(), "product", 10)
    expected = int(decision == "accept-as-review-record")
    assert view["summary"]["ai_delegated_closed_count"] == status["summary"]["ai_delegated_closed_count"] == expected
    assert view["summary"]["ai_generated_pending_count"] == 1 - expected
    assert view["summary"]["human_reviewed_count"] == 0


def test_transaction_guards_concurrent_body_changes(case):
    root, item, _, _, _ = case
    inputs = snapshot_inputs(root)
    transaction = RepositoryTransaction(root, expected_inputs=inputs)
    before = (root / item["path"]).read_bytes()
    transaction.add_bytes(item["path"], before, expected_sha256=content_digest(root, item["path"]))
    (root / item["path"]).write_text("其他线程更新")
    with pytest.raises(WriteConflict):
        transaction.apply()
    assert (root / item["path"]).read_text() == "其他线程更新"


@pytest.mark.parametrize("review_status", sorted(OWNER_BLOCKED) + ["needs-owner-custom", "pending-owner-custom", "blocked-custom", "owner-review-required", "owner-gate-blocked"])
def test_owner_blocked_status_is_not_eligible_even_with_rebound_identity(case, review_status):
    root, item, auth, _, _ = case
    item["review_status"] = review_status
    auth["entries"][0]["item_sha256"] = item_digest(item)
    assert not eligible(root, item)
    result, payload = run_cli(case, apply=True)
    assert result.returncode == 1 and not payload["applied"]


def test_domain_evidence_contract_is_not_eligible(case):
    root, item, auth, _, _ = case
    item["evidence_contract"] = {"required": True}
    auth["entries"][0]["item_sha256"] = item_digest(item)
    assert not eligible(root, item)


def test_real_provider_promotion_disclaimer_is_allowed(case):
    root, item, auth, _, _ = case
    item["promotion_decision"] = "none; capture does not authorize active promotion or owner decision"
    auth["entries"][0]["item_sha256"] = item_digest(item)
    assert eligible(root, item)
    result, payload = run_cli(case)
    assert result.returncode == 0 and payload["selected_count"] == 1


def test_authorization_statement_and_hash_use_same_read_snapshot(case, monkeypatch, capsys):
    from tools.codex_assets.knowledge_hub import delegated_content_review_cli as cli
    root, item, auth, evidence, independent = case
    # Evidence A has a matching hash but no authorization statement. Replace
    # it with B immediately after the single read; B must never authorize A.
    evidence.write_text("没有授权语句的证据A")
    auth["authorization_evidence_sha256"] = hashlib.sha256(evidence.read_bytes()).hexdigest()
    (root / "registry/items.jsonl").write_text(json.dumps(item))
    scope = evidence.parent / "scope.json"
    scope.write_text(json.dumps(auth))
    actual_read = cli.read_evidence
    calls = []
    def swapping_read(path):
        raw = actual_read(path)
        if path == evidence:
            calls.append(path)
            path.write_text("授权自动复核")
        return raw
    monkeypatch.setattr(cli, "read_evidence", swapping_read)
    monkeypatch.setenv("CODEX_THREAD_ID", auth["thread_id"])
    monkeypatch.setattr(sys, "argv", ["review", "--root", str(root), "--authorization", str(scope),
                                   "--authorization-sha256", hashlib.sha256(scope.read_bytes()).hexdigest(),
                                   "--authorization-evidence", str(evidence), "--request-file", str(evidence), "--independent-review", str(independent), "--apply"])
    assert cli.main() == 1
    assert json.loads(capsys.readouterr().out)["reason"] == "authorization statement absent from supplied evidence"
    assert len(calls) == 1 and not (root / LEDGER).exists()


def test_official_human_review_supersedes_ai_and_keeps_history(case):
    root, item, _ = install(case)
    (root / "registry/items.jsonl").write_text(json.dumps(item) + "\n")
    queue.configure_review_queue(root, None, lambda path: content_digest(root, path))
    row = queue.make_review_queue_item(item, "ai-human-review", ["missing-human-review"], ["human_reviewed_by", "human_reviewed_at", "review_basis"])
    form = queue.make_review_queue_form(row)
    form.update(human_reviewed_by="leiwenjun", human_reviewed_at=dt.date.today().isoformat(),
                review_basis="隔离fixture的真实human入口契约测试，非实际用户签收。", review_decision="accept-as-review-record")
    forms = root.parent / "human.jsonl"
    forms.write_text(json.dumps(form) + "\n")
    env = dict(os.environ, PYTHONPATH=str(pathlib.Path(__file__).resolve().parents[1]))
    result = subprocess.run(["rtk", sys.executable, "-m", "tools.codex_assets.knowledge_hub.review_queue_apply_cli", str(root), "--forms", str(forms), "--apply", "--json"], cwd=root.parent, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    updated = json.loads((root / "registry/items.jsonl").read_text())
    assert FIELD not in updated and load_ledger(root)
    counts = review_counts(root, [updated])
    assert counts["ai_delegated_closed_count"] == 0
    assert counts["human_reviewed_count"] == 1
    assert counts["human_review_current_body_bound_count"] == 1
    assert counts["human_review_historical_unbound_count"] == 0
    assert queue.build_review_queue_view([updated], [])["summary"]["row_count"] == 0
    assert review_state(root, updated)["status"] == "absent"


@pytest.mark.parametrize("change", ["malformed", "duplicate", "scope"])
def test_orphan_ledger_validation_rejects_invalid_history(case, change):
    root, item, auth = install(case)
    item.pop(FIELD)
    if change == "malformed":
        (root / LEDGER).write_text("not-json")
    elif change == "duplicate":
        (root / LEDGER).write_text(json.dumps(auth) + "\n" + json.dumps(auth))
    else:
        auth["scope"] = "active-promotion"
        (root / LEDGER).write_text(json.dumps(auth))
    with pytest.raises((ValueError, RuntimeError)):
        load_ledger(root)


def test_orphan_ledger_is_valid_history_after_human_supersession(case):
    root, item, auth = install(case)
    item.pop(FIELD)
    item["human_reviewed_by"] = "leiwenjun"
    (root / item["path"]).write_text("后续真人审读后的新内容")
    assert load_ledger(root) == {auth["authorization_id"]: auth}


def test_new_exact_scope_can_rereview_drift_without_overwriting_history(case):
    root, item, old = install(case)
    auth = copy.deepcopy(old)
    auth["authorization_id"] = "pilot-new-body"
    (root / item["path"]).write_text("完整重新审读的新历史内容")
    auth["entries"][0]["content_sha256"] = content_digest(root, item["path"])
    auth["entries"][0]["basis"] = "独立重新完整审读新正文，仍不证明设备放行。"
    result, payload = run_cli((root, item, auth, *case[3:]), apply=True)
    assert result.returncode == 0 and payload["updated_count"] == 1
    updated = json.loads((root / "registry/items.jsonl").read_text())
    assert review_state(root, updated)["closed"]
    assert set(load_ledger(root)) == {old["authorization_id"], auth["authorization_id"]}


@pytest.mark.parametrize("change", ["empty", "missing", "hash", "schema-bool", "extra-human", "date"])
def test_new_scope_cannot_silently_replace_malformed_old_credential(case, change):
    root, item, old = install(case)
    auth = copy.deepcopy(old)
    auth["authorization_id"] = "new-scope"
    if change == "empty":
        item[FIELD] = {}
    elif change == "missing":
        item[FIELD] = {"authorization_id": "old"}
    elif change == "hash":
        item[FIELD]["content_sha256"] = "invalid"
    elif change == "schema-bool":
        item[FIELD]["schema_version"] = True
    elif change == "extra-human":
        item[FIELD]["human_reviewed_by"] = "Codex"
    else:
        item[FIELD]["reviewed_at"] = "invalid"
    result, payload = run_cli((root, item, auth, *case[3:]), apply=True)
    assert result.returncode == 1 and not payload["applied"]
    assert set(load_ledger(root)) == {old["authorization_id"]}


@pytest.mark.parametrize("lifecycle", ["active", "reviewing"])
def test_legacy_human_review_without_body_hash_is_an_explicit_current_exception(case, lifecycle):
    root, item, _, _, _ = case
    item.update({
        "status": lifecycle,
        "human_reviewed_by": "leiwenjun",
        "human_reviewed_at": "2026-10-16",
        "review_basis": "历史人工审核说明，不足以绑定当前文件版本",
        "human_review_decision": "accept-as-review-record",
    })

    counts = review_counts(root, [item])
    assert counts["human_reviewed_count"] == 1  # preserved legacy metadata count
    assert counts["human_review_current_body_bound_count"] == 0
    assert counts["human_review_historical_unbound_count"] == 1
    assert counts["human_review_content_hash_mismatch_count"] == 0

    queue.configure_review_queue(root, None, lambda path: content_digest(root, path))
    view = queue.build_review_queue_view([item], [])
    status = build_review_queues(root, [item], [], dt.date(2026, 10, 16), "product", 10)
    assert view["summary"]["ai_generated_pending_count"] == 1
    assert status["summary"]["ai_generated_pending_count"] == 1
    assert "human-review-current-body-unbound" in view["rows"][0]["reasons"]
    assert "human-review-current-body-unbound" in status["ai_generated_pending"][0]["reasons"]
    # Legacy review identity gaps are human-review exceptions: never silently
    # closed, never promoted, but not misreported as a technical failure.
    assert view["rows"][0]["priority"] == "P1"
    assert status["ai_generated_pending"][0]["priority"] == "P1"
    assert view["summary"]["active_or_promotion_blocker_count"] == 0
    assert status["summary"]["active_or_promotion_blocker_count"] == 0
    assert status["product_blocking_final_gate"] is True
    assert status["active_blocking_final_gate"] is False

    item["human_review_content_sha256"] = content_digest(root, item["path"])
    counts = review_counts(root, [item])
    assert counts["human_review_current_body_bound_count"] == 1
    assert counts["human_review_historical_unbound_count"] == 0
    assert queue.build_review_queue_view([item], [])["summary"]["ai_generated_pending_count"] == 0
    assert build_review_queues(root, [item], [], dt.date(2026, 10, 16), "product", 10)["summary"]["ai_generated_pending_count"] == 0

    (root / item["path"]).write_text("# 新版本\n未经重新审核", encoding="utf-8")
    counts = review_counts(root, [item])
    assert counts["human_review_content_hash_mismatch_count"] == 1
    assert counts["human_review_current_body_bound_count"] == 0
    assert queue.build_review_queue_view([item], [])["summary"]["ai_generated_pending_count"] == 1
    assert build_review_queues(root, [item], [], dt.date(2026, 10, 16), "product", 10)["summary"]["ai_generated_pending_count"] == 1
    if lifecycle == "active":
        assert queue.build_review_queue_view([item], [])["rows"][0]["priority"] == "P0"
        assert build_review_queues(root, [item], [], dt.date(2026, 10, 16), "product", 10)["summary"]["active_or_promotion_blocker_count"] == 1


def test_active_ai_missing_human_review_is_still_hard_blocked(case):
    root, item, _, _, _ = case
    item["status"] = "active"
    queue.configure_review_queue(root, None, lambda path: content_digest(root, path))
    view = queue.build_review_queue_view([item], [])
    status = build_review_queues(root, [item], [], dt.date(2026, 10, 16), "product", 10)
    assert view["rows"][0]["priority"] == "P0"
    assert status["ai_generated_pending"][0]["priority"] == "P0"
    assert status["summary"]["active_or_promotion_blocker_count"] == 1
    assert status["active_blocking_final_gate"] is True
    assert status["product_blocking_final_gate"] is True
    assert "human-review-current-body-unbound" not in view["rows"][0]["reasons"]


def test_historical_archived_human_review_without_hash_is_not_active_gate(case):
    root, item, _, _, _ = case
    item.update({
        "status": "archived",
        "human_reviewed_by": "leiwenjun",
        "human_reviewed_at": "2026-10-16",
        "review_basis": "存档时历史批准；没有当前 active 适用声明",
    })
    queue.configure_review_queue(root, None, lambda path: content_digest(root, path))
    assert queue.build_review_queue_view([item], [])["summary"]["ai_generated_pending_count"] == 0
    assert build_review_queues(root, [item], [], dt.date(2026, 10, 16), "product", 10)["summary"]["ai_generated_pending_count"] == 0
    assert review_counts(root, [item])["human_review_historical_unbound_count"] == 1
