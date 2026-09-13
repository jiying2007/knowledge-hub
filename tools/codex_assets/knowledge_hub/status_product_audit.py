import collections
import pathlib
import re
from typing import Any, Dict, List, Sequence

from .status_common import display_path, load_jsonl

PRODUCT_COPY_TARGET_PREFIXES = ("projects/", "domains/", "notes/")
PRODUCT_COPY_ALLOWED_OBJECT_TYPES = {"markdown"}
PRODUCT_NONCANONICAL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bmigrated-", r"copy-?first", r"copyfirst", r"migration-baseline",
        r"migration-applied", r"migration-dry-run", r"source-docs",
    ]
]
PRODUCT_PROCESS_MANIFEST_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [r"copy-?first", r"source-inventory-\d{8}", r"project-docs-classification-\d{8}"]
]
PRODUCT_ALLOWED_PROCESS_MANIFEST_NAMES = {"knowledge-hub-governance-regression-helper-20260619.md"}
PRODUCT_REVIEWING_TARGET_RATIO = 0.10


def _inventory_row_blockers(root: pathlib.Path, row: Dict[str, Any]) -> List[str]:
    object_type = str(row.get("object_type", ""))
    disposition = str(row.get("hub_disposition", ""))
    row_status = str(row.get("status", ""))
    target_path = str(row.get("target_path", "")).strip()
    blockers: List[str] = []
    if row_status == "pending":
        blockers.append("pending-row")
    if disposition == "copy-body":
        if object_type not in PRODUCT_COPY_ALLOWED_OBJECT_TYPES:
            blockers.append("copy-body-non-markdown")
        if not target_path:
            blockers.append("copy-body-missing-target")
        elif not target_path.startswith(PRODUCT_COPY_TARGET_PREFIXES):
            blockers.append("copy-body-noncanonical-target")
        elif not (root / target_path).exists():
            blockers.append("copy-body-target-missing")
    return blockers


def _inventory_source_rows(
    root: pathlib.Path,
    errors: List[str],
    source: Dict[str, Any],
    rows: List[Dict[str, Any]],
    blockers: List[Dict[str, Any]],
) -> None:
    source_id = str(source.get("id", ""))
    if not source_id:
        return
    inventory_path = root / "sources" / source_id / "inventory.jsonl"
    if not inventory_path.exists():
        blockers.append({"source_id": source_id, "row_id": "", "reason": "missing-inventory", "summary_zh": "source 缺少 inventory.jsonl，不能证明正文最大迁移处置已覆盖。"})
        return
    inventory_rows = load_jsonl(root, errors, inventory_path)
    if not inventory_rows:
        blockers.append({"source_id": source_id, "row_id": "", "reason": "empty-inventory", "summary_zh": "source inventory 为空，不能证明正文最大迁移处置已覆盖。"})
    for line_no, row in enumerate(inventory_rows, 1):
        row_id = str(row.get("id", "{}:{}".format(source_id, line_no)))
        row_blockers = _inventory_row_blockers(root, row)
        record = {"source_id": source_id, "row_id": row_id, "line": line_no, "object_type": str(row.get("object_type", "")), "hub_disposition": str(row.get("hub_disposition", "")), "target_path": str(row.get("target_path", "")).strip(), "status": str(row.get("status", "")), "blockers": row_blockers}
        rows.append(record)
        if row_blockers:
            blockers.append(dict(record, reason=",".join(row_blockers), summary_zh="product 要求正文复制仅限可维护 Markdown，并落到 projects/domains/notes；其他对象必须 summary/reference/artifact/archive/exclude。"))


def build_product_source_inventory_audit(
    root: pathlib.Path,
    errors: List[str],
    sources: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    blockers: List[Dict[str, Any]] = []
    for source in sorted(sources, key=lambda row: str(row.get("id", ""))):
        _inventory_source_rows(root, errors, source, rows, blockers)
    by_reason: Dict[str, int] = collections.Counter()
    for blocker in blockers:
        for reason in str(blocker.get("reason", "")).split(","):
            if reason:
                by_reason[reason] += 1
    return {
        "status": "pass" if not blockers else "needs-fix", "profile": "product",
        "row_count": len(rows), "blocker_count": len(blockers), "by_reason": dict(sorted(by_reason.items())),
        "blockers": blockers,
        "rules": {"copy_body_allowed_object_types": sorted(PRODUCT_COPY_ALLOWED_OBJECT_TYPES), "copy_body_target_prefixes": list(PRODUCT_COPY_TARGET_PREFIXES), "pending_rows_block_final_gate": True},
        "notes_zh": "product 终态要求可复制正文落到 canonical 正文层；raw/session/history/log/binary/source-code/tool/config/artifact 不得全文 copy-body。",
    }


def _noncanonical_text_matches(*values: Any) -> bool:
    parts: List[str] = []
    for value in values:
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    haystack = " ".join(parts)
    return any(pattern.search(haystack) for pattern in PRODUCT_NONCANONICAL_PATTERNS)


def _sealed_historical_item(item: Dict[str, Any]) -> bool:
    status_value = str(item.get("status", ""))
    path_value = str(item.get("path", ""))
    review_status = str(item.get("review_status", ""))
    tags = item.get("tags", []) if isinstance(item.get("tags", []), list) else []
    if status_value != "archived":
        return False
    if "/current/" in path_value or (path_value.startswith("projects/") and "/archive/" not in path_value and not path_value.startswith("artifacts/manifests/")):
        return False
    if "owner-ready-no-decision" in review_status or "delete-blocked" in review_status or review_status.endswith("-open"):
        return False
    sealed_tags = {"archive-only", "deleted-tombstoned", "historical-session", "historical-release", "historical-policy", "historical-analysis", "historical-code-analysis", "historical-memory-curation", "no-active-promotion", "tombstone", "delete-execution", "coverage-audit"}
    return bool({str(tag) for tag in tags} & sealed_tags) or path_value.startswith("artifacts/manifests/")


def _scan_items(items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    noncanonical: List[Dict[str, Any]] = []
    sealed: List[Dict[str, Any]] = []
    reviewing: List[Dict[str, Any]] = []
    archived: List[str] = []
    for item in items:
        item_id = str(item.get("id", ""))
        status_value = str(item.get("status", ""))
        hit = _noncanonical_text_matches(item_id, item.get("path", ""), item.get("tags", []), item.get("review_status", ""), item.get("summary_zh", ""))
        if hit:
            ref = {"id": item_id, "status": status_value, "kind": item.get("kind", ""), "domain": item.get("domain", ""), "path": item.get("path", ""), "review_status": item.get("review_status", ""), "tags": item.get("tags", [])}
            if _sealed_historical_item(item):
                sealed.append(ref)
            else:
                noncanonical.append(ref)
                if status_value == "archived":
                    archived.append(item_id)
        if status_value == "reviewing":
            reviewing.append({"id": item_id, "domain": item.get("domain", ""), "path": item.get("path", ""), "review_after": item.get("review_after", ""), "review_status": item.get("review_status", "")})
    return {"noncanonical": noncanonical, "sealed": sealed, "reviewing": reviewing, "archived": archived}


def _process_residue(root: pathlib.Path, current_sources: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    manifests: List[str] = []
    manifests_root = root / "artifacts" / "manifests"
    if manifests_root.exists():
        for path in sorted(manifests_root.iterdir()):
            if path.is_file() and path.name not in PRODUCT_ALLOWED_PROCESS_MANIFEST_NAMES and any(pattern.search(path.name) for pattern in PRODUCT_PROCESS_MANIFEST_PATTERNS):
                manifests.append(display_path(path))
    copy_first = [display_path(path) for path in sorted((root / "tools").glob("knowledge-copy-first*.sh")) if path.exists()]
    closed = [{"id": str(source.get("id", "")), "status": source.get("status", ""), "final_disposition": source.get("final_disposition", ""), "canonical_target": source.get("canonical_target", "")} for source in current_sources if str(source.get("status", "")) == "retired"]
    return {"manifests": manifests, "copy_first": copy_first, "closed": closed}


def _residue_blockers(scan: Dict[str, Any], residue: Dict[str, Any]) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    specs = [
        ("noncanonical", "product-noncanonical-items", "product 运行模型不允许带有 copy-first、migrated、source-docs 等封存流程标记的条目留在当前 registry。"),
        ("manifests", "product-process-manifests", "product 运行模型不把 copy-first、classification 或 source-inventory 过程 manifest 保留为当前树资产。"),
        ("copy_first", "product-copy-first-tools", "product 运行模型不暴露 copy-first 工具入口；外部资料吸收统一走 source/intake/review/promote。"),
        ("closed", "product-closed-sources-in-current-registry", "product 运行模型不把已关闭来源保留在 registry/sources.json 当前 source 主列表。"),
    ]
    combined = dict(residue, noncanonical=scan["noncanonical"])
    for key, blocker_id, summary in specs:
        rows = combined[key]
        if rows:
            blockers.append({"id": blocker_id, "count": len(rows), "summary_zh": summary, "sample": rows[:20]})
    return blockers


def build_product_noncanonical_residue_audit(
    root: pathlib.Path,
    items: Sequence[Dict[str, Any]],
    current_sources: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    scan = _scan_items(items)
    residue = _process_residue(root, current_sources)
    blockers = _residue_blockers(scan, residue)
    reviewing_count = len(scan["reviewing"])
    item_count = len(items)
    reviewing_ratio = round(reviewing_count / item_count, 4) if item_count else 0
    return {
        "status": "pass" if not blockers else "needs-fix", "profile": "product", "item_count": item_count,
        "noncanonical_item_count": len(scan["noncanonical"]), "archived_noncanonical_item_count": len(scan["archived"]),
        "sealed_historical_item_count": len(scan["sealed"]), "sealed_historical_item_sample": scan["sealed"][:20],
        "process_manifest_count": len(residue["manifests"]), "copy_first_tool_count": len(residue["copy_first"]), "closed_source_count": len(residue["closed"]),
        "reviewing_count": reviewing_count, "reviewing_ratio": reviewing_ratio, "reviewing_target_ratio": PRODUCT_REVIEWING_TARGET_RATIO,
        "blocker_count": len(blockers), "blockers": blockers,
        "notes_zh": "product 运行模型只允许 canonical 资产进入当前入口；reviewing 比例只作采用度观测，不作为技术失败。已封存且不可误用的历史证据只作 provenance。",
    }
