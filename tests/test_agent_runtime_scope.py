from tools.codex_assets.knowledge_hub import agent_runtime as ar
from tools.codex_assets.knowledge_hub.search import SearchFilters


def test_constraint_completeness_respects_domain_boundary(tmp_path, monkeypatch):
    items = [
        {
            "id": "project-constraint",
            "title": "Project constraint",
            "kind": "standard",
            "domain": "projects/demo",
            "path": "projects/demo/current/constraint.md",
            "status": "active",
            "summary_zh": "项目约束",
            "evidence_refs": ["evidence:project"],
            "agent_contract": {"role": "constraint", "force": "mandatory"},
        },
        {
            "id": "governance-constraint",
            "title": "Governance constraint",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/constraint.md",
            "status": "active",
            "summary_zh": "治理约束",
            "evidence_refs": ["evidence:governance"],
            "agent_contract": {"role": "constraint", "force": "mandatory"},
        },
        {
            "id": "governance-retired",
            "title": "Retired governance constraint",
            "kind": "standard",
            "domain": "governance",
            "path": "governance/archive/constraint.md",
            "status": "archived",
            "summary_zh": "已归档治理约束",
            "evidence_refs": ["evidence:old"],
            "agent_contract": {
                "role": "constraint",
                "force": "mandatory",
                "guard": {"when_any": ["uart"]},
            },
        },
    ]

    monkeypatch.setattr(ar, "registry_items", lambda _root: items)
    monkeypatch.setattr(ar, "SearchIndex", lambda _root: object())
    monkeypatch.setattr(
        ar,
        "search",
        lambda *args, **kwargs: {
            "results": [],
            "search_trace": {},
            "index": {},
        },
    )

    pack = ar.build_evidence_pack(
        tmp_path,
        "uart",
        filters=SearchFilters(domains=("projects",)),
    )

    assert [row["id"] for row in pack["must"]] == ["project-constraint"]
    assert "governance-constraint" not in {
        row.get("id") for row in pack["must"] + pack["provisional"]
    }
    assert "governance-retired" not in {
        row.get("id") for row in pack["search_trace"]["lifecycle_excluded"]
    }
