import argparse
import datetime as dt
import json
import pathlib

import pytest

from test_provider_archive import setup
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_jsonl, file_sha256
from tools.codex_assets.knowledge_hub.provider_subjects import digest, OPERATIONS_PATH, GRANTS_PATH, BINDINGS_PATH
from tools.codex_assets.knowledge_hub.provider_operations import archive_v2, assign, reconcile, import_legacy
from tools.codex_assets.knowledge_hub.provider_onboarding import register_project, bind_workspace, resolve_workspace
from tools.codex_assets.knowledge_hub.provider_cli import parser, run, main
from tools.codex_assets.knowledge_hub.store import RepositoryTransaction


def subject_root(tmp_path):
    root, source, old = setup(tmp_path)
    (root / "local").mkdir()
    (root / "local/activity-report.json").write_text(json.dumps({"schema_version": 2, "enabled": True,
        "default_scope": "personal", "subject_id": "local-user", "receipt_persistence": True}))
    policy = pathlib.Path(__file__).parents[1] / "registry/provider-subject-policy.json"
    (root / "registry/provider-subject-policy.json").write_bytes(policy.read_bytes())
    (root / "registry/provider-workspaces.json").write_text('{"schema_version":1,"workspaces":[]}')
    (root / "registry/repositories.json").write_text('{"repositories":[]}')
    (root / "registry/projects.json").write_text('{"schema_version":1,"projects":[]}')
    (root / "registry/project-groups.json").write_text('{"groups":[]}')
    (root / "registry/retired-sources.jsonl").write_text("")
    (root / "registry/sources.json").write_text('{"sources":[]}')
    product = json.loads((pathlib.Path(__file__).parents[1] / "registry/product-policy.json").read_text())
    product["project_readiness_extensions"] = []
    product["specialized_owner_requirements"] = []
    (root / "registry/product-policy.json").write_text(json.dumps(product))
    args = parser().parse_args(["archive", "--subject", "project:test", "--source", str(source), "--kind", "validation", "--sanitized", "--apply"])
    return root, source, args


def grant(root, action, target, expected_hash, **extra):
    rows = load_jsonl(root / GRANTS_PATH)
    ident = "grant-" + expected_hash[:20]
    rows.append({"id": ident, "actor": "local-user", "action": action, "subject_ref": target,
                 "expected_hash": expected_hash, "status": "active", "expires_at": (dt.date.today() + dt.timedelta(days=1)).isoformat(),
                 "visibility_change": False, **extra})
    from tools.codex_assets.knowledge_hub.common import encode_jsonl
    (root / GRANTS_PATH).write_text(encode_jsonl(rows))
    return ident


@pytest.mark.parametrize("target", ["project:test", "domain:embedded", "domain:codex", "personal:local-user", "unassigned:local-user"])
def test_all_subjects_archive_without_git_and_retry(tmp_path, target):
    root, source, args = subject_root(tmp_path)
    assert not (root / ".git").exists()
    args.subject, args.declared_scope = target, "team-general"
    first = archive_v2(root, args)
    assert first["status"] == "ARCHIVED" and first["persisted"] is True
    assert first["candidate_status"] == "reviewing" and first["promotion"] == "none"
    assert first["project_archived"] == target.startswith("project:")
    second = archive_v2(root, args)
    assert second["status"] == "ALREADY_ARCHIVED" and second["write_performed"] is False
    assert len(load_jsonl(root / "registry/items.jsonl")) == 1
    assert reconcile(root, first["operation_id"], first["content_sha256"])["status"] == "VERIFIED"


@pytest.mark.parametrize("target", ["personal:other", "unassigned:other", "domain:patents", "project:unknown"])
def test_subject_denials_have_no_effect(tmp_path, target):
    root, _, args = subject_root(tmp_path)
    args.subject = target
    args.declared_scope = "team-general"
    with pytest.raises(KnowledgeHubError):
        archive_v2(root, args)
    assert load_jsonl(root / "registry/items.jsonl") == []
    assert not (root / OPERATIONS_PATH).exists()


def test_assign_keeps_id_and_replays_creation_after_move(tmp_path):
    root, _, args = subject_root(tmp_path)
    args.subject = "unassigned:local-user"
    first = archive_v2(root, args)
    old_path = load_jsonl(root / "registry/items.jsonl")[0]["path"]
    move = parser().parse_args(["assign", "--subject", "project:test", "--item-id", first["item_id"],
                               "--expected-content-sha256", first["content_sha256"], "--apply"])
    request_hash = digest({"action": "assign", "item_id": first["item_id"], "subject_ref": {"type": "project", "id": "test"},
                           "expected_content_sha256": first["content_sha256"]})
    move.authorization_id = grant(root, "assign", {"type": "project", "id": "test"}, request_hash, visibility_change=True)
    result = assign(root, move)
    assert result["status"] == "ASSIGNED" and result["item_id"] == first["item_id"]
    assert not (root / old_path).exists()
    assert assign(root, move)["status"] == "ALREADY_ASSIGNED"
    assert archive_v2(root, args)["subject_ref"] == {"type": "project", "id": "test"}
    assert len(load_jsonl(root / "registry/items.jsonl")) == 1


def test_assign_authorization_is_exact_not_substring(tmp_path):
    root, _, args = subject_root(tmp_path)
    first = archive_v2(root, args)
    move = parser().parse_args(["assign", "--subject", "personal:local-user", "--item-id", first["item_id"],
                               "--expected-content-sha256", first["content_sha256"], "--apply"])
    move.authorization_id = grant(root, "assign", {"type": "personal", "id": "local-user-extra"}, "0" * 64, visibility_change=True)
    before = (root / "registry/items.jsonl").read_bytes()
    with pytest.raises(KnowledgeHubError):
        assign(root, move)
    assert (root / "registry/items.jsonl").read_bytes() == before


def test_authorized_non_git_register_bind_and_discovery_boundary(tmp_path):
    root, _, _ = subject_root(tmp_path)
    declaration = tmp_path / "request.txt"
    declaration.write_text("为 alpha 项目登记这个工作目录")
    planned = register_project(root, "alpha", "Alpha", str(declaration))
    auth = grant(root, "register", planned["subject_ref"], planned["expected_hash"], declaration_sha256=planned["declaration_sha256"])
    assert register_project(root, "alpha", "Alpha", str(declaration), auth, True)["status"] == "REGISTERED"
    directory = tmp_path / "plain"
    directory.mkdir()
    (directory / "child").mkdir()
    planned = bind_workspace(root, "workspace://alpha", str(directory))
    auth = grant(root, "bind", planned["subject_ref"], planned["expected_hash"], binding_path_sha256=planned["binding_path_sha256"])
    assert bind_workspace(root, "workspace://alpha", str(directory), authorization_id=auth, apply=True)["status"] == "BOUND"
    assert resolve_workspace(root, str(directory / "child"))["subject_ref"] == {"type": "project", "id": "alpha"}
    assert resolve_workspace(root, str(directory) + "-other")["state"] == "unresolved"
    original = (root / BINDINGS_PATH).read_bytes()
    from tools.codex_assets.knowledge_hub.workspace_discovery import discover_workspaces
    discover_workspaces(root, [tmp_path], apply=True)
    assert (root / BINDINGS_PATH).read_bytes() == original
    from tools.codex_assets.knowledge_hub.project_readiness import _route_document
    from tools.codex_assets.knowledge_hub.common import project_rows, route_rows
    routes = _route_document(project_rows(root), [], [], route_rows(root), [], set())
    assert next(r for r in routes["routes"] if r["project_id"] == "alpha")["repo_refs"] == []


def test_directory_replacement_is_stale_not_verified(tmp_path):
    root, _, _ = subject_root(tmp_path)
    directory = tmp_path / "work"
    directory.mkdir()
    (root / "registry/provider-workspaces.json").write_text('{"schema_version":1,"workspaces":[{"workspace_ref":"workspace://test","subject_ref":{"type":"project","id":"test"}}]}')
    planned = bind_workspace(root, "workspace://test", str(directory))
    auth = grant(root, "bind", planned["subject_ref"], planned["expected_hash"], binding_path_sha256=planned["binding_path_sha256"])
    bind_workspace(root, "workspace://test", str(directory), authorization_id=auth, apply=True)
    directory.rename(tmp_path / "previous")
    directory.mkdir()
    result = resolve_workspace(root, str(directory))
    assert result["state"] == "unresolved" and "WORKSPACE_STALE" in result["reason_codes"]


@pytest.mark.parametrize("change", [{"enabled": "false"}, {"mode": "report-only"}, {"maximum_bytes": 1}, {"owner_id": "unknown-owner"}])
def test_archive_policy_denials_are_zero_write(tmp_path, change):
    root, _, args = subject_root(tmp_path)
    policy_path = root / "registry/provider-archive-policy.json"
    policy = json.loads(policy_path.read_text())
    policy.update(change)
    policy_path.write_text(json.dumps(policy))
    before = (root / "registry/items.jsonl").read_bytes()
    with pytest.raises(KnowledgeHubError):
        archive_v2(root, args)
    assert (root / "registry/items.jsonl").read_bytes() == before
    assert not (root / OPERATIONS_PATH).exists()


def test_bind_revoked_before_snapshot_is_denied(tmp_path, monkeypatch):
    root, _, _ = subject_root(tmp_path)
    directory = tmp_path / "work"
    directory.mkdir()
    (root / "registry/provider-workspaces.json").write_text('{"schema_version":1,"workspaces":[{"workspace_ref":"workspace://test","subject_ref":{"type":"project","id":"test"}}]}')
    planned = bind_workspace(root, "workspace://test", str(directory))
    auth = grant(root, "bind", planned["subject_ref"], planned["expected_hash"], binding_path_sha256=planned["binding_path_sha256"])
    from tools.codex_assets.knowledge_hub import provider_onboarding
    original = provider_onboarding.snapshot_inputs
    def revoke_then_snapshot(candidate):
        rows = load_jsonl(candidate / GRANTS_PATH)
        rows[0]["status"] = "revoked"
        from tools.codex_assets.knowledge_hub.common import encode_jsonl
        (candidate / GRANTS_PATH).write_text(encode_jsonl(rows))
        return original(candidate)
    monkeypatch.setattr(provider_onboarding, "snapshot_inputs", revoke_then_snapshot)
    with pytest.raises(KnowledgeHubError):
        bind_workspace(root, "workspace://test", str(directory), authorization_id=auth, apply=True)
    assert not (root / BINDINGS_PATH).exists()


def test_legacy_codex_lane_reconcile_and_v2_replay(tmp_path):
    root, source, args = subject_root(tmp_path)
    routes_path = root / "registry/project-routes.json"
    routes = json.loads(routes_path.read_text())
    routes["routes"][0]["validation_path"] = "domains/codex/validation"
    routes_path.write_text(json.dumps(routes))
    from tools.codex_assets.knowledge_hub.provider_archive import archive
    legacy_args = argparse.Namespace(project="test", source=str(source), kind="validation", title="", sanitized=True, apply=True, as_of="")
    first = archive(root, legacy_args)
    assert import_legacy(root, True)["status"] == "IMPORTED"
    row = load_jsonl(root / OPERATIONS_PATH)[0]
    verified = reconcile(root, first["operation_id"], row["current_content_sha256"])
    assert verified["status"] == "VERIFIED"
    assert verified["subject_ref"] == {"type":"project", "id":"test"}
    replay = archive_v2(root, args)
    assert replay["status"] == "ALREADY_ARCHIVED" and replay["item_id"] == first["item_id"]
    assert len(load_jsonl(root / "registry/items.jsonl")) == 1


def test_irrelevant_write_flag_is_not_silently_ignored(tmp_path):
    root, _, _ = subject_root(tmp_path)
    args = parser().parse_args(["resolve", "--subject", "project:test"])
    with pytest.raises(KnowledgeHubError):
        run(root, args)


def test_context_archive_eligibility_respects_disabled_policy(tmp_path):
    root, _, _ = subject_root(tmp_path)
    path = root / "registry/provider-archive-policy.json"
    value = json.loads(path.read_text())
    value["enabled"] = False
    path.write_text(json.dumps(value))
    args = parser().parse_args(["context", "--api-version", "3", "--cwd", str(tmp_path), "--execution-project", "test", "--query", "事务"])
    result = run(root, args)
    assert result["archive_eligibility"]["eligible"] is False
    assert "POLICY_DENIED" in result["archive_eligibility"]["reason_codes"]


def test_linked_worktree_uses_common_remote_but_own_head(tmp_path):
    from tools.codex_assets.knowledge_hub.context_support import find_git_config, workspace_git_head, remote_urls_from_config
    common = tmp_path / "main/.git"
    linked = common / "worktrees/feature"
    linked.mkdir(parents=True)
    (common / "refs/heads").mkdir(parents=True)
    (common / "config").write_text('[remote "origin"]\n url = https://example.org/team/project.git\n')
    (common / "HEAD").write_text("ref: refs/heads/main\n")
    (common / "refs/heads/main").write_text("1" * 40 + "\n")
    (common / "refs/heads/feature").write_text("2" * 40 + "\n")
    (linked / "HEAD").write_text("ref: refs/heads/feature\n")
    (linked / "commondir").write_text("../..\n")
    work = tmp_path / "linked"
    work.mkdir()
    (work / ".git").write_text("gitdir: " + str(linked) + "\n")
    config, root = find_git_config(str(work))
    assert config == common / "config" and root == work
    assert remote_urls_from_config(config)[0]["remote_key"] == "team/project"
    assert workspace_git_head(str(work), config) == "2" * 40


def test_explicit_logical_workspace_without_git_and_conflict(tmp_path):
    root, _, _ = subject_root(tmp_path)
    (root / "registry/provider-workspaces.json").write_text('{"schema_version":1,"workspaces":[{"workspace_ref":"workspace://test","subject_ref":{"type":"project","id":"test"}}]}')
    args = parser().parse_args(["context", "--api-version", "3", "--cwd", str(tmp_path), "--workspace", "workspace://test", "--query", "事务"])
    value = run(root, args)
    assert value["execution_subject"] == {"type":"project", "id":"test"}
    assert value["source_state"]["vcs"] == "none" and value["archive_eligibility"]["eligible"] is True
    args.retrieval_domain = "codex"
    assert run(root, args)["retrieval_scope"] == [{"type":"domain", "id":"codex"}]
    (root / "registry/provider-workspaces.json").write_text('{"schema_version":1,"workspaces":[{"workspace_ref":"workspace://codex","subject_ref":{"type":"domain","id":"codex"}}]}')
    args.workspace, args.execution_project = "workspace://codex", "test"
    with pytest.raises(KnowledgeHubError, match="ROUTE_CONFLICT"):
        run(root, args)


def test_private_queries_are_explicit_and_cache_invalidates(tmp_path):
    root, _, args = subject_root(tmp_path)
    args.subject = "personal:local-user"
    first = archive_v2(root, args)
    query = parser().parse_args(["context", "--api-version", "3", "--cwd", str(tmp_path), "--query", "事务", "--summary-json", "--personal", "--receipt-key", "own"])
    value = run(root, query)
    assert value["cache"]["hit"] is False
    assert value["context"][0]["items"][0]["id"] == first["item_id"]
    assert run(root, query)["cache"]["hit"] is True
    from tools.codex_assets.knowledge_hub.common import load_json
    host = load_json(root / "registry/provider-subject-policy.json")
    host["authorization_basis"] += " revised"
    (root / "registry/provider-subject-policy.json").write_text(json.dumps(host))
    assert run(root, query)["cache"]["hit"] is False
    query.personal, query.receipt_key = False, ""
    default = run(root, query)
    assert all(first["item_id"] not in str(g) for g in default["context"])


def test_retrieval_project_does_not_change_execution(tmp_path):
    root, _, _ = subject_root(tmp_path)
    query = parser().parse_args(["context", "--api-version", "3", "--cwd", str(tmp_path), "--query", "事务", "--retrieval-project", "test"])
    result = run(root, query)
    assert result["execution_subject"] is None
    assert result["retrieval_scope"] == [{"type": "project", "id": "test"}]
    assert result["archive_eligibility"]["eligible"] is False


def test_delete_rollback_and_interrupted_journal_block(tmp_path, monkeypatch):
    root, _, _ = subject_root(tmp_path)
    path = root / "temporary.md"
    path.write_text("original")
    before = file_sha256(path)
    transaction = RepositoryTransaction(root)
    transaction.add_delete("temporary.md", before)
    transaction.add_text("z-later.md", "later")
    import tools.codex_assets.knowledge_hub.store as module
    original = module.os.replace
    def fail_later(source, target):
        if str(target).endswith("z-later.md"):
            raise OSError("fault")
        return original(source, target)
    monkeypatch.setattr(module.os, "replace", fail_later)
    with pytest.raises(KnowledgeHubError):
        transaction.apply()
    assert path.read_text() == "original"
    monkeypatch.setattr(module.os, "replace", original)
    journal = root / ".tmp/transactions/interrupted/journal.json"
    journal.parent.mkdir()
    journal.write_text('{"schema_version":1,"status":"applying","writes":[],"applied_paths":[]}')
    with pytest.raises(KnowledgeHubError, match="STORAGE_RECOVERY_REQUIRED"):
        run(root, parser().parse_args(["resolve", "--cwd", str(tmp_path)]))


def test_unknown_after_commit_has_operation_for_reconciliation(tmp_path, monkeypatch, capsys):
    root, source, _ = subject_root(tmp_path)
    from tools.codex_assets.knowledge_hub import provider_operations as module
    original = module.verify_item
    def fail_readback(*a, **kw):
        raise OSError("readback fault")
    monkeypatch.setattr(module, "verify_item", fail_readback)
    assert main(["archive", "--root", str(root), "--subject", "project:test", "--source", str(source),
                 "--kind", "validation", "--sanitized", "--apply"]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "UNKNOWN" and result["persisted"] is None and result["operation_id"]
    monkeypatch.setattr(module, "verify_item", original)
    assert reconcile(root, result["operation_id"])["status"] == "PRESENT_UNVERIFIED"
