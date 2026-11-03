import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
from .common import registry_items
from .maintenance_lineage import historical_target

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Materialize PCR02 owner-approved target documents inside Knowledge Hub.")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD")
args = parser.parse_args(argv)

today = args.as_of or dt.date.today().isoformat()
home = pathlib.Path.home()
source_root = home / "work" / "sigmastar" / "pcr02_ssc305" / "SourceCode" / "sdk" / "verify" / "gros" / "docs"
landing_manifest_path = root / "artifacts" / "manifests" / "pcr02-project-docs-owner-decision-landing-20260623.jsonl"

def load_landing_rows():
    rows = {}
    if not landing_manifest_path.exists():
        return rows
    for line in landing_manifest_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        worksheet_id = str(row.get("worksheet_id", ""))
        if worksheet_id:
            rows[worksheet_id] = row
    return rows

landing_rows = load_landing_rows()

targets = [
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-003",
        "item_id": "pcr02-asan-debug-guide-project-local-20260624",
        "source_path": "runbooks/asan-debug-guide.md",
        "target_path": "projects/gros/current/runbooks/asan-debug-guide.md",
        "title": "PCR02 ASAN 调试指导",
        "status": "project-local-current",
        "boundary": "仅作为 PCR02 project-local runbook；不得整篇提升为团队级 ASAN 标准，团队层方法论必须另行重写和复核。",
        "owner_decision": "split-approved",
    },
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-005",
        "source_path": "plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md",
        "target_path": "projects/gros/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md",
        "title": "DVR 录像回放 proto/sensor 解耦设计与实施计划",
        "status": "archive-only",
        "boundary": "仅归档原计划；缺少 completed 证据，不声明完成，不作为 current baseline。",
        "owner_decision": "archive-only",
    },
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-006",
        "source_path": "reports/2026-05-29-motor-mcu-debug-record.md",
        "target_path": "projects/gros/archive/reports/2026-05-29-motor-mcu-debug-record.md",
        "title": "电机 MCU 调试详细记录",
        "status": "archive-only",
        "boundary": "仅归档调试记录；事实、反馈、推断、建议和 open items 未拆分前不得进入 validation/current。",
        "owner_decision": "archive-only",
    },
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-007",
        "source_path": "reports/2026-06-16-dvr-record-replay-session-archive.md",
        "target_path": "projects/gros/archive/reports/2026-06-16-dvr-record-replay-session-archive.md",
        "title": "DVR 录像回放解耦会话归档",
        "status": "archive-only",
        "boundary": "仅归档 session archive；handoff、dirty-state 和 memory candidates 不进入 active facts，不写 memory。",
        "owner_decision": "archive-only",
    },
]


def read_target(item):
    """Navigate proved history for reads; never grant a new materialization."""
    original = item['target_path']
    item_id = item.get('item_id')
    matches = [row.get('path', '') for row in registry_items(root)
               if row.get('id') == item_id] if item_id else [original]
    if len(matches) != 1 or not matches[0]:
        return '', True
    canonical = matches[0]
    if canonical != original:
        history = historical_target(root, original)
        return (history if history == canonical else ''), True
    if (root / original).is_file():
        return original, False
    history = historical_target(root, original)
    if item_id and history and history != canonical:
        return '', True
    return (history, True) if history else (original, False)

results = []
blocked = []
for item in targets:
    source_file = source_root / item["source_path"]
    resolved_target, relocated = read_target(item)
    target_file = root / resolved_target if resolved_target else None
    source_exists = source_file.exists()
    landing_row = landing_rows.get(item["worksheet_id"], {})
    source_hash = str(landing_row.get("source_sha256", ""))
    source_size = landing_row.get("source_size", 0)
    source_text = ""
    can_materialize = bool(args.apply and source_exists and not relocated)

    if args.apply:
        if relocated:
            blocked.append({
                'worksheet_id': item['worksheet_id'], 'source_path': item['source_path'],
                'reason': 'registered target relocated or unresolved; re-materialization is forbidden',
            })
        elif not source_exists:
            blocked.append({
                "worksheet_id": item["worksheet_id"],
                "source_path": item["source_path"],
                "reason": "source file missing; retired origin is unavailable for re-materialization",
            })
        else:
            source_bytes = source_file.read_bytes()
            source_text = source_bytes.decode()
            source_hash = hashlib.sha256(source_bytes).hexdigest()
            source_size = len(source_bytes)

    if can_materialize:
        header = f"""---
title: {item['title']}
doc_type: owner-approved-target
status: {item['status']}
owner: leiwenjun
source_id: pcr02-project-docs
source_path: {item['source_path']}
source_sha256: {source_hash}
source_size: {len(source_bytes)}
owner_decision: {item['owner_decision']}
worksheet_id: {item['worksheet_id']}
review_after: 2026-09-17
generated_at: {today}
---

# {item['title']}

## Hub 边界

{item['boundary']}

## 来源

- Hub source path: `sources/pcr02-project-docs`
- Origin root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/gros/docs`（retired provenance only）
- Source path: `{item['source_path']}`
- Source SHA256: `{source_hash}`
- Owner decision: `{item['owner_decision']}`
- Worksheet: `{item['worksheet_id']}`

## 原始正文

"""
        content = header + source_text.rstrip() + "\n"
    exists_before = bool(target_file and target_file.exists())
    if can_materialize:
        target_file = root / item['target_path']
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content)
    results.append({
        "worksheet_id": item["worksheet_id"],
        "source_path": item["source_path"],
        "target_path": item["target_path"],
        "resolved_target_path": resolved_target,
        "target_resolution_source": 'maintenance-manifest' if relocated and resolved_target else 'owner-decision-landing-manifest',
        "exists_before": exists_before,
        "target_exists": bool(target_file and target_file.exists()),
        "written": can_materialize,
        "source_available": source_exists,
        "source_sha256": source_hash,
        "source_size": source_size,
        "source_identity_source": "runtime-source-file" if can_materialize else "owner-decision-landing-manifest",
    })

payload = {
    "status": "blocked" if blocked else ("applied" if args.apply else "planned"),
    "read_only": not args.apply,
    "target_count": len(targets),
    "written_count": sum(1 for row in results if row["written"]),
    "target_present_count": sum(1 for row in results if row["target_exists"]),
    "source_available_count": sum(1 for row in results if row["source_available"]),
    "blocked_count": len(blocked),
    "blocked": blocked,
    "landing_manifest": str(landing_manifest_path.relative_to(root)),
    "source_root": str(source_root).replace(str(home), "~", 1),
    "notes_zh": "默认只读模式只检查 Hub 内目标存在性，并从 owner decision landing manifest 读取 source identity；不会读取 retired origin 正文。--apply 需要 retired origin source 文件仍可用，否则返回 blocked。",
    "results": results,
}

if args.json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    print(f"status: {payload['status']}")
    for result in results:
        if result["written"]:
            action = "written"
        elif result["target_exists"]:
            action = "present"
        else:
            action = "missing"
        print(f"{result['target_path']}: {action}")
if blocked:
    sys.exit(1)
