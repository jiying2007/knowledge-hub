import json

import pytest

from test_provider_subjects import subject_root, grant
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError, load_json
from tools.codex_assets.knowledge_hub.provider_repositories import registration
from tools.codex_assets.knowledge_hub.provider_onboarding import resolve_workspace
from tools.codex_assets.knowledge_hub.provider_cli import parser, run, main
from tools.codex_assets.knowledge_hub.provider_grants import issue_grant


URL = "ssh://git@example.test:10022/robot/a123x/integration.git"


def setup_project(tmp_path):
    root, _, _ = subject_root(tmp_path)
    (root / "registry/projects.json").write_text('{"projects":[{"id":"test","name":"Test"}]}')
    return root


def authorize(root, remote=URL, repository_id="a123x-integration"):
    plan = registration(root, "test", repository_id, remote)
    return grant(root, "register", plan["subject_ref"], plan["expected_hash"])


def test_plan_is_zero_write_and_exact_register_is_idempotent(tmp_path):
    root = setup_project(tmp_path)
    before = (root / "registry/repositories.json").read_bytes()
    plan = registration(root, "test", "a123x-integration", URL)
    assert plan["status"] == "PLANNED" and plan["persisted"] is False
    assert (root / "registry/repositories.json").read_bytes() == before
    auth = authorize(root)
    result = registration(root, "test", "a123x-integration", URL, auth, True)
    assert result["status"] == "REGISTERED" and result["persisted"] is True
    assert set(result["transaction"]["changed_paths"]) == {"registry/repositories.json", "registry/project-routes.json"}
    value = load_json(root / "registry/repositories.json")
    assert len(value["repositories"]) == 1
    assert str(tmp_path) not in json.dumps(value)
    assert "example.test" not in json.dumps(value)  # only normalized identity, no URL or credential
    assert load_json(root / "registry/project-routes.json")["routes"][0]["repo_refs"] == ["a123x-integration"]
    second = registration(root, "test", "a123x-integration", URL, auth, True)
    assert second["status"] == "ALREADY_REGISTERED" and second["write_performed"] is False


def test_clones_relocation_private_ports_and_unknown_repositories(tmp_path):
    root = setup_project(tmp_path)
    registration(root, "test", "a123x-integration", URL, authorize(root), True)
    checkout = tmp_path / "first-clone"
    (checkout / ".git").mkdir(parents=True)
    config = checkout / ".git/config"
    config.write_text('[remote "origin"]\n url = ' + URL + '\n')
    assert resolve_workspace(root, checkout)["subject_ref"] == {"type": "project", "id": "test"}
    moved = tmp_path / "elsewhere"
    checkout.rename(moved)
    assert resolve_workspace(root, moved)["subject_ref"] == {"type": "project", "id": "test"}
    (moved / ".git/config").write_text('[remote "origin"]\n url = ' + URL.replace(':10022', ':10023') + '\n')
    assert resolve_workspace(root, moved)["state"] == "unresolved"
    (moved / ".git/config").write_text('[remote "origin"]\n url = ' + URL.replace('integration.git', 'unknown.git') + '\n')
    assert resolve_workspace(root, moved)["state"] == "unresolved"


def test_legacy_reserved_ids_without_remote_are_preserved(tmp_path):
    root = setup_project(tmp_path)
    path = root / 'registry/repositories.json'
    legacy = [{"repo_id": "legacy-a", "project_id": "legacy-a", "remote_key": None, "status": "registered"},
              {"repo_id": "legacy-b", "project_id": "legacy-b", "status": "registered"}]
    path.write_text(json.dumps({"repositories": legacy}))
    registration(root, 'test', 'a123x-integration', URL, authorize(root), True)
    assert load_json(path)['repositories'][:2] == legacy
    with pytest.raises(KnowledgeHubError, match='ROUTE_CONFLICT'):
        registration(root, 'test', 'legacy-a', URL.replace('integration.git', 'other.git'))


@pytest.mark.parametrize("repo,remote,project", [
    ("other-id", URL, "test"),
    ("a123x-integration", URL.replace('integration.git', 'other.git'), "test"),
    ("a123x-integration", URL, "other"),
])
def test_conflicts_cannot_reassign_or_overwrite(tmp_path, repo, remote, project):
    root = setup_project(tmp_path)
    registration(root, "test", "a123x-integration", URL, authorize(root), True)
    projects = load_json(root / "registry/projects.json")
    projects["projects"].append({"id": "other"})
    (root / "registry/projects.json").write_text(json.dumps(projects))
    routes = load_json(root / "registry/project-routes.json")
    routes["routes"].append({"project_id": "other", "repo_refs": []})
    (root / "registry/project-routes.json").write_text(json.dumps(routes))
    before = (root / "registry/repositories.json").read_bytes()
    with pytest.raises(KnowledgeHubError, match="ROUTE_CONFLICT"):
        registration(root, project, repo, remote)
    assert (root / "registry/repositories.json").read_bytes() == before


@pytest.mark.parametrize("remote", ["/data/local", "file:///data/local", "https://token@example.test/repo", "https://user:pass@example.test/repo", "ssh://git@example.test/repo?token=secret", "ssh://git@example.test/a/../b"])
def test_unsafe_identity_is_rejected_without_echo(tmp_path, capsys, remote):
    root = setup_project(tmp_path)
    assert main(["register-repository", "--root", str(root), "--project", "test", "--repository-id", "sample", "--remote-url", remote]) == 2
    output = capsys.readouterr().out
    assert remote not in output and '"write_performed":false' in output


def test_requires_existing_project_and_exact_grant(tmp_path):
    root = setup_project(tmp_path)
    with pytest.raises(KnowledgeHubError, match="PROJECT_UNREGISTERED"):
        registration(root, "missing", "sample", URL)
    with pytest.raises(KnowledgeHubError, match="AUTHORIZATION_REQUIRED"):
        registration(root, "test", "sample", URL, apply=True)
    wrong = authorize(root, repository_id="another")
    with pytest.raises(KnowledgeHubError, match="POLICY_DENIED"):
        registration(root, "test", "sample", URL, wrong, True)


def test_attested_contextual_request_grants_only_resolved_project(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    checkout = tmp_path / "caller"
    (checkout / ".git").mkdir(parents=True)
    (checkout / ".git/config").write_text('[remote "origin"]\n url = ' + URL + '\n')
    registration(root, "test", "a123x-integration", URL, authorize(root), True)
    request = tmp_path / "request.txt"
    request.write_text("按已审查建议执行")
    from tools.codex_assets.knowledge_hub import provider_grants
    monkeypatch.setattr(provider_grants, "attested_request", lambda raw, path: ("a" * 64, "b" * 64))
    args = parser().parse_args(["grant", "--grant-action", "register", "--project", "test", "--repository-id", "project-docs",
                                "--remote-url", URL.replace('integration.git', 'project.git'), "--cwd", str(checkout),
                                "--declaration-file", str(request), "--apply"])
    issued = issue_grant(root, args)
    assert issued["status"] == "GRANTED"
    registration(root, "test", "project-docs", args.remote_url, issued["authorization_id"], True)
    args.cwd = str(tmp_path / "unknown")
    with pytest.raises(KnowledgeHubError, match="ROUTE_CONFLICT"):
        issue_grant(root, args)


def test_revocation_after_snapshot_and_cli_parameter_boundaries(tmp_path, monkeypatch):
    root = setup_project(tmp_path)
    auth = authorize(root)
    from tools.codex_assets.knowledge_hub import provider_repositories
    original = provider_repositories.snapshot_inputs
    def revoke(candidate):
        path = root / 'registry/provider-grants.jsonl'
        path.write_text(path.read_text().replace('"active"', '"revoked"'))
        return original(candidate)
    monkeypatch.setattr(provider_repositories, 'snapshot_inputs', revoke)
    with pytest.raises(KnowledgeHubError, match="POLICY_DENIED"):
        registration(root, "test", "a123x-integration", URL, auth, True)
    assert load_json(root / "registry/repositories.json")["repositories"] == []
    args = parser().parse_args(["resolve", "--repository-id", "sample"])
    with pytest.raises(KnowledgeHubError):
        run(root, args)


@pytest.mark.parametrize("change", ["checkout", "registry"])
def test_grant_rejects_boundary_changes_after_scope(tmp_path, monkeypatch, change):
    root = setup_project(tmp_path)
    registration(root, "test", "a123x-integration", URL, authorize(root), True)
    checkout = tmp_path / "caller"
    (checkout / '.git').mkdir(parents=True)
    config = checkout / '.git/config'
    config.write_text('[remote "origin"]\n url = ' + URL + '\n')
    request = tmp_path / 'request.txt'
    request.write_text('按已审查建议执行')
    from tools.codex_assets.knowledge_hub import provider_grants
    monkeypatch.setattr(provider_grants, 'attested_request', lambda raw, path: ('a' * 64, 'b' * 64))
    original = provider_grants._grant_action_scope
    def changed_scope(*args):
        result = original(*args)
        if change == 'checkout':
            config.write_text('[remote "origin"]\n url = ssh://git@unknown.test/new/repo.git\n')
        else:
            path = root / 'registry/repositories.json'
            path.write_text('{"repositories":[]}')
        return result
    monkeypatch.setattr(provider_grants, '_grant_action_scope', changed_scope)
    args = parser().parse_args(['grant', '--grant-action', 'register', '--project', 'test', '--repository-id', 'project-docs',
                               '--remote-url', URL.replace('integration.git', 'project.git'), '--cwd', str(checkout),
                               '--declaration-file', str(request), '--apply'])
    before = (root / 'registry/provider-grants.jsonl').read_bytes()
    with pytest.raises(KnowledgeHubError):
        issue_grant(root, args)
    assert (root / 'registry/provider-grants.jsonl').read_bytes() == before
