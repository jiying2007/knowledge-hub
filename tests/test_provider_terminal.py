"""Negative requirements for the terminal Provider; temporary fixtures only."""

import json
import pytest

from test_provider_subjects import subject_root, grant
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_jsonl, file_sha256
from tools.codex_assets.knowledge_hub.provider_cli import parser
from tools.codex_assets.knowledge_hub.provider_operations import archive, assign, reconcile, assignment_request
from tools.codex_assets.knowledge_hub.store import audit_transactions


def test_metadata_transaction_preserves_operation_history(tmp_path):
    from tools.codex_assets.knowledge_hub.provider_operations import stage_metadata_update
    from tools.codex_assets.knowledge_hub.common import load_markdown, render_markdown, encode_jsonl
    from tools.codex_assets.knowledge_hub.model import merge_frontmatter_mirror
    from tools.codex_assets.knowledge_hub.store import RepositoryTransaction, snapshot_inputs
    root, _, args = subject_root(tmp_path)
    receipt = archive(root, args)
    before = load_jsonl(root / "registry/items.jsonl")[0]
    history = load_jsonl(root / "registry/provider-operations.jsonl")
    after = dict(before, review_after="2026-12-01")
    metadata, body = load_markdown(root / before["path"])
    rendered = render_markdown(merge_frontmatter_mirror(metadata, after), body)
    transaction = RepositoryTransaction(root, expected_inputs=snapshot_inputs(root))
    transaction.add_text(before["path"], rendered)
    transaction.add_text("registry/items.jsonl", encode_jsonl([after]))
    stage_metadata_update(root, transaction, before, after, rendered)
    transaction.apply()
    assert load_jsonl(root / "registry/provider-operations.jsonl")[0] == history[0]
    assert reconcile(root, receipt["operation_id"], file_sha256(root / before["path"]))["status"] == "VERIFIED"
    assert reconcile(root, receipt["operation_id"], receipt["content_sha256"])["status"] == "CONFLICT"


def test_corrupted_cache_cannot_upgrade_authority(tmp_path):
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, _, args = subject_root(tmp_path)
    archive(root, args)
    query = parser().parse_args(["context", "--cwd", str(tmp_path), "--query", "事务", "--execution-project", "test", "--summary-json", "--receipt-key", "forged"])
    assert run(root, query)["cache"]["hit"] is False
    path = root / ".cache/knowledge-hub/context-receipts/v4-forged.json"
    value = json.loads(path.read_text())
    value["summary"]["context"][0]["items"][0]["status"] = "active"
    ident = value["summary"]["context"][0]["items"][0].get("id") or value["summary"]["context"][0]["items"][0]["item_id"]
    value["summary"]["authority_lanes"] = {"authoritative": [ident], "provisional": [], "historical": [], "discovery": []}
    path.write_text(json.dumps(value))
    result = run(root, query)
    assert result["cache"]["hit"] is False
    assert result["authority_lanes"]["authoritative"] == []


def test_cache_does_not_store_query_terms_in_selection_reasons(tmp_path):
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, source, args = subject_root(tmp_path)
    source.write_text("# 普通知识\n\n普通摘要。\n\nuniquenonmetadataquery\n")
    archive(root, args)
    query = parser().parse_args(["context", "--cwd", str(tmp_path), "--query", "uniquenonmetadataquery", "--retrieval-project", "test", "--summary-json", "--receipt-key", "query"])
    run(root, query)
    assert "uniquenonmetadataquery" not in (root / ".cache/knowledge-hub/context-receipts/v4-query.json").read_text()


def test_remote_identity_keeps_host_port_and_case():
    from tools.codex_assets.knowledge_hub.remote_identity import parse_remote, identity_key
    assert parse_remote("https://one.example/team/Test.git") != parse_remote("https://two.example/team/Test.git")
    assert parse_remote("https://one.example/team/Test.git") != parse_remote("https://one.example:8443/team/Test.git")
    assert parse_remote("https://one.example/team/Test.git") != parse_remote("https://one.example/team/test.git")
    assert parse_remote("git@github.com:Team/Test.git") == parse_remote("https://github.com/team/test.git")
    assert identity_key("team/test") == ""


def test_principal_does_not_depend_on_reporting(tmp_path):
    root, _, args = subject_root(tmp_path)
    (root / "local/activity-report.json").write_text('{"enabled":false}')
    assert archive(root, args)["status"] == "ARCHIVED"


def test_no_hit_cache_invalidates_unselected_body(tmp_path):
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, _, args = subject_root(tmp_path)
    args.subject = "personal:local-user"
    archive(root, args)
    query = parser().parse_args(["context", "--cwd", str(tmp_path), "--query", "uniquecorpusneedle", "--personal", "--summary-json", "--receipt-key", "negative"])
    assert run(root, query)["context"][0]["zero_hit"] is True
    row = load_jsonl(root / "registry/items.jsonl")[0]
    path = root / row["path"]
    path.write_text(path.read_text() + "\nuniquecorpusneedle\n")
    result = run(root, query)
    assert result["cache"]["hit"] is False
    assert result["context"][0]["zero_hit"] is False


@pytest.mark.parametrize("private_type", ["personal", "unassigned"])
def test_logical_private_workspace_invalidates_negative_cache(tmp_path, private_type):
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, _, args = subject_root(tmp_path)
    args.subject = private_type + ":local-user"
    archive(root, args)
    (root / "registry/provider-workspaces.json").write_text(json.dumps({"schema_version": 1, "workspaces": [
        {"workspace_ref": "workspace://private", "subject_ref": {"type": private_type, "id": "local-user"}}]}))
    query = parser().parse_args(["context", "--cwd", str(tmp_path), "--query", "uniquecorpusneedle",
                                "--workspace", "workspace://private", "--summary-json", "--receipt-key", "implicit"])
    assert run(root, query)["context"][0]["zero_hit"] is True
    item = load_jsonl(root / "registry/items.jsonl")[0]
    path = root / item["path"]
    path.write_text(path.read_text() + "\nuniquecorpusneedle\n")
    result = run(root, query)
    assert result["cache"]["hit"] is False
    assert result["context"][0]["zero_hit"] is False


def test_unauthorized_private_workspace_never_hashes_body(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import provider_context
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, _, args = subject_root(tmp_path)
    args.subject = "personal:local-user"
    archive(root, args)
    (root / "registry/provider-workspaces.json").write_text(json.dumps({"schema_version": 1, "workspaces": [
        {"workspace_ref": "workspace://private", "subject_ref": {"type": "personal", "id": "local-user"}}]}))
    (root / "local/provider-principal.json").write_text('{"schema_version":1,"enabled":true,"principal_id":"other-user"}')
    private = root / load_jsonl(root / "registry/items.jsonl")[0]["path"]
    reads = []
    original = provider_context.file_sha256
    def monitored(path):
        if path == private:
            reads.append(path)
        return original(path)
    monkeypatch.setattr(provider_context, "file_sha256", monitored)
    query = parser().parse_args(["context", "--workspace", "workspace://private", "--query", "事务",
                                "--summary-json", "--receipt-key", "denied"])
    with pytest.raises(KnowledgeHubError, match="VISIBILITY_DENIED"):
        run(root, query)
    assert reads == []
    assert not (root / ".cache/knowledge-hub/context-receipts/v4-denied.json").exists()


def test_archive_predicted_hash_drift_is_blocked_before_write(tmp_path):
    root, _, args = subject_root(tmp_path)
    args.apply = False
    plan = archive(root, args)
    args.apply = True
    args.expected_content_sha256 = "0" * 64
    with pytest.raises(KnowledgeHubError, match="CONTENT_DRIFT"):
        archive(root, args)
    assert load_jsonl(root / "registry/items.jsonl") == []
    args.expected_content_sha256 = plan["content_sha256"]
    assert archive(root, args)["status"] == "ARCHIVED"


def test_archive_grant_requires_exact_reviewed_content_scope(tmp_path, monkeypatch):
    from tools.codex_assets.knowledge_hub import provider_grants, authorization
    root, source, args = subject_root(tmp_path)
    args.apply = False
    planned = archive(root, args)
    request = tmp_path / "request.txt"
    request.write_text("批准将此脱敏结论归档到 test 项目。")
    monkeypatch.setattr(provider_grants, "attested_request", lambda *unused: ("a" * 64, "b" * 64))
    approved = {"actor": "local-user", "action": "archive", "subject_ref": {"type": "project", "id": "test"},
                "expected_hash": planned["operation_id"], "visibility_change": False}
    monkeypatch.setattr(authorization, "require_authorization", lambda *unused: {"scope": json.dumps(approved)})
    grant_args = parser().parse_args(["grant", "--grant-action", "archive", "--subject", "project:test",
        "--source", str(source), "--kind", "validation", "--sanitized", "--declaration-file", str(request),
        "--authorization-id", "reviewed-archive", "--apply"])
    result = provider_grants.issue_grant(root, grant_args)
    assert result["status"] == "GRANTED" and result["expected_hash"] == planned["operation_id"]
    source.write_text("# 不同结论\n\n新内容。\n")
    before = (root / "registry/provider-grants.jsonl").read_bytes()
    with pytest.raises(KnowledgeHubError, match="POLICY_DENIED"):
        provider_grants.issue_grant(root, grant_args)
    assert (root / "registry/provider-grants.jsonl").read_bytes() == before


def test_discovery_respects_small_budget_with_larger_limit(tmp_path):
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, source, args = subject_root(tmp_path)
    for number in range(5):
        source.write_text(f"# 公共候选 {number}\n\n事务记录。\n")
        archive(root, args)
    query = parser().parse_args(["context", "--cwd", str(tmp_path), "--query", "事务", "--limit", "16", "--context-budget", "small"])
    result = run(root, query)
    assert result["retrieval_scope"] == []
    assert sum(len(group["items"]) for group in result["context"]) <= 3


def test_body_hit_is_not_discarded_by_metadata_budget(tmp_path):
    from tools.codex_assets.knowledge_hub.provider_cli import run
    root, source, args = subject_root(tmp_path)
    for number in range(4):
        source.write_text(f"# 普通知识 {number}\n\n普通结论。\n")
        archive(root, args)
    rows = sorted(load_jsonl(root / "registry/items.jsonl"), key=lambda row: row["id"])
    path = root / rows[-1]["path"]
    path.write_text(path.read_text() + "\nuniquebodyneedle\n")
    query = parser().parse_args(["context", "--cwd", str(tmp_path), "--query", "uniquebodyneedle", "--retrieval-project", "test"])
    result = run(root, query)
    assert rows[-1]["id"] in {row.get("id", row.get("item_id")) for group in result["context"] for row in group["items"]}


@pytest.mark.parametrize("value", ["", "a", "z" * 64])
def test_assignment_requires_exact_content_hash(tmp_path, value):
    root, _, args = subject_root(tmp_path)
    result = archive(root, args)
    move = parser().parse_args(["assign", "--subject", "personal:local-user", "--item-id", result["item_id"], "--apply"])
    move.expected_content_sha256 = value
    before = (root / "registry/items.jsonl").read_bytes()
    with pytest.raises(KnowledgeHubError, match="CONTENT_HASH_REQUIRED"):
        assign(root, move)
    assert (root / "registry/items.jsonl").read_bytes() == before


def test_assignment_cannot_accept_drift_even_with_changed_hash(tmp_path):
    root, _, args = subject_root(tmp_path)
    args.subject = "personal:local-user"
    result = archive(root, args)
    row = load_jsonl(root / "registry/items.jsonl")[0]
    path = root / row["path"]
    path.write_text(path.read_text() + "\n追加未经归档验证的正文。\n")
    changed_hash = file_sha256(path)
    move = parser().parse_args(["assign", "--subject", "project:test", "--item-id", result["item_id"],
                               "--expected-content-sha256", changed_hash, "--apply"])
    move.from_subject = "personal:local-user"
    request_hash, _, _ = assignment_request(root, move, "validation")
    move.authorization_id = grant(root, "assign", {"type": "project", "id": "test"}, request_hash, visibility_change=True)
    before = (root / "registry/items.jsonl").read_bytes()
    with pytest.raises(KnowledgeHubError, match="CONTENT_DRIFT"):
        assign(root, move)
    assert reconcile(root, result["operation_id"], changed_hash)["status"] == "CONFLICT"
    assert (root / "registry/items.jsonl").read_bytes() == before


def test_missing_existence_proof_never_certifies_corrupted_backup(tmp_path):
    import hashlib
    root, _, _ = subject_root(tmp_path)
    target = root / "candidate.txt"
    target.write_text("after")
    directory = root / ".tmp/transactions/broken"
    (directory / "before").mkdir(parents=True)
    (directory / "before/candidate.txt").write_text("corrupted")
    journal = {"schema_version": 1, "status": "applying", "writes": [{"path": "candidate.txt",
               "before_sha256": hashlib.sha256(b"before").hexdigest(), "after_sha256": hashlib.sha256(b"after").hexdigest()}],
               "applied_paths": ["candidate.txt"]}
    (directory / "journal.json").write_text(json.dumps(journal))
    report = audit_transactions(root)
    assert report["rows"][0]["recoverable"] is False
    assert target.read_text() == "after"
