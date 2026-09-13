"""Cross-index recovery audit for index-plan."""

def read_relative_text(root, warnings, relative_path):
    path = root / relative_path
    try:
        return path.read_text()
    except Exception as exc:
        warnings.append(f"cannot read {relative_path}: {exc}")
        return ""

def build_linking_audit(root, warnings, by_project, by_source, by_topic, decisions, by_decision, items, sources, topics, projects):
    project_ids = sorted(by_project)
    source_ids = sorted(by_source)
    topic_index_anchors = sorted(
        {
            str(row.get("domain", ""))
            for row in by_topic.values()
            if row.get("domain")
        }
    )
    decision_ids = sorted(
        str(row.get("decision_id", ""))
        for row in decisions
        if row.get("decision_id")
    )
    required_index_anchors = {
        "by_project": {
            "path": "indexes/by-project.md",
            "anchors": project_ids,
        },
        "by_source": {
            "path": "indexes/by-source.md",
            "anchors": source_ids,
        },
        "by_topic": {
            "path": "indexes/by-topic.md",
            "anchors": topic_index_anchors,
        },
        "by_decision": {
            "path": "indexes/by-decision.md",
            "anchors": decision_ids,
        },
    }

    expected_project_ids = {
        str(row.get("id", "")) for row in projects if row.get("id")
    }
    expected_source_ids = {
        str(row.get("id", "")) for row in sources if row.get("id")
    }
    expected_topic_ids = {
        str(row.get("id", "")) for row in topics if row.get("id")
    }
    expected_decision_ids = set(decision_ids)
    recovered_decision_ids = {
        str(row.get("decision_id", ""))
        for row in by_decision.get("registry_decisions", [])
        if row.get("decision_id")
    }
    cross_session_checks = {
        "project_registry_recoverable": expected_project_ids == set(by_project),
        "source_registry_recoverable": expected_source_ids == set(by_source),
        "topic_registry_recoverable": expected_topic_ids == set(by_topic),
        "decision_registry_recoverable": expected_decision_ids
        == recovered_decision_ids,
    }
    missing_cross_session = sorted(
        check_id for check_id, passed in cross_session_checks.items() if not passed
    )

    missing_source_provenance = []
    for source_id, source in sorted(by_source.items()):
        has_check_or_reason = bool(str(source.get("check", "")).strip() or str(source.get("no_check_reason", "")).strip())
        has_provenance = all(str(source.get(field, "")).strip() for field in ["path", "owner", "review_after", "source_strategy", "final_disposition"]) and has_check_or_reason
        if not has_provenance:
            missing_source_provenance.append(source_id)
    item_source_refs = sorted(
        {
            str((item.get("source") or {}).get("source_id", ""))
            for item in items
            if isinstance(item.get("source", {}), dict)
            and (item.get("source") or {}).get("source_id")
        }
    )
    unknown_item_source_ids = sorted(set(item_source_refs) - expected_source_ids)
    missing_cross_project = [
        "source-provenance:{}".format(source_id)
        for source_id in missing_source_provenance
    ] + [
        "unknown-item-source:{}".format(source_id)
        for source_id in unknown_item_source_ids
    ]

    markdown_missing = []
    markdown_index_recovery = {}
    for index_id, spec in required_index_anchors.items():
        text = read_relative_text(root, warnings, spec["path"])
        missing_anchors = [anchor for anchor in spec["anchors"] if anchor not in text]
        markdown_index_recovery[index_id] = {
            "status": "pass" if not missing_anchors else "fail",
            "path": spec["path"],
            "required_anchors": spec["anchors"],
            "missing_anchors": missing_anchors,
        }
        for anchor in missing_anchors:
            markdown_missing.append({"index": index_id, "path": spec["path"], "anchor": anchor})

    cross_session_status = "pass" if not missing_cross_session else "fail"
    cross_project_status = "pass" if not missing_cross_project else "fail"
    markdown_status = "pass" if not markdown_missing else "fail"
    status = "pass" if cross_session_status == "pass" and cross_project_status == "pass" and markdown_status == "pass" else "fail"
    return {
        "contract_version": 2,
        "status": status,
        "read_only": True,
        "source_body_read": False,
        "owner_gate_mutation": False,
        "commands": {
            "index_plan": "rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json",
            "status": "runtime:knowledge-status --strict payload",
            "search_contract": "runtime:knowledge-regression search result ids",
        },
        "cross_session": {
            "status": cross_session_status,
            **cross_session_checks,
            "missing": missing_cross_session,
        },
        "cross_project": {
            "status": cross_project_status,
            "registered_source_count": len(by_source),
            "item_source_ref_count": len(item_source_refs),
            "unknown_item_source_ids": unknown_item_source_ids,
            "source_provenance_complete": not missing_source_provenance,
            "missing_source_provenance_ids": missing_source_provenance,
            "missing": missing_cross_project,
        },
        "markdown_index_recovery": {
            "status": markdown_status,
            "indexes": markdown_index_recovery,
            "missing_anchors": markdown_missing,
        },
        "evidence_refs": [
            "runtime:status.sources.source_recovery_rows",
            "runtime:index_plan.indexes.by_project",
            "runtime:index_plan.indexes.by_source",
            "runtime:index_plan.indexes.by_topic",
            "runtime:index_plan.indexes.by_decision",
            "runtime:checks.knowledge_regression",
        ],
        "limitations_zh": "只证明当前 registry/index/search 恢复链路；不证明 owner decision 已签收，也不读取任何源项目正文。",
    }

