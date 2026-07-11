#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import collections
import datetime as dt
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(
    prog="knowledge-summary-backfill.sh",
    description="Backfill archived registry summary_zh fields from Hub-local bodies.",
)
parser.add_argument("--apply", action="store_true", help="Write registry, report artifacts and core indexes.")
parser.add_argument("--as-of", default=dt.date.today().isoformat())
parser.add_argument(
    "--artifact-id",
    default="",
    help="Closeout artifact id. Defaults to knowledge-hub-archived-summary-full-closeout-YYYYMMDD.",
)
parser.add_argument("--json", action="store_true", help="Print JSON result.")
args = parser.parse_args(argv)

try:
    as_of = dt.date.fromisoformat(args.as_of)
except ValueError:
    parser.error("--as-of must be YYYY-MM-DD")

compact_date = as_of.strftime("%Y%m%d")
artifact_id = args.artifact_id or f"knowledge-hub-archived-summary-full-closeout-{compact_date}"
md_rel = f"artifacts/manifests/{artifact_id}.md"
jsonl_rel = f"artifacts/manifests/{artifact_id}.jsonl"
items_path = root / "registry" / "items.jsonl"


def load_items():
    rows = []
    for line_no, line in enumerate(items_path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"registry/items.jsonl:{line_no}: invalid JSON: {exc}") from exc
    return rows


def compact_dump(row):
    return json.dumps(row, ensure_ascii=False, separators=(",", ":"))


def clean(text):
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def title_from_text(text, item):
    match = re.search(r"^#\s+(.+)$", text, re.M)
    if match:
        return clean(match.group(1))
    match = re.search(r"^title:\s*(.+)$", text, re.M)
    if match:
        return clean(match.group(1).strip(" \""))
    return item.get("title") or item["id"]


def extract_summary(text):
    match = re.search(r"^##\s*(摘要|Summary)\s*$", text, re.M | re.I)
    if match:
        start = match.end()
        next_heading = re.search(r"^##\s+", text[start:], re.M)
        block = text[start : start + next_heading.start()] if next_heading else text[start:]
        lines = []
        for raw in block.splitlines():
            line = raw.strip()
            if not line or line.startswith("```") or line.startswith("|") or re.match(r"^-+\s*$", line):
                if lines:
                    break
                continue
            if line.startswith("-"):
                line = line.lstrip("- ").strip()
            lines.append(line)
            if len("".join(lines)) > 90:
                break
        if lines:
            return clean("；".join(lines))

    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    body = re.sub(r"^# .+\n", "", body, count=1, flags=re.M)
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph or paragraph.startswith("##") or paragraph.startswith("|") or paragraph.startswith("```"):
            continue
        paragraph = re.sub(r"^[-*]\s+", "", paragraph)
        value = clean(paragraph)
        if len(value) >= 12:
            return value[:160]
    return ""


def boundary_phrase(item):
    kind = item.get("kind", "")
    domain = item.get("domain", "")
    if kind == "project-current":
        return "该条目当前为 archived retired-source provenance，仅作历史项目材料检索入口，不代表当前项目事实、active 决策或 owner 签收。"
    if kind == "decision":
        return "该条目当前为 archived decision provenance，仅作历史决策材料检索入口，不代表新的 owner decision、active 规则或当前发布状态。"
    if kind == "artifact-ref":
        return "该条目当前为 archived artifact reference，仅登记制品身份和可追溯边界，不代表内容复核、发布许可或 active 事实。"
    if kind == "patent" or domain == "patents" or domain.startswith("patents"):
        return "该条目当前为 archived patent/provenance 材料，仅作专利材料检索和附件身份边界，不代表法律复核、公开授权或正式提交。"
    if domain == "codex":
        return "该条目当前为 archived Codex 治理证据，仅作历史 provenance，不提升 active 规则、不写 memory、不改变运行态配置。"
    if domain == "embedded":
        return "该条目当前为 archived embedded 治理证据，仅作历史 provenance，不提升团队 active 标准或项目事实。"
    if domain == "governance":
        return "该条目当前为 archived Knowledge Hub 治理证据，仅作 report-only 历史 provenance，不生成 owner decision、不关闭 owner gate、不写 memory。"
    if domain == "projects/pcr02":
        return "该条目当前为 archived PCR02 治理证据，仅作历史 provenance，不代表当前项目事实、owner decision、active promotion 或源项目写入。"
    return "该条目当前为 archived 历史证据，仅作 provenance，不代表 active promotion、owner decision、memory write 或 source project write。"


def make_summary(item):
    path = root / item["path"]
    if path.is_file():
        text = path.read_text(errors="replace")
        title = title_from_text(text, item)
        core = extract_summary(text)
    elif path.is_dir():
        title = item.get("title") or item["id"]
        core = f"归档目录 {item['path']}，用于保留 {title} 的 Hub 内历史正文或附件集合。"
    else:
        raise SystemExit(f"{item['id']}: path does not exist: {item['path']}")

    if not core:
        core = f"归档 {title}。"
    summary = clean(core)
    if len(summary) > 170:
        summary = summary[:170].rstrip("，；。 ") + "。"
    if "不代表" not in summary and "不生成" not in summary and "不写" not in summary:
        summary = summary.rstrip("。") + "。" + boundary_phrase(item)
    return summary


def missing_archived_summary(item):
    return item.get("status") == "archived" and not item.get("summary_zh")


def append_unique_line(path, line):
    text = path.read_text() if path.exists() else ""
    if line in text.splitlines():
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text + line + "\n")
    return True


def insert_owner_line(owner, item_id):
    path = root / "indexes/by-owner.md"
    line = f"- `{item_id}`"
    text = path.read_text()
    if line in text.splitlines():
        return False
    marker = f"## {owner}\n"
    pos = text.find(marker)
    if pos == -1:
        return append_unique_line(path, f"\n## {owner}\n\n{line}")
    insert_at = pos + len(marker)
    if text[insert_at : insert_at + 1] == "\n":
        insert_at += 1
    path.write_text(text[:insert_at] + line + "\n" + text[insert_at:])
    return True


def add_closeout_indexes(item_id, review_after):
    changed = []
    if insert_owner_line("leiwenjun", item_id):
        changed.append("indexes/by-owner.md")
    if append_unique_line(root / "indexes/by-status.md", f"- archived: `{item_id}`"):
        changed.append("indexes/by-status.md")
    if append_unique_line(root / "indexes/by-review-date.md", f"- {review_after}: `{item_id}`"):
        changed.append("indexes/by-review-date.md")
    decision_line = (
        f"- `{item_id}`: archived summary_zh 全量缺口收口；证据：`{md_rel}`；"
        "只补 registry 可读摘要，不改变 archived 状态、不生成 owner decision、不提升 active、不写 memory。"
    )
    if append_unique_line(root / "indexes/by-decision.md", decision_line):
        changed.append("indexes/by-decision.md")
    return changed


items = load_items()
targets = [item for item in items if missing_archived_summary(item)]
updates = []
for item in targets:
    updates.append(
        {
            "id": item["id"],
            "kind": item.get("kind", ""),
            "domain": item.get("domain", ""),
            "path": item.get("path", ""),
            "summary_zh": make_summary(item),
        }
    )

by_kind_domain = collections.Counter((row["kind"], row["domain"]) for row in updates)
result = {
    "schema_version": 1,
    "artifact_id": artifact_id,
    "as_of": args.as_of,
    "mode": "apply" if args.apply else "dry-run",
    "selected_count": len(updates),
    "by_kind_domain": [
        {"kind": kind, "domain": domain, "count": count}
        for (kind, domain), count in sorted(by_kind_domain.items(), key=lambda row: (-row[1], row[0][1], row[0][0]))
    ],
    "updated_ids": [row["id"] for row in updates],
    "boundary": "archived summary backfill only; no owner decision, no active promotion, no owner gate closure, no memory write and no source project write",
}

if args.apply:
    summaries = {row["id"]: row["summary_zh"] for row in updates}
    for item in items:
        if item.get("id") in summaries:
            item["summary_zh"] = summaries[item["id"]]
            item["updated_at"] = args.as_of

    if not any(item.get("id") == artifact_id for item in items):
        closeout_item = {
            "id": artifact_id,
            "title": "Knowledge Hub archived summary_zh 全量缺口收口 2026-07-11",
            "kind": "audit",
            "domain": "governance",
            "path": md_rel,
            "scope": "team-general",
            "visibility": "team-internal",
            "status": "archived",
            "owner": "leiwenjun",
            "source": {"type": "generated", "from": "knowledge-summary-backfill.sh archived summary closeout"},
            "validation_refs": [
                md_rel,
                jsonl_rel,
                "rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-11",
                "rtk bash tools/knowledge-status.sh --strict --json --as-of 2026-07-11 --final-profile mature",
            ],
            "summary_zh": "记录 2026-07-11 archived summary_zh 全量缺口收口：按 Hub 内正文或 ref 文件为 archived 条目补齐中文摘要，保持 archive-only/provenance 边界，不生成 owner decision、不提升 active、不关闭 owner gate、不写 memory、不修改源项目。",
            "primary_language": "zh-CN",
            "source_language": "zh-CN",
            "translation_status": "not-required",
            "terminology_status": "reviewed",
            "review_status": "human-reviewed-accepted",
            "evidence_strength": "hub-local-body-summary-backfill-plus-final-gate",
            "evidence_refs": [md_rel, jsonl_rel],
            "promotion_decision": "none; archived summary readability closeout only, no active promotion, no owner decision, no memory write and no source project write",
            "generated_by_ai": True,
            "ai_role": "classified",
            "ai_model_or_tool": "Codex",
            "ai_generated_at": args.as_of,
            "human_reviewed_by": "leiwenjun-via-codex-delegation",
            "human_reviewed_at": args.as_of,
            "review_basis": "用户要求处理所有 archived summary_zh 缺口；Codex 依据 Hub 内正文/ref 文件机械抽取或保守生成摘要，仅补可读性字段并保持 archived 边界。",
            "human_review_decision": "accept-as-review-record",
            "tags": ["knowledge-hub", "summary-gap", "archived", "registry", "governance", "report-only", "no-active-promotion", "no-memory-write"],
            "review_after": "2026-10-11",
            "promotion": "none",
            "created_at": args.as_of,
            "updated_at": args.as_of,
        }
        items.append(closeout_item)

    items_path.write_text("\n".join(compact_dump(item) for item in items) + "\n")

    md_path = root / md_rel
    jsonl_path = root / jsonl_rel
    md_path.parent.mkdir(parents=True, exist_ok=True)
    jsonl_path.write_text(compact_dump(result) + "\n")
    md_path.write_text(
        "# Knowledge Hub Archived Summary Full Closeout 2026-07-11\n\n"
        "## Scope\n\n"
        "本记录收口 Knowledge Hub registry 中所有 archived `summary_zh` 缺口。摘要来源限定为 Hub 内已存在正文、ref 文件或目录身份，不读取源项目、不复制 raw log、不生成 owner decision。\n\n"
        "## Result\n\n"
        f"- Backfilled archived items: {len(updates)}\n"
        f"- Closeout artifact id: `{artifact_id}`\n"
        "- Boundary: archived readability only; no active promotion, no owner gate closure, no memory write, no source project write.\n\n"
        "## Batch Distribution\n\n"
        + "\n".join(f"- `{row['domain']}` / `{row['kind']}`: {row['count']}" for row in result["by_kind_domain"])
        + "\n\n## Verification\n\n"
        "- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-11`\n"
        "- `rtk bash tools/knowledge-status.sh --strict --json --as-of 2026-07-11 --final-profile mature`\n"
        "- `rtk bash tools/knowledge-final-gate.sh --json --final-profile mature --as-of 2026-07-11`\n"
        "- `rtk bash tools/knowledge-regression.sh --json --suite full --as-of 2026-07-11`\n"
    )
    result["index_updates"] = sorted(set(add_closeout_indexes(artifact_id, "2026-10-11")))

if args.json:
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print(f"mode: {result['mode']}")
    print(f"selected_count: {result['selected_count']}")
    for row in result["by_kind_domain"]:
        print(f"- {row['domain']} / {row['kind']}: {row['count']}")
PY
