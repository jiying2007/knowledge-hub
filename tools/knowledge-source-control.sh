#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

exec rtk python3 - "$ROOT" "$@" <<'PY'
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1]).resolve()
argv = sys.argv[2:]

parser = argparse.ArgumentParser(description="Create or check source control directories for registered Knowledge Hub sources.")
parser.add_argument("--apply", action="store_true", help="Write missing source control files.")
parser.add_argument("--json", action="store_true")
parser.add_argument("--as-of", default="", metavar="YYYY-MM-DD")
args = parser.parse_args(argv)

today = args.as_of or dt.date.today().isoformat()

def load_json(path):
    return json.loads(path.read_text())

def load_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows

def select_source_coverage():
    candidates = []
    pattern = re.compile(r"knowledge-hub-source-coverage-closeout-(\d{8})\.jsonl$")
    for path in sorted((root / "artifacts" / "manifests").glob("knowledge-hub-source-coverage-closeout-*.jsonl")):
        match = pattern.match(path.name)
        if match:
            candidates.append((match.group(1), path))
    return candidates[-1][1] if candidates else None

def first_sentence(value):
    text = str(value or "").strip()
    if not text:
        return ""
    return text.split("。", 1)[0] + ("。" if "。" in text else "")

sources = load_json(root / "registry" / "sources.json").get("sources", []) + load_jsonl(root / "registry" / "retired-sources.jsonl")
coverage_path = select_source_coverage()
coverage_by_source = {
    row.get("source_id"): row
    for row in load_jsonl(coverage_path) if row.get("source_id")
}

source_type_rules = {
    "hub-canonical-source": ("markdown", "copy-body"),
    "hub-runtime-input": ("archive", "reference-only"),
    "hub-native-source": ("automation-run", "reference-only"),
    "codex-history-source": ("history", "summary-only"),
    "codex-session-source": ("session", "summary-only"),
    "codex-archive-registry-source": ("archive", "summary-only"),
    "codex-automation-source": ("automation-run", "reference-only"),
    "codex-governance-source": ("archive", "summary-only"),
    "auxiliary-memory-source": ("archive", "reference-only"),
    "project-current-tools-source": ("tool", "reference-only"),
    "project-product-test-source": ("artifact", "artifact-ref"),
    "project-current-knowledge-source": ("markdown", "summary-only"),
    "project-scratch-source": ("archive", "archive-only"),
    "project-root-artifact-source": ("artifact", "artifact-ref"),
    "project-agent-rules-source": ("markdown", "reference-only"),
    "project-agent-config-source": ("config", "artifact-ref"),
    "team-knowledge-source": ("markdown", "summary-only"),
    "project-archive-source": ("markdown", "copy-body"),
    "patent-source": ("markdown", "copy-body"),
    "project-current-docs-source": ("markdown", "copy-body"),
}

results = []
written = []
missing = []

for source in sources:
    source_id = source.get("id", "")
    if not source_id:
        continue
    role = source.get("role", "")
    coverage = coverage_by_source.get(source_id, {})
    source_dir = root / "sources" / source_id
    object_type, disposition = source_type_rules.get(role, ("unknown", "summary-only"))
    if source.get("final_disposition") in {"auxiliary-recall-only", "reference-first-registered", "owner-gated-pending-decision", "artifact-ref-registered"}:
        disposition = "reference-only" if disposition == "copy-body" else disposition
    if "artifact" in str(source.get("source_strategy", "")) and disposition == "copy-body":
        disposition = "artifact-ref"
    target_path = f"sources/{source_id}/README.md"
    canonical_target = str(source.get("canonical_target", ""))
    if disposition == "copy-body":
        if canonical_target.startswith(("projects/", "domains/", "notes/")):
            target_path = canonical_target
        else:
            disposition = "reference-only"

    inventory_row = {
        "id": f"{source_id}-root",
        "source_id": source_id,
        "source_path": source.get("path", ""),
        "origin_path": source.get("origin_path", ""),
        "object_type": object_type,
        "hub_disposition": disposition,
        "target_path": target_path,
        "sha256": "",
        "size_bytes": 0,
        "status": "covered",
        "reason_zh": coverage.get("decision") or source.get("source_strategy", ""),
        "risk_zh": coverage.get("risk") or "未逐项展开前不得把 source 原文直接提升为 active facts。",
        "checked_at": today,
    }

    readme = f"""# {source_id}

## 定位

- Source ID: `{source_id}`
- Hub source path: `{source.get('path', '')}`
- Role: `{role}`
- Authority: `{source.get('authority', '')}`
- Final disposition: `{source.get('final_disposition', '')}`
- Source strategy: `{source.get('source_strategy', '')}`
- Owner: `{source.get('owner', '')}`
- Review after: `{source.get('review_after', '')}`

## Hub 管理方式

{coverage.get('decision') or '该 source 已进入 Knowledge Hub 统一 source 控制面。'}

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

{coverage.get('risk') or 'source 内容仍需按对象级 inventory 和 owner/review 规则逐步收敛。'}

## 维护入口

- 清单：`sources/{source_id}/inventory.jsonl`
- 覆盖：`sources/{source_id}/coverage.md`
- 策略：`sources/{source_id}/source-policy.md`
"""

    coverage_text = f"""# {source_id} 覆盖状态

## 结论

- Status: `{coverage.get('status', source.get('status', 'registered'))}`
- Classification: `{coverage.get('classification', '')}`
- Checked at: `{coverage.get('checked_at', today)}`

## 决策

{coverage.get('decision') or first_sentence(source.get('source_strategy', ''))}

## 风险

{coverage.get('risk') or '不得把未复核 source 原文直接提升为 active facts。'}

## 证据

- `registry/sources.json`
- `{coverage_path.relative_to(root) if coverage_path else 'artifacts/manifests/knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl'}`
- `sources/{source_id}/inventory.jsonl`
"""

    plan = f"""# {source_id} Source 策略

## 终态

该 source 必须通过 `sources/{source_id}/` 在 Hub 内可恢复、可搜索、可审计。

## 当前策略

- `registry/sources.json` 的 `path` 已收敛到 `sources/{source_id}`。
- 当前知识入口只使用 Hub 内路径。
- 通过 inventory 记录正文、附件、runtime input 或 hub-native 边界。

## 后续维护

- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。
"""

    desired = {
        source_dir / "README.md": readme,
        source_dir / "coverage.md": coverage_text,
        source_dir / "source-policy.md": plan,
        source_dir / "inventory.jsonl": json.dumps(inventory_row, ensure_ascii=False, separators=(",", ":")) + "\n",
    }

    source_result = {"source_id": source_id, "dir": f"sources/{source_id}", "missing": [], "written": []}
    for path, content in desired.items():
        if not path.exists():
            source_result["missing"].append(str(path.relative_to(root)))
            missing.append(str(path.relative_to(root)))
            if args.apply:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
                source_result["written"].append(str(path.relative_to(root)))
                written.append(str(path.relative_to(root)))
        elif args.apply and path.read_text() != content:
            path.write_text(content)
            source_result["written"].append(str(path.relative_to(root)))
            written.append(str(path.relative_to(root)))
    results.append(source_result)

status = "applied" if args.apply else "planned"
if not args.apply and missing:
    status = "needs-apply"

payload = {
    "status": status,
    "read_only": not args.apply,
    "source_count": len(sources),
    "coverage_manifest": str(coverage_path.relative_to(root)) if coverage_path else "",
    "missing_count": len(missing),
    "written_count": len(written),
    "missing": missing,
    "written": written,
    "results": results,
}

if args.json:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
else:
    print(f"status: {payload['status']}")
    print(f"source_count: {payload['source_count']}")
    print(f"missing_count: {payload['missing_count']}")
    print(f"written_count: {payload['written_count']}")
    for path in written:
        print(f"written: {path}")
    for path in missing[:50]:
        print(f"missing: {path}")

sys.exit(0 if args.apply or not missing else 1)
PY
