import json

import pytest

from tools.codex_assets.knowledge_hub.agent_runtime import (
    build_evidence_pack,
    check_action,
)
from tools.codex_assets.knowledge_hub.model import validate_item
from tools.codex_assets.knowledge_hub.common import repository_root
from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.schemas import validate_instance


def _contract(role, force="advisory", **extra):
    value = {"schema_version": 1, "role": role, "force": force}
    value.update(extra)
    return value


def _root(tmp_path):
    (tmp_path / "registry").mkdir()
    (tmp_path / "governance").mkdir()
    rows = [
        {
            "id": "no-force-push",
            "title": "No force push",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/no-force.md",
            "status": "active",
            "owner": "owner-a",
            "summary_zh": "禁止强制推送主分支。",
            "tags": ["git", "push"],
            "agent_contract": _contract(
                "constraint",
                "hard",
                subject="Repository.Demo",
                scope_refs=["repository:demo"],
                capabilities=["searchable", "enforceable", "guardable"],
                guard={"when_any": ["push", "main"], "deny_any": ["--force", "--force-with-lease"]},
                exceptions=["explicit-owner-authorization"],
            ),
        },
        {
            "id": "candidate-constraint",
            "title": "Candidate rule",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/candidate.md",
            "status": "reviewing",
            "owner": "owner-a",
            "summary_zh": "尚未生效的候选规则。",
            "tags": ["git", "push"],
            "agent_contract": _contract(
                "constraint",
                "hard",
                scope_refs=["repository:demo"],
                capabilities=["searchable", "enforceable", "guardable"],
                guard={"when_any": ["push"], "deny_any": ["origin"]},
            ),
        },
        {
            "id": "repo-fact",
            "title": "Repository fact",
            "kind": "project-current",
            "domain": "governance",
            "path": "governance/fact.md",
            "status": "active",
            "owner": "owner-a",
            "summary_zh": "demo 仓库主分支是 main。",
            "tags": ["demo", "main"],
            "agent_contract": _contract("assertion", "advisory", scope_refs=["repository:demo"]),
        },
        {
            "id": "open-question",
            "title": "Open question",
            "kind": "validation",
            "domain": "governance",
            "path": "governance/question.md",
            "status": "active",
            "owner": "owner-a",
            "summary_zh": "demo 发布窗口尚未确认。",
            "tags": ["demo", "release"],
            "agent_contract": _contract("question", "advisory", scope_refs=["repository:demo"]),
        },
        {
            "id": "archived-rule",
            "title": "Archived rule",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/archived.md",
            "status": "archived",
            "owner": "owner-a",
            "summary_zh": "已经归档的旧规则。",
            "tags": ["git", "push"],
            "agent_contract": _contract(
                "constraint",
                "hard",
                scope_refs=["repository:demo"],
                capabilities=["searchable", "enforceable", "guardable"],
                guard={"when_any": ["push"], "deny_any": ["origin"]},
            ),
        },
    ]
    for row in rows:
        (tmp_path / row["path"]).write_text("# {}\n\n{}\n".format(row["title"], row["summary_zh"]))
    (tmp_path / "registry/items.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    )
    (tmp_path / "registry/sources.json").write_text('{"sources": []}\n')
    (tmp_path / "registry/retired-sources.jsonl").write_text("")
    return tmp_path


def test_evidence_pack_keeps_candidate_constraint_provisional(tmp_path):
    root = _root(tmp_path)
    pack = build_evidence_pack(
        root,
        "push main demo",
        scope_refs=["repository:demo"],
    )

    assert [row["id"] for row in pack["must"]] == ["no-force-push"]
    assert "candidate-constraint" in [row["id"] for row in pack["provisional"]]
    assert "candidate-constraint" not in [row["id"] for row in pack["must"]]
    assert "archived-rule" not in [row["id"] for row in pack["provisional"]]
    assert any(
        row["id"] == "archived-rule"
        for row in pack["search_trace"]["lifecycle_excluded"]
    )
    assert "repo-fact" in [row["id"] for row in pack["context"]]
    assert pack["authority_contract"]["candidate_constraints_enforced"] is False
    assert validate_instance(repository_root(), "agent-evidence-pack-v1", pack)["status"] == "pass"


def test_action_check_blocks_active_rule_and_ignores_candidate_rule(tmp_path):
    root = _root(tmp_path)
    result = check_action(
        root,
        "push main",
        "git push --force origin main",
        scope_refs=["repository:demo"],
    )

    assert result["verdict"] == "BLOCK"
    assert [row["id"] for row in result["violations"]] == ["no-force-push"]
    assert [row["id"] for row in result["provisional_constraints"]] == [
        "candidate-constraint"
    ]
    assert validate_instance(repository_root(), "agent-action-check-v1", result)["status"] == "pass"


def test_action_check_allows_only_after_explicit_rules_evaluate(tmp_path):
    root = _root(tmp_path)
    allowed = check_action(
        root,
        "push main",
        "git push origin main",
        scope_refs=["repository:demo"],
    )
    unknown_scope = check_action(
        root,
        "deploy",
        "deploy service",
        scope_refs=["repository:other"],
    )

    assert allowed["verdict"] == "ALLOW"
    assert unknown_scope["verdict"] == "NEEDS_REVIEW"


def test_candidate_hit_cannot_consume_active_evidence_limit(tmp_path):
    root = _root(tmp_path)
    items_path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in items_path.read_text().splitlines() if line]
    active = next(row for row in rows if row["id"] == "repo-fact")
    active["summary_zh"] = "active exact candidate beacon fact"
    candidate = {
        "id": "candidate-exact-beacon",
        "title": "exact candidate beacon",
        "kind": "project-current",
        "domain": "governance",
        "path": "governance/candidate-beacon.md",
        "status": "reviewing",
        "owner": "owner-a",
        "summary_zh": "candidate exact candidate beacon observation",
        "tags": ["exact", "candidate", "beacon"],
        "agent_contract": _contract("assertion", "advisory"),
    }
    (root / candidate["path"]).write_text("# exact candidate beacon\n")
    rows.append(candidate)
    items_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    )

    pack = build_evidence_pack(root, "exact candidate beacon", limit=1)

    assert [row["id"] for row in pack["context"]] == ["repo-fact"]
    assert [row["id"] for row in pack["provisional"]] == [
        "candidate-exact-beacon"
    ]
    assert pack["active_search_trace"]["schema_version"] == (
        "knowledge-hub.search-trace.v1"
    )
    assert pack["authority_contract"]["candidate_hits_consume_active_limit"] is False


def test_item_validation_rejects_nondeterministic_guard_contract():
    item = {
        "agent_contract": _contract(
            "constraint",
            "hard",
            guard={"deny_any": ["danger"]},
            capabilities=["searchable"],
        )
    }
    errors = validate_item(item)
    assert "agent_contract guard requires enforceable and guardable capabilities" in errors


def test_item_validation_reports_non_string_contract_values_without_crashing():
    item = {
        "agent_contract": _contract(
            "constraint",
            "hard",
            capabilities=[{"not": "a string"}],
            guard={"deny_regex": [{"not": "a regex"}]},
            relations={"conflicts_with": [{"not": "an id"}]},
        )
    }

    errors = validate_item(item)

    assert "agent_contract capabilities must contain non-empty strings" in errors
    assert "agent_contract guard.deny_regex must contain non-empty strings" in errors
    assert "agent_contract relations.conflicts_with must contain non-empty strings" in errors


def test_evidence_pack_rejects_unbounded_limit(tmp_path):
    with pytest.raises(KnowledgeHubError, match="limit must be between"):
        build_evidence_pack(_root(tmp_path), "demo", limit=101)


def test_action_check_rejects_unbounded_task_scope_and_exceptions(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="task exceeds"):
        check_action(root, "t" * 8193, "safe")
    with pytest.raises(KnowledgeHubError, match="scope_refs exceeds"):
        check_action(
            root,
            "push main",
            "git push origin main",
            scope_refs=tuple("scope:{}".format(i) for i in range(33)),
        )
    with pytest.raises(KnowledgeHubError, match="asserted_exceptions value exceeds"):
        check_action(
            root,
            "push main",
            "git push origin main",
            asserted_exceptions=("x" * 501,),
        )


def test_item_validation_rejects_unsafe_guard_regex():
    item = {
        "agent_contract": _contract(
            "constraint",
            "hard",
            capabilities=["enforceable", "guardable"],
            guard={"deny_regex": ["(a+)+$"]},
        )
    }
    errors = validate_item(item)
    assert "unsafe agent_contract deny_regex: nested quantified group" in errors


def test_item_validation_rejects_nested_groups_and_large_repeat_bounds():
    nested = {
        "agent_contract": _contract(
            "constraint",
            "hard",
            capabilities=["enforceable", "guardable"],
            guard={"deny_regex": ["((ab)+)+$"]},
        )
    }
    repeated = {
        "agent_contract": _contract(
            "constraint",
            "hard",
            capabilities=["enforceable", "guardable"],
            guard={"deny_regex": ["a{1001}"]},
        )
    }

    assert "unsafe agent_contract deny_regex: nested groups are not allowed" in validate_item(nested)
    assert "unsafe agent_contract deny_regex: repeat bound exceeds 1000" in validate_item(repeated)


def test_action_check_rejects_string_scope_sequence(tmp_path):
    root = _root(tmp_path)
    with pytest.raises(KnowledgeHubError, match="sequence of strings"):
        check_action(
            root,
            "push main",
            "git push origin main",
            scope_refs="repository:demo",
        )


def test_action_check_fails_closed_for_unsafe_guard_regex(tmp_path):
    root = _root(tmp_path)
    path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rows[0]["agent_contract"]["guard"]["deny_regex"] = ["(a+)+$"]
    rows[0]["agent_contract"]["guard"]["deny_any"] = []
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    result = check_action(
        root,
        "push main",
        "git push origin main",
        scope_refs=["repository:demo"],
    )
    assert result["verdict"] == "NEEDS_REVIEW"
    assert {row["reason"] for row in result["needs_review"]} == {"unsafe_guard_regex"}


def test_evidence_pack_excludes_expired_active_evidence(tmp_path):
    root = _root(tmp_path)
    path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    expired = next(row for row in rows if row["id"] == "repo-fact")
    expired["valid_to"] = "2026-09-20"
    expired["summary_zh"] = "expired beacon proof"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    pack = build_evidence_pack(root, "expired beacon proof", as_of="2026-09-25")

    selected = {
        row.get("id")
        for lane in ("must", "should", "context", "provisional")
        for row in pack[lane]
    }
    assert "repo-fact" not in selected
    assert any(
        row.get("id") == "repo-fact"
        and row.get("reason") == "non-serviceable-corpus-or-time"
        for row in pack["search_trace"]["lifecycle_excluded"]
    )


def test_evidence_pack_as_of_can_recover_then_valid_fact(tmp_path):
    root = _root(tmp_path)
    path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    fact = next(row for row in rows if row["id"] == "repo-fact")
    fact["valid_to"] = "2026-09-20"
    fact["summary_zh"] = "historical-valid beacon"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    pack = build_evidence_pack(root, "historical-valid beacon", as_of="2026-09-19")
    assert "repo-fact" in [row["id"] for row in pack["context"]]


def test_expired_active_constraint_is_not_completeness_promoted(tmp_path):
    root = _root(tmp_path)
    path = root / "registry/items.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    rule = next(row for row in rows if row["id"] == "no-force-push")
    rule["valid_to"] = "2026-09-20"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    pack = build_evidence_pack(
        root, "push main", scope_refs=["repository:demo"], as_of="2026-09-25"
    )
    assert "no-force-push" not in [row["id"] for row in pack["must"]]


def test_evidence_pack_rejects_invalid_as_of(tmp_path):
    with pytest.raises(KnowledgeHubError, match="YYYY-MM-DD"):
        build_evidence_pack(_root(tmp_path), "demo", as_of="not-a-date")
