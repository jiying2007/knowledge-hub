"""Manifest classification helpers for index-plan."""

def manifest_profile_health(manifest_path, first, date_value, summary_source, evidence_source, evidence_count):
    path_name = manifest_path.name
    in_current_profile = path_name.startswith("knowledge-hub-") and date_value >= "2026-06-21"
    if not in_current_profile:
        mode = str(first.get("mode", "") or "")
        classification = str(first.get("classification", "") or "")
        review_status = str(first.get("review_status", "") or "")
        if "reference" in mode or "reference" in classification or "reference" in review_status:
            return "reference-only"
        return "historical-evidence-exempt"
    if summary_source == "missing":
        return "missing-summary"
    if evidence_source == "missing" or evidence_count == 0:
        return "missing-evidence"
    if not isinstance(first.get("boundaries"), dict):
        return "advisory-missing-boundary"
    return "pass"

def classify_unpaired_manifest(root, stem, has_jsonl, has_md):
    reasons = []
    status = "needs_review"
    if "dry-run" in stem:
        status = "expected"
        reasons.append("dry-run 制品允许只保留执行明细或 Markdown 摘要之一")
    if "artifact-ref" in stem:
        status = "expected"
        reasons.append("artifact-ref 制品常以 JSONL 作为机器可读引用清单")
    if "source-inventory" in stem:
        status = "expected"
        reasons.append("source inventory 是历史盘点入口，允许 Markdown-only")
    if "classification" in stem:
        status = "expected"
        reasons.append("classification 是历史分类报告，允许 Markdown-only")
    if "copy-first-applied" in stem:
        status = "expected"
        reasons.append("早期 copy-first applied 记录允许 Markdown-only；后续新增治理 manifest 优先成对")
    if not reasons:
        reasons.append("未命中已知历史例外，建议人工确认是否缺少 Markdown 或 JSONL 配对文件")
    return {
        "stem": stem,
        "jsonl_path": str((root / "artifacts" / "manifests" / f"{stem}.jsonl").relative_to(root)) if has_jsonl else "",
        "markdown_path": str((root / "artifacts" / "manifests" / f"{stem}.md").relative_to(root)) if has_md else "",
        "pairing_status": "jsonl-only" if has_jsonl and not has_md else "markdown-only" if has_md and not has_jsonl else "unknown",
        "review_status": status,
        "reasons_zh": reasons,
        "notes_zh": "只读恢复分类；expected 不代表推荐新增同类单边文件，needs_review 不自动作为硬失败。",
    }

