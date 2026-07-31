"""Create governed items or print the current maintenance guide."""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import pathlib
import sys
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .common import KnowledgeHubError, load_json, resolve_today
from .lifecycle import capture


AI_ROLES = ("none", "drafted", "summarized", "translated", "rewritten", "classified", "extracted")
SOURCE_ENUMS = {
    "role": ("hub-canonical-source", "hub-runtime-input", "hub-native-source"),
    "authority": ("knowledge-hub-canonical", "runtime-input-provenance", "knowledge-hub-ledger"),
    "status": ("registered",),
    "write_policy": ("knowledge-hub-only", "runtime-read-only-input", "hub-native-registry"),
}
TEMPLATES = {
    "runbook": ("templates/runbook.md", "runbook"),
    "decision": ("templates/decision.md", "decision"),
    "validation": ("templates/validation-report.md", "validation"),
    "validation-report": ("templates/validation-report.md", "validation"),
    "project-archive": ("templates/archive-note.md", "project-archive"),
    "archive-note": ("templates/archive-note.md", "project-archive"),
    "debug-record": ("templates/debug-record.md", "debug-record"),
    "external-source-note": ("templates/external-source-note.md", "external-source-note"),
    "external-source": ("templates/external-source-note.md", "external-source-note"),
    "owner-decision-worksheet": ("templates/owner-decision-worksheet.md", "owner-decision-worksheet"),
    "owner-worksheet": ("templates/owner-decision-worksheet.md", "owner-decision-worksheet"),
    "patent-disclosure": ("templates/patent-disclosure.md", "patent-disclosure"),
    "patent": ("templates/patent-disclosure.md", "patent"),
    "artifact-ref": ("templates/artifact-ref.md", "artifact-ref"),
}
DEFAULT_TEMPLATE = ("templates/item.md", "")


class GuideParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if message.startswith("unrecognized arguments:"):
            unknown = message.split(":", 1)[1].strip().split()[0]
            self.exit(2, "ERROR unknown argument: {}\nRun: rtk bash ~/knowledge-hub/tools/knowledge-new.sh --help\n".format(unknown))
        super().error(message)


def _parser() -> argparse.ArgumentParser:
    parser = GuideParser(
        description="Print a Knowledge Hub maintenance guide or transactionally create a draft/reviewing item.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/xcrz-sigmastar-demo --owner team-core --id pcr02-example-runbook --path projects/xcrz-sigmastar-demo/current/runbooks/example.md\n"
            "  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/xcrz-sigmastar-demo --owner team-core --id pcr02-example-runbook --path projects/xcrz-sigmastar-demo/current/runbooks/example.md --dry-run --json\n"
            "  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id example-source --source-path sources/example-source --role hub-canonical-source --authority knowledge-hub-canonical --write-policy knowledge-hub-only --check \"rtk test -d sources/example-source\"\n"
            "  rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id runtime-example --source-path sources/runtime-example --role hub-runtime-input --authority runtime-input-provenance --write-policy runtime-read-only-input --no-check-reason \"runtime input; Hub control directory pending\"\n\n"
            "Guide mode is read-only. --dry-run prints an exact transaction plan; --apply performs the governed transaction."
        ),
    )
    parser.add_argument("--source", action="store_true", dest="source_mode")
    parser.add_argument("--source-id", default="")
    parser.add_argument("--source-path", default="")
    parser.add_argument("--item-source-id", default="")
    parser.add_argument("--item-source-path", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--authority", default="")
    parser.add_argument("--write-policy", default="")
    parser.add_argument("--check", default="")
    parser.add_argument("--no-check-reason", default="")
    parser.add_argument("--kind", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--owner", default="leiwenjun")
    parser.add_argument("--manual-source-reason", default="manual-entry:knowledge-new.sh")
    parser.add_argument("--manual-validation-pending", action="store_true")
    parser.add_argument("--manual-validation-reason", default="")
    parser.add_argument("--generated-by-ai", action="store_true")
    parser.add_argument("--ai-role", choices=AI_ROLES, default="none")
    parser.add_argument("--id", default="")
    parser.add_argument("--path", default="")
    parser.add_argument("--title", default="")
    parser.add_argument("--summary-zh", default="")
    parser.add_argument("--review-after", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--status", choices=("draft", "reviewing", "personal"), default="reviewing")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true")
    output.add_argument("--summary-json", action="store_true")
    return parser


def _add_months(value: dt.date, months: int = 3) -> dt.date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


def _compact(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=False, separators=(",", ":"))


def _owner_status(root: pathlib.Path, owner: str) -> str:
    path = root / "registry/owners.json"
    if not path.exists():
        return "owners-registry-missing"
    data = load_json(path, {}) or {}
    known = {str(row.get("id", "")) for row in data.get("owners", []) if isinstance(row, dict)}
    return "registered" if owner in known else "unknown-owner"


def _source_ids(root: pathlib.Path) -> set:
    data = load_json(root / "registry/sources.json", {}) or {}
    return {str(row.get("id", "")) for row in data.get("sources", []) if isinstance(row, dict)}


def _validate_common(args: argparse.Namespace) -> None:
    if args.apply and args.dry_run:
        raise KnowledgeHubError("--apply and --dry-run are mutually exclusive")
    if args.domain == "personal":
        raise KnowledgeHubError("domain=personal 不属于当前路径契约；请使用 --domain notes --path notes/personal/<file>.md")
    if args.path.startswith("domains/personal/"):
        raise KnowledgeHubError("domains/personal/ 不属于当前路径契约；请使用 notes/personal/...")
    if args.path.startswith("domains/projects/"):
        raise KnowledgeHubError("domains/projects/ 不属于当前路径契约；请使用 projects/<project>/...")
    if args.ai_role != "none":
        args.generated_by_ai = True
    if args.generated_by_ai and args.ai_role == "none":
        raise KnowledgeHubError("--generated-by-ai requires --ai-role <drafted|summarized|translated|rewritten|classified|extracted>")
    if args.manual_validation_pending and not args.manual_validation_reason:
        raise KnowledgeHubError("--manual-validation-pending requires --manual-validation-reason <reason>")


def _validate_source(args: argparse.Namespace) -> None:
    if args.item_source_id or args.item_source_path:
        raise KnowledgeHubError("source mode cannot combine --item-source-id/--item-source-path")
    if not args.check and not args.no_check_reason:
        raise KnowledgeHubError("source mode requires either --check <command> or --no-check-reason <reason>")
    if args.check and args.no_check_reason:
        raise KnowledgeHubError("source mode cannot combine --check with --no-check-reason; choose exactly one")
    values = {
        "role": args.role,
        "authority": args.authority,
        "status": "registered",
        "write_policy": args.write_policy,
    }
    for field, value in values.items():
        if value and value not in SOURCE_ENUMS[field]:
            raise KnowledgeHubError("source {} value is not allowed by registry/schema.md: {}".format(field, value))
    if args.source_id and args.source_path and args.source_path != "sources/{}".format(args.source_id):
        raise KnowledgeHubError("terminal source path must be Hub-local sources/<source-id>: {}".format(args.source_path))
    if args.apply or args.dry_run:
        raise KnowledgeHubError("source registration remains review-only; --apply/--dry-run are available for governed items only")


def _source_recommendation(role: str, policy: str) -> Tuple[str, str, str, str]:
    if role == "hub-runtime-input" and policy == "runtime-read-only-input":
        return (
            "runtime-input-reference-only",
            "runtime-input-index-summary-only",
            "运行态输入只登记 Hub control 和 provenance，不复制 raw history/session/memory，不写 memory。",
            "用摘要、候选和人工复核记录表达可用信息，raw 输入不进入正文层。",
        )
    if role == "hub-native-source" and policy == "hub-native-registry":
        return (
            "hub-native-source",
            "hub-native-ledger",
            "Hub 原生账本不需要外部来源；权威正文仍在 Hub registry、manifest 或 automation ledger。",
            "保持 Hub-native control，不创建非权威外部 source entry。",
        )
    return (
        "hub-canonical",
        "hub-canonical-copy-docs",
        "默认按终态 Hub-only source 处理；path 只能是 sources/<source_id>，当前知识入口只使用 Hub 内路径。",
        "默认通过 Hub source control、canonical target、artifact vault 和 source policy 表达终态状态，不生成外部回源入口。",
    )


def _source_guide(root: pathlib.Path, args: argparse.Namespace, today: dt.date) -> str:
    source_id = args.source_id or args.id or "<source-id>"
    source_path = args.source_path or "sources/{}".format(source_id)
    role = args.role or "hub-canonical-source"
    authority = args.authority or "knowledge-hub-canonical"
    source_status = "registered"
    policy = args.write_policy or "knowledge-hub-only"
    owner_state = _owner_status(root, args.owner)
    final_disposition, strategy, disposition_reason, strategy_reason = _source_recommendation(role, policy)
    registry_row: Dict[str, Any] = {
        "id": source_id,
        "path": source_path,
        "origin_path": "<external-origin-or-empty>",
        "role": role,
        "authority": authority,
        "status": source_status,
        "write_policy": policy,
        "source_strategy": strategy,
        "owner": args.owner,
        "review_after": _add_months(today).isoformat(),
        "final_disposition": final_disposition,
    }
    if args.check:
        registry_row["check"] = args.check
    else:
        registry_row["no_check_reason"] = args.no_check_reason
    coverage: Dict[str, Any] = {
        "id": "SCC-{}-{}".format(today.strftime("%Y%m%d"), source_id),
        "source_id": source_id,
        "status": "{}-pending-classification".format(source_status),
        "classification": strategy,
        "decision": "新增 source 已进入 Knowledge Hub 终态控制面；path 为 Hub-local，当前知识入口只使用 Hub 内路径。",
        "evidence": "registry/sources.json; indexes/by-source.md; sources/{}/README.md".format(source_id),
        "risk": "source coverage 只代表治理状态，不代表 owner decision 或 active fact。",
        "owner": args.owner,
        "checked_at": today.isoformat(),
    }
    if args.check:
        coverage["check"] = args.check
    else:
        coverage["no_check_reason"] = args.no_check_reason
    coverage["source_identity"] = {
        "type": "hub-source-control",
        "notes": "当前知识入口只使用 Hub 内 source control path；不把外部位置作为 active source path。",
    }
    warning = ""
    if owner_state == "unknown-owner":
        warning = "- owner_warning_zh: source registry owner 未在 registry/owners.json 登记；落盘前请先补 owner registry，或改用已登记 owner。\n"
    elif owner_state == "owners-registry-missing":
        warning = "- owner_warning_zh: registry/owners.json 不存在；落盘前请先恢复 owner registry。\n"
    no_check_summary = args.no_check_reason if not args.check else "<not-required: check provided>"
    return """# Knowledge Hub Source 登记向导

本命令只输出 source 人工维护清单，不创建、不修改、不提交任何文件。

## 输入摘要

- source_id: {source_id}
- source_path: {source_path}
- role: {role}
- authority: {authority}
- status: {source_status}
- write_policy: {policy}
- check: {check}
- no_check_reason: {no_check}
- owner: {owner}
- owner_registry_status: {owner_state}
{warning}
## 只读推荐提示

- recommended_final_disposition: {final_disposition}
- recommended_source_strategy: {strategy}
- disposition_reason_zh: {disposition_reason}
- source_strategy_reason_zh: {strategy_reason}
- recommendation_scope_zh: 以上只是人工填写提示，不代表 owner decision，不关闭 owner gate；可复制 JSON 仍默认保守，落盘前必须按 registry/schema.md、coverage manifest 和 owner gate 状态确认。

## 最小人工步骤

1. 在 registry/sources.json 增加 source object；path 必须是 sources/<source_id>。
2. 在 indexes/by-source.md 增加一行，并生成 sources/<source_id>/ 控制目录。
3. 在 source coverage closeout 增加 coverage row。
4. 运行：

   rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
   rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics

## 枚举速查

- role: hub-canonical-source / hub-runtime-input / hub-native-source
- authority: knowledge-hub-canonical / runtime-input-provenance / knowledge-hub-ledger
- status: registered
- write_policy: knowledge-hub-only / runtime-read-only-input / hub-native-registry
- final_disposition 常用值: hub-canonical / runtime-input-reference-only / hub-native-source

脚本会对已传入的 role、authority、status 和 write_policy 做预校验；final_disposition 仍需落盘前按 `registry/schema.md` 人工确认。

## 可复制草稿

### registry/sources.json object

```json
{registry_json}
```

### indexes/by-source.md 主表行

```md
| {source_id} | {role} | `{source_path}` |
```

### source coverage JSONL row

```json
{coverage_json}
```

## 不要做

- 不修改 source 目录或源项目文件。
- 不复制大附件、日志、二进制、脚本或 session 正文。
- 不生成 owner decision，不关闭 owner gate，不启用自动写操作，不写 memory。
""".format(
        source_id=source_id,
        source_path=source_path,
        role=role,
        authority=authority,
        source_status=source_status,
        policy=policy,
        check=args.check or "<空>",
        no_check=no_check_summary,
        owner=args.owner,
        owner_state=owner_state,
        warning=warning.rstrip(),
        final_disposition=final_disposition,
        strategy=strategy,
        disposition_reason=disposition_reason,
        strategy_reason=strategy_reason,
        registry_json=_compact(registry_row),
        coverage_json=_compact(coverage),
    )


def _template_for(kind: str) -> Tuple[str, str]:
    template, normalized = TEMPLATES.get(kind, DEFAULT_TEMPLATE)
    return template, normalized or kind or "<kind>"


def _item_guide(root: pathlib.Path, args: argparse.Namespace, today: dt.date, parser: argparse.ArgumentParser) -> str:
    if args.item_source_path and not args.item_source_id:
        raise KnowledgeHubError("--item-source-path requires --item-source-id <registered-source-id>")
    if args.item_source_id and args.item_source_id not in _source_ids(root):
        raise KnowledgeHubError("--item-source-id is not registered in registry/sources.json: {}".format(args.item_source_id))
    if not args.domain and args.path.startswith("notes/"):
        args.domain = "notes"
    if args.path.startswith("notes/personal/") and args.domain != "notes":
        raise KnowledgeHubError("目标路径 {} 位于 notes/personal/，但 --domain 为 {}；请改为 --domain notes。".format(args.path, args.domain or "<未指定>"))
    template, registry_kind = _template_for(args.kind)
    project = args.domain.split("/", 1)[1] if args.domain.startswith("projects/") else "<可选>"
    scope = "project-specific" if args.domain.startswith("projects/") else "team-general"
    visibility = "personal-local" if args.domain == "notes" and args.path.startswith("notes/personal/") else "team-internal"
    draft_status = "archived" if registry_kind == "project-archive" else "personal" if visibility == "personal-local" else "reviewing"
    owner_state = _owner_status(root, args.owner)
    warning = ""
    if owner_state == "unknown-owner":
        warning = "- owner_warning_zh: item owner 未在 registry/owners.json 登记；落盘前请先补 owner registry，或改用已登记 owner。\n"
    elif owner_state == "owners-registry-missing":
        warning = "- owner_warning_zh: registry/owners.json 不存在；落盘前请先恢复 owner registry。\n"
    source: Dict[str, Any] = {"type": "manual", "from": args.manual_source_reason}
    source_index = (
        "# indexes/by-source.md\n- {}: `{}`".format(args.item_source_id, args.id or "<id>")
        if args.item_source_id
        else "# indexes/by-source.md\n# 条件索引：本次未提供 --item-source-id；未知来源不要同步 by-source，也不要复制占位行。\n# - <真实-source-id>: `{}`".format(args.id or "<id>")
    )
    search_command = 'rtk bash ~/knowledge-hub/tools/knowledge-search.sh "{}" --json'.format(args.id or "<id>")
    if args.item_source_id:
        source = {"type": "registered", "source_id": args.item_source_id}
        if args.item_source_path:
            source["source_path"] = args.item_source_path
        source["from"] = args.manual_source_reason
        search_command = 'rtk bash ~/knowledge-hub/tools/knowledge-search.sh "{}" --source-id {} --json'.format(
            args.id or "<id>", args.item_source_id
        )
    review_after = args.review_after or _add_months(today).isoformat()
    validation_command = "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
    validation_refs: List[str] = [validation_command]
    if args.manual_validation_pending:
        validation_refs = [
            "manual_validation_pending: true",
            "reason: {}".format(args.manual_validation_reason),
            "required_followup: {}".format(validation_command),
        ]
    generated = bool(args.generated_by_ai)
    row: Dict[str, Any] = {
        "id": args.id or "<id>",
        "title": args.title or "<中文标题>",
        "kind": registry_kind,
        "domain": args.domain or "<domain>",
        "path": args.path or "<path>",
        "scope": scope,
        "visibility": visibility,
        "status": draft_status,
        "owner": args.owner,
        "source": source,
        "summary_zh": args.summary_zh or "<中文 1-3 句摘要>",
        "primary_language": "zh-CN",
        "source_language": "zh-CN",
        "translation_status": "not-required",
        "terminology_status": "pending-review",
        "review_status": "manual-entry-pending-review",
        "evidence_strength": "manual-entry-pending-validation",
        "evidence_refs": [],
        "promotion_decision": "none",
        "generated_by_ai": generated,
        "ai_role": args.ai_role,
        "ai_model_or_tool": "Codex" if generated else "",
        "ai_generated_at": today.isoformat() if generated else "",
        "human_reviewed_by": "",
        "human_reviewed_at": "",
        "review_basis": "",
        "validation_refs": validation_refs,
        "tags": ["knowledge-hub", "<topic>"],
        "review_after": review_after,
        "promotion": "none",
        "created_at": today.isoformat(),
        "updated_at": today.isoformat(),
    }
    project_block = ""
    project_step = "5. 如需主题入口，在 indexes/by-topic.md 增加可读路径引用。"
    if args.domain.startswith("projects/"):
        project_step = "5. 同步 indexes/by-project.md 的项目导航入口。"
        project_block = "\n# indexes/by-project.md\n- {}: {}\n".format(project, args.path or "<path>")
    decision_block = ""
    if args.kind == "decision":
        decision_block = "\n# indexes/by-decision.md\n- {}: {}\n".format(args.id or "<id>", args.path or "<path>")
    manual_validation = ""
    if args.manual_validation_pending:
        manual_validation = """
### 人工待验证说明

```yaml
manual_validation_pending: true
manual_validation_reason: {reason}
required_followup: {command}
```
""".format(reason=args.manual_validation_reason, command=validation_command)
    status_bucket = "archived" if draft_status == "archived" else "personal" if draft_status == "personal" else "reviewing"
    return """# Knowledge Hub 人工新增向导

本命令只输出人工维护清单，不创建、不修改、不提交任何文件。

## 输入摘要

- id: {item_id}
- input_kind: {input_kind}
- registry_kind: {registry_kind}
- domain: {domain}
- project: {project}
- owner: {owner}
- owner_registry_status: {owner_state}
{warning}- path: {path}
- item_source_id: {source_id}
- item_source_path: {source_path}
- 推荐模板: {template}
- 推荐 registry status: {draft_status}
- 推荐 visibility: {visibility}
- 推荐 scope: {scope}
- manual_source_reason: {manual_source_reason}
- manual_validation_pending: {manual_pending}
- generated_by_ai: {generated}
- ai_role: {ai_role}

## 最小人工步骤

1. 先确认正文唯一位置，避免同一正文维护两份。
2. 从 {template} 复制内容到目标路径，正文默认使用简体中文。
3. 在 registry/items.jsonl 新增一行，字段对齐 registry/schema.md。
4. 在 indexes/by-owner.md、indexes/by-review-date.md、indexes/by-status.md 登记新 id。
{project_step}
6. 维护条件索引并记录 Evidence Index。
7. 运行：

   rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
   {validation_command}
   rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain {item_id}
   {search_command}

## 可复制草稿

### registry/items.jsonl

```json
{registry_json}
```
{manual_validation}
### 核心索引

```md
# indexes/by-owner.md
- `{item_id}`

# indexes/by-review-date.md
- {review_after}: `{item_id}`

# indexes/by-status.md
- {status_bucket}: `{item_id}`
{project_block}{source_index}{decision_block}
```

### Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `{validation_command}` | 0 | 中文摘要，说明 registry、index 和正文通过门禁。 | <manifest-or-report-path> | Knowledge Hub | {item_id} |

## 不要做

- 不把 project-specific 内容提升到 domains/embedded/standards。
- 不把 personal-local 内容加入团队 active index。
- 不把 raw log、SDK、release binary 或 secret 写入正文。
- 不把 AI 生成内容直接标记为 active，除非已有人工复核证据。
""".format(
        item_id=args.id or "<待填写>",
        input_kind=args.kind or "<kind>",
        registry_kind=registry_kind,
        domain=args.domain or "<待填写>",
        project=project,
        owner=args.owner,
        owner_state=owner_state,
        warning=warning,
        path=args.path or "<待填写>",
        source_id=args.item_source_id or "<未指定>",
        source_path=args.item_source_path or "<未指定>",
        template=template,
        draft_status=draft_status,
        visibility=visibility,
        scope=scope,
        manual_source_reason=args.manual_source_reason,
        manual_pending=str(args.manual_validation_pending).lower(),
        generated=str(generated).lower(),
        ai_role=args.ai_role,
        project_step=project_step,
        validation_command=validation_command,
        search_command=search_command,
        registry_json=_compact(row),
        manual_validation=manual_validation,
        review_after=review_after,
        status_bucket=status_bucket,
        project_block=project_block,
        source_index=source_index,
        decision_block=decision_block,
    )


def _transaction(root: pathlib.Path, args: argparse.Namespace, today: dt.date) -> Dict[str, Any]:
    if not args.kind or not args.id or not args.path:
        raise KnowledgeHubError("--dry-run/--apply require --kind, --id and --path")
    template, registry_kind = _template_for(args.kind)
    if registry_kind == "project-archive":
        raise KnowledgeHubError("knowledge-new --apply creates draft/reviewing/personal items only; archive through an authorized lifecycle transition")
    status = "personal" if args.domain == "notes" and args.path.startswith("notes/personal/") else args.status
    return capture(
        root,
        root / template,
        registry_kind,
        args.path,
        today,
        args.apply,
        item_id=args.id,
        title=args.title,
        domain=args.domain,
        owner=args.owner,
        visibility="personal-local" if status == "personal" else "team-internal",
        status=status,
        review_after=args.review_after,
        tags=args.tag or (registry_kind, "knowledge-new", "manual-validation-pending"),
        summary_zh=args.summary_zh,
        generated_by_ai=args.generated_by_ai,
        ai_role=args.ai_role if args.ai_role != "none" else "drafted",
        source_type="manual",
        source_from=args.manual_source_reason,
        registered_source_id=args.item_source_id,
        registered_source_path=args.item_source_path,
    )


def _transaction_summary(payload: Mapping[str, Any]) -> Dict[str, Any]:
    transaction = payload.get("transaction", {})
    if not isinstance(transaction, Mapping):
        transaction = {}
    return {
        "schema_version": 1,
        "projection": "knowledge-new-summary-v1",
        "status": payload.get("status", ""),
        "action": payload.get("action", ""),
        "id": payload.get("id", ""),
        "target": payload.get("target", ""),
        "created_status": payload.get("created_status", ""),
        "active_promotion": payload.get("active_promotion", False),
        "transaction_id": transaction.get("transaction_id", ""),
        "changed_path_count": len(transaction.get("changed_paths", []) or []),
        "rolled_back": transaction.get("rolled_back", False),
        "diagnostic_count": len(transaction.get("diagnostics", []) or []),
        "as_of": payload.get("as_of", ""),
        "dry_run": payload.get("dry_run", False),
    }


def main(argv: Sequence[str] = ()) -> int:
    values = list(argv) if argv else sys.argv[1:]
    if not values:
        raise SystemExit("Knowledge Hub root argument is required")
    root = pathlib.Path(values.pop(0)).resolve()
    parser = _parser()
    args = parser.parse_args(values)
    try:
        _validate_common(args)
        today, date_source = resolve_today(args.as_of)
        if args.source_mode or args.kind == "source":
            args.source_mode = True
            _validate_source(args)
            guide = _source_guide(root, args, today)
        elif args.apply or args.dry_run:
            payload = _transaction(root, args, today)
            payload.update({"as_of": today.isoformat(), "date_source": date_source, "dry_run": not args.apply})
            if args.json or args.summary_json:
                projection = (
                    _transaction_summary(payload)
                    if args.summary_json
                    else payload
                )
                print(json.dumps(projection, ensure_ascii=False, indent=2))
            else:
                print("\n".join("{}: {}".format(k, v) for k, v in payload.items()))
            return 0
        else:
            guide = _item_guide(root, args, today, parser)
        if args.json or args.summary_json:
            guide_payload = {
                "status": "guide",
                "read_only": True,
                "guide": guide,
                "as_of": today.isoformat(),
            }
            if args.summary_json:
                guide_payload = {
                    "schema_version": 1,
                    "projection": "knowledge-new-summary-v1",
                    "status": "guide",
                    "read_only": True,
                    "source_mode": bool(args.source_mode),
                    "kind": args.kind,
                    "id": args.id,
                    "path": args.path,
                    "as_of": today.isoformat(),
                    "next_action": "rerun without --summary-json for the full guide",
                }
            print(json.dumps(guide_payload, ensure_ascii=False, indent=2))
        else:
            print(guide, end="" if guide.endswith("\n") else "\n")
        return 0
    except KnowledgeHubError as exc:
        if args.json or args.summary_json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print("ERROR {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
