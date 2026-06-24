#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Materialize PCR02 owner-approved target documents inside Knowledge Hub.")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--json", action="store_true")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD")
args = parser.parse_args(argv)

today = args.as_of or dt.date.today().isoformat()
home = pathlib.Path.home()
source_root = home / "work" / "sigmastar" / "pcr02_ssc305" / "SourceCode" / "sdk" / "verify" / "xcrz_sigmastar_demo" / "docs"

targets = [
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-003",
        "source_path": "runbooks/asan-debug-guide.md",
        "target_path": "projects/pcr02/current/runbooks/asan-debug-guide.md",
        "title": "PCR02 ASAN 调试指导",
        "status": "project-local-current",
        "boundary": "仅作为 PCR02 project-local runbook；不得整篇提升为团队级 ASAN 标准，团队层方法论必须另行重写和复核。",
        "owner_decision": "split-approved",
    },
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-005",
        "source_path": "plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md",
        "target_path": "projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md",
        "title": "DVR 录像回放 proto/sensor 解耦设计与实施计划",
        "status": "archive-only",
        "boundary": "仅归档原计划；缺少 completed 证据，不声明完成，不作为 current baseline。",
        "owner_decision": "archive-only",
    },
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-006",
        "source_path": "reports/2026-05-29-motor-mcu-debug-record.md",
        "target_path": "projects/pcr02/archive/reports/2026-05-29-motor-mcu-debug-record.md",
        "title": "电机 MCU 调试详细记录",
        "status": "archive-only",
        "boundary": "仅归档调试记录；事实、反馈、推断、建议和 open items 未拆分前不得进入 validation/current。",
        "owner_decision": "archive-only",
    },
    {
        "worksheet_id": "pcr02-owner-decision-worksheet-007",
        "source_path": "reports/2026-06-16-dvr-record-replay-session-archive.md",
        "target_path": "projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md",
        "title": "DVR 录像回放解耦会话归档",
        "status": "archive-only",
        "boundary": "仅归档 session archive；handoff、dirty-state 和 memory candidates 不进入 active facts，不写 memory。",
        "owner_decision": "archive-only",
    },
]

results = []
for item in targets:
    source_file = source_root / item["source_path"]
    target_file = root / item["target_path"]
    source_text = source_file.read_text()
    source_bytes = source_file.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
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

- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Source path: `{item['source_path']}`
- Source SHA256: `{source_hash}`
- Owner decision: `{item['owner_decision']}`
- Worksheet: `{item['worksheet_id']}`

## 原始正文

"""
    content = header + source_text.rstrip() + "\n"
    exists_before = target_file.exists()
    if args.apply:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(content)
    results.append({
        "worksheet_id": item["worksheet_id"],
        "source_path": item["source_path"],
        "target_path": item["target_path"],
        "exists_before": exists_before,
        "written": bool(args.apply),
        "source_sha256": source_hash,
        "source_size": len(source_bytes),
    })

payload = {
    "status": "applied" if args.apply else "planned",
    "read_only": not args.apply,
    "target_count": len(targets),
    "written_count": len(targets) if args.apply else 0,
    "results": results,
}

if args.json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    print(f"status: {payload['status']}")
    for result in results:
        print(f"{result['target_path']}: {'written' if args.apply else 'planned'}")
PY
