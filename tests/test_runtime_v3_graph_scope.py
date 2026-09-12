from tools.codex_assets.knowledge_hub import runtime_v3 as rv3


def _item(item_id, domain, status="active", visibility="team-internal", **extra):
    row = {
        "id": item_id,
        "title": item_id,
        "kind": "standard",
        "domain": domain,
        "path": "{}/{}.md".format(domain, item_id),
        "status": status,
        "visibility": visibility,
        "updated_at": "2026-09-01",
    }
    row.update(extra)
    return row


def test_context_graph_cannot_expand_outside_agent_scope_or_validity(monkeypatch, tmp_path):
    seed = _item(
        "seed",
        "projects/demo",
        agent_contract={
            "relations": {
                "related_to": [
                    "project-peer",
                    "governance-peer",
                    "personal-peer",
                    "archived-peer",
                    "future-peer",
                ]
            }
        },
    )
    rows = [
        seed,
        _item("project-peer", "projects/demo/sub"),
        _item("governance-peer", "governance"),
        _item("personal-peer", "projects/demo", visibility="personal-local"),
        _item("archived-peer", "projects/demo", status="archived"),
        _item("future-peer", "projects/demo", valid_from="2027-01-01"),
    ]
    monkeypatch.setattr(rv3, "registry_items", lambda _root: rows)

    graph = rv3.context_graph(
        tmp_path,
        ["seed"],
        hops=1,
        knowledge_scopes=("projects",),
        as_of="2026-09-11",
    )

    assert graph["node_ids"] == ["project-peer", "seed"]
    assert graph["edges"] == [
        {
            "source_id": "seed",
            "relation": "related_to",
            "target_id": "project-peer",
        }
    ]
