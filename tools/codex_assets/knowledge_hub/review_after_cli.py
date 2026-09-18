import argparse
import datetime as dt
import json
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]
script_repository_root = pathlib.Path(__file__).resolve().parents[3]
if str(script_repository_root) not in sys.path:
    sys.path.insert(0, str(script_repository_root))

from tools.codex_assets.knowledge_hub.common import KnowledgeHubError
from tools.codex_assets.knowledge_hub.review_risk import (
    classify_review_risk,
    load_review_risk_policy as load_shared_review_risk_policy,
)

parser = argparse.ArgumentParser(description="Print a report-only review_after stale and near-due report.")
output_mode = parser.add_mutually_exclusive_group()
output_mode.add_argument("--json", action="store_true")
output_mode.add_argument("--summary-json", action="store_true")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD", help="Use a fixed date for review_after checks.")
parser.add_argument("--window-days", type=int, default=30, help="Near-due window for registry items.")
parser.add_argument("--source-window-days", type=int, default=30, help="Near-due window for registered sources.")
parser.add_argument("--include-sources", action="store_true", help="Include near-due source detail rows.")
parser.add_argument("--include-owner-gates", action="store_true", help="Include open owner gate detail rows.")
args = parser.parse_args(argv)

if args.window_days < 0:
    parser.error("--window-days must be >= 0")
if args.source_window_days < 0:
    parser.error("--source-window-days must be >= 0")

def resolve_today():
    if args.as_of:
        raw_value = args.as_of
        source = "arg:--as-of"
    else:
        raw_value = os.environ.get("KNOWLEDGE_TODAY", "")
        source = "env:KNOWLEDGE_TODAY" if raw_value else "system-date"
    if raw_value:
        try:
            return dt.date.fromisoformat(raw_value), source
        except Exception:
            parser.error(f"invalid date for {source}: {raw_value}")
    return dt.date.today(), source

today, today_source = resolve_today()
item_window_end = today + dt.timedelta(days=args.window_days)
source_window_end = today + dt.timedelta(days=args.source_window_days)

errors = []

def load_review_risk_policy():
    try:
        return load_shared_review_risk_policy(root)
    except KnowledgeHubError as exc:
        errors.append(str(exc))
        return {
            "default_class": "ordinary",
            "classes": {
                "ordinary": {
                    "stale_severity": "warning",
                    "ai_first_action": "auto-triage",
                }
            },
            "rules": [],
        }

review_risk_policy = load_review_risk_policy()

def review_risk(path_value):
    return classify_review_risk(review_risk_policy, path_value)

def user_path_prefixes():
    prefixes = [str(pathlib.Path.home())]
    user_name = os.environ.get("USER", "")
    if user_name:
        prefixes.append("/" + "vsdata" + "/" + user_name)
    return [prefix for prefix in prefixes if prefix and prefix != "/"]

def display_path(value):
    text = str(value)
    for prefix in user_path_prefixes():
        if text == prefix:
            text = "~"
        elif text.startswith(prefix + "/"):
            text = "~" + text[len(prefix):]
        else:
            text = text.replace(prefix, "~")
    return text

def read_jsonl(path):
    rows = []
    try:
        for line_no, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.relative_to(root)}:{line_no}: {exc}")
    except Exception as exc:
        errors.append(f"cannot read {path.relative_to(root)}: {exc}")
    return rows

def parse_date(value, label):
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except Exception:
        errors.append(f"{label} invalid review_after: {value}")
        return None

items = read_jsonl(root / "registry" / "items.jsonl")

try:
    sources_payload = json.loads((root / "registry" / "sources.json").read_text())
    sources = sources_payload.get("sources", [])
    if not isinstance(sources, list):
        errors.append("registry/sources.json field sources is not a list")
        sources = []
except Exception as exc:
    errors.append(f"cannot read registry/sources.json: {exc}")
    sources = []

worksheet_paths = sorted((root / "artifacts" / "manifests").glob("*owner-decision-worksheets-*.jsonl"))
if not worksheet_paths:
    errors.append("missing artifacts/manifests/*owner-decision-worksheets-*.jsonl")
owner_gate_rows = []
for worksheet_path in worksheet_paths:
    for row in read_jsonl(worksheet_path):
        if isinstance(row, dict):
            row = dict(row)
            row["worksheet_file"] = str(worksheet_path.relative_to(root))
            owner_gate_rows.append(row)

stale_items = []
near_due_items = []
for item in items:
    item_id = str(item.get("id", ""))
    review_date = parse_date(item.get("review_after", ""), f"items:{item_id}")
    if not review_date:
        continue
    source = item.get("source", {}) if isinstance(item.get("source", {}), dict) else {}
    source_id = str(source.get("source_id", ""))
    days = (review_date - today).days
    risk = review_risk(item.get("path", ""))
    detail = {
        "row_type": "stale_item" if review_date < today else "near_due_item",
        "entity_type": "item",
        "item_id": item_id,
        "owner": item.get("owner", ""),
        "status": item.get("status", ""),
        "domain": item.get("domain", ""),
        "source_id": source_id,
        "source_status": "present" if source_id else "missing",
        "path": item.get("path", ""),
        "review_after": review_date.isoformat(),
        "days_until_review": days,
        **risk,
        "selection_reason": "review_after < as_of" if review_date < today else f"review_after <= {item_window_end.isoformat()}",
        "suggested_action_zh": (
            "AI 自动生成复核 packet 和差异摘要；仅在需要 owner/语义决定时升级人工。"
            if risk["ai_first_action"] != "human-review-required"
            else "关键治理条目：AI 先生成复核 packet，最终语义签收保留人工。"
        ),
    }
    if review_date < today:
        stale_items.append(detail)
    elif review_date <= item_window_end:
        near_due_items.append(detail)

stale_sources = []
near_due_sources = []
for source in sources:
    source_id = str(source.get("id", ""))
    review_date = parse_date(source.get("review_after", ""), f"sources:{source_id}")
    if not review_date:
        continue
    days = (review_date - today).days
    detail = {
        "row_type": "stale_source" if review_date < today else "near_due_source",
        "entity_type": "source",
        "source_id": source_id,
        "owner": source.get("owner", ""),
        "status": source.get("status", ""),
        "path": source.get("path", ""),
        "review_after": review_date.isoformat(),
        "days_until_review": days,
        "final_disposition": source.get("final_disposition", ""),
        "selection_reason": "review_after < as_of" if review_date < today else f"review_after <= {source_window_end.isoformat()}",
        "suggested_action_zh": "AI 自动复核 source 覆盖、check/no-check、引用可达性和 final_disposition；仅 authority/retirement 语义冲突升级 owner。",
    }
    if review_date < today:
        stale_sources.append(detail)
    elif review_date <= source_window_end:
        near_due_sources.append(detail)

open_owner_gates = []
for row in owner_gate_rows:
    status = str(row.get("status", ""))
    worksheet_status = str(row.get("worksheet_status", ""))
    if status in {"resolved", "owner-approved", "closed"} or worksheet_status not in {"owner-fill-required", "open", "blocked-pending-owner-review"}:
        continue
    review_date = parse_date(row.get("review_after", ""), f"owner-gate:{row.get('id', row.get('worksheet_id', 'unknown'))}")
    open_owner_gates.append(
        {
            "row_type": "open_owner_gate",
            "entity_type": "owner_gate",
            "worksheet_id": row.get("worksheet_id", row.get("id", "")),
            "worksheet_file": row.get("worksheet_file", ""),
            "source_id": row.get("source_id", ""),
            "source_path": row.get("source_path", ""),
            "owner": row.get("owner_required", row.get("owner", "")),
            "status": status,
            "worksheet_status": worksheet_status,
            "review_after": review_date.isoformat() if review_date else "",
            "days_until_review": (review_date - today).days if review_date else None,
            "suggested_action_zh": "仅提示真实 owner 人工签收；不得由 AI 代签、关闭 gate 或提升 active。",
        }
    )

detail_rows = sorted(stale_items + near_due_items, key=lambda row: (row["review_after"], row["item_id"]))
if args.include_sources:
    detail_rows.extend(sorted(stale_sources + near_due_sources, key=lambda row: (row["review_after"], row["source_id"])))
if args.include_owner_gates:
    detail_rows.extend(sorted(open_owner_gates, key=lambda row: (row.get("review_after", ""), row.get("worksheet_id", ""))))

item_review_rows = sorted(stale_items + near_due_items, key=lambda row: (row["review_after"], row["item_id"]))

def group_item_rows(rows, field, missing_value=""):
    grouped = {}
    for row in rows:
        raw_key = str(row.get(field, ""))
        key = raw_key if raw_key else missing_value
        if not key:
            key = "<missing>"
        entry = grouped.setdefault(
            key,
            {
                "count": 0,
                "item_ids": [],
                "first_review_after": "",
                "latest_review_after": "",
                "suggested_action_zh": "",
            },
        )
        entry["count"] += 1
        entry["item_ids"].append(row.get("item_id", ""))
        review_after = str(row.get("review_after", ""))
        if not entry["first_review_after"] or review_after < entry["first_review_after"]:
            entry["first_review_after"] = review_after
        if not entry["latest_review_after"] or review_after > entry["latest_review_after"]:
            entry["latest_review_after"] = review_after
    for key, entry in grouped.items():
        if field == "owner":
            entry["suggested_action_zh"] = "AI 先生成 owner 聚合复核 packet；只有 current validity 的语义签收才分派给 owner。"
        elif field == "source_id":
            if key == "<missing-source-id>":
                entry["suggested_action_zh"] = "AI 先自动发现可证明的 source_id 候选并生成 proposal；无唯一候选时再进入治理复核。"
            else:
                entry["suggested_action_zh"] = "按 source_id 由 AI 自动复核迁移来源、validation_refs 和 source coverage；不改变 owner 语义决定。"
        elif field == "status":
            if key == "archived":
                entry["suggested_action_zh"] = "复核 archive-only 边界和证据，不把历史材料提升为 active fact。"
            else:
                entry["suggested_action_zh"] = "复核 reviewing 条目的 owner、适用范围、证据和下一次 review_after。"
        elif field == "domain":
            entry["suggested_action_zh"] = "按 domain 自动聚合维护候选；项目域不得自动提升到团队标准。"
        elif field == "review_class":
            entry["suggested_action_zh"] = "按风险等级自动 triage；关键治理只把最终语义签收升级给人。"
        entry["item_ids"] = sorted(entry["item_ids"])
    return dict(sorted(grouped.items(), key=lambda kv: (-kv[1]["count"], kv[0])))

groups = {
    "grouping_contract_version": 1,
    "by_owner": group_item_rows(item_review_rows, "owner", "<missing-owner>"),
    "by_status": group_item_rows(item_review_rows, "status", "<missing-status>"),
    "by_domain": group_item_rows(item_review_rows, "domain", "<missing-domain>"),
    "by_source_id": group_item_rows(item_review_rows, "source_id", "<missing-source-id>"),
    "by_review_class": group_item_rows(item_review_rows, "review_class", "ordinary"),
    "notes_zh": "默认由 AI 自动 triage/生成复核 packet；只有 owner/语义签收和 security-critical 最终决定保留人工。",
}

status = "fail" if errors else "report-only"
output = {
    "schema_version": 1,
    "status": status,
    "root": display_path(root),
    "read_only": True,
    "report_only": True,
    "today": today.isoformat(),
    "as_of_source": today_source,
    "item_window_days": args.window_days,
    "item_window_end": item_window_end.isoformat(),
    "source_window_days": args.source_window_days,
    "source_window_end": source_window_end.isoformat(),
    "include_sources": args.include_sources,
    "include_owner_gates": args.include_owner_gates,
    "counts": {
        "items_total": len(items),
        "stale_items": len(stale_items),
        "near_due_items": len(near_due_items),
        "sources_total": len(sources),
        "stale_sources": len(stale_sources),
        "near_due_sources": len(near_due_sources),
        "owner_gate_open_count": len(open_owner_gates),
        "detail_row_count": len(detail_rows),
        "missing_source_id_count": sum(1 for row in item_review_rows if not row.get("source_id")),
    },
    "groups": groups,
    "rows": detail_rows,
    "errors": errors,
    "limitations_zh": "review_after 默认由 AI 自动 triage 和生成复核 packet；不自动修改日期、不关闭 owner gate、不生成 owner decision、不改变 final gate 语义。",
    "must_not": [
        "不得自动修改 review_after",
        "不得把 ordinary near-due warning 当作 blocking error",
        "不得关闭 owner gate",
        "不得生成 owner decision",
        "不得写 memory",
    ],
}

if args.json or args.summary_json:
    projection = output
    if args.summary_json:
        projection = {
            "schema_version": 1,
            "projection": "knowledge-review-after-summary-v1",
            "status": output["status"],
            "read_only": True,
            "report_only": True,
            "today": output["today"],
            "counts": output["counts"],
            "groups": {
                key: {
                    name: {
                        "count": group.get("count", 0),
                        "first_review_after": group.get(
                            "first_review_after", ""
                        ),
                        "latest_review_after": group.get(
                            "latest_review_after", ""
                        ),
                    }
                    for name, group in value.items()
                }
                for key, value in output["groups"].items()
                if key.startswith("by_") and isinstance(value, dict)
            },
            "error_count": len(errors),
        }
    print(json.dumps(projection, ensure_ascii=False, indent=2))
else:
    print("# Knowledge review_after Report")
    print()
    print(f"- status: {status}")
    print(f"- as_of: {today.isoformat()}")
    print(f"- item window: {args.window_days} days, until {item_window_end.isoformat()}")
    print(f"- stale items: {len(stale_items)}")
    print(f"- near-due items: {len(near_due_items)}")
    print(f"- stale sources: {len(stale_sources)}")
    print(f"- near-due sources: {len(near_due_sources)}")
    print(f"- open owner gates: {len(open_owner_gates)}")
    print(f"- missing source_id items: {output['counts']['missing_source_id_count']}")
    print()
    print("## AI-first 复核分组")
    for title, key in [
        ("按 owner", "by_owner"),
        ("按 source_id", "by_source_id"),
        ("按 status", "by_status"),
        ("按 domain", "by_domain"),
        ("按风险", "by_review_class"),
    ]:
        print()
        print(f"### {title}")
        for name, group in groups[key].items():
            print(
                f"- {name}: count={group.get('count', 0)} "
                f"first={group.get('first_review_after', '')} latest={group.get('latest_review_after', '')}"
            )
            print(f"  - action: {group.get('suggested_action_zh', '')}")
    print()
    print("## 明细")
    for row in detail_rows:
        row_id = row.get("item_id") or row.get("source_id") or row.get("worksheet_id")
        print(f"- {row.get('row_type')}: {row_id} review_after={row.get('review_after')}")
    if errors:
        print()
        for error in errors:
            print(f"ERROR {error}")

sys.exit(1 if errors else 0)
