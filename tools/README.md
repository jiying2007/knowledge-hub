# Knowledge Hub Tools

All tools are conservative by default.

用户、文档和自动化默认只调用稳定 shell 入口：

```bash
rtk bash ~/knowledge-hub/tools/<tool>.sh ...
```

不要在长期文档中直接引用内部 Python 入口，也不要绕过 `rtk` 裸跑 shell 命令。

- `knowledge-check.sh`: read-only validation.
  覆盖 registry JSON/JSONL 解析、owner/project/topic 登记、source index 和 source coverage 收口、owner-gated active 阻断、owner gate 字段阻断、item 日期和 source reference、validation reference 结构与路径、tag/promotion、registry 字段/路径/枚举/边界、migration record、template 必填字段、personal-local active 阻断、AI-generated active 人工复核门禁、source enum、文本知识和 `artifacts/manifests/` secret-pattern scan、核心索引缺失/过期/重复 item ref、`indexes/*.md` 本地 path/glob 引用、`--explain <item-id>` 条目诊断，以及 `--diagnostics` 中文错误分组。
- Stale `review_after` values in registry items are warnings, not blocking errors; invalid date format and `updated_at < created_at` remain errors.
- `knowledge-search.sh`: read-only text search across registered sources and local domains.
- `knowledge-status.sh`: read-only control-plane dashboard; summarizes `knowledge-check`, registry counts, source coverage, migrations, stale review dates, owner gate status, all-open owner summary commands, by-owner owner summary commands, owner forms JSONL commands, owner filled-form validation command templates, no-write landing-plan command templates, the next open owner gate commands and structured `strict_blockers`. Use `--strict` as a final-state gate that returns non-zero unless the status is `ok`; `strict_blockers[].commands` contains directly executable commands, while `strict_blockers[].command_templates` contains commands that require replacing placeholders such as `<owner-decisions.jsonl>`.
- `knowledge-final-gate.sh`: repository read-only final-state gate; runs `knowledge-check --diagnostics`, `knowledge-regression --json` and `knowledge-status --strict --json` together so terminal validation cannot miss regression drift. It returns non-zero unless all three gates are terminal-ok. The regression subcommand may create and clean temporary fixtures under `/tmp`; it must not modify Knowledge Hub content, registry, indexes or source project docs.
- `knowledge-doctor.sh`: read-only maintenance helper; runs `knowledge-check --diagnostics`, optional `--explain <item-id>`/search and optional `--owner-gates <source-id>` board without writing files.
- `knowledge-index-plan.sh`: read-only core index planner; prints registry-derived `by-owner`、`by-review-date` and `by-status` views without writing files.
- `knowledge-owner-gates.sh`: read-only owner gate board; prints unresolved owner decision worksheet rows, required owner fields, active exposure status and read-only current source identity without writing files. Use `--summary` to show all open gates, owner distribution, source identity counts and focus commands, `--owner <owner>` to filter one exact owner for assignment, `--checklist` to merge owner intake questions, hard gates and source identity into a closure checklist, `--forms` to print human-readable context plus copyable owner decision JSONL skeletons, `--forms-jsonl` to print only one compact JSONL skeleton per open row on stdout, `--validate-forms <jsonl>` to check filled owner forms including required fields, owner decision enums, date formats and `source_sha256/source_size` matching the observed current source identity, `--landing-plan` with validation to print a no-write manual landing plan, `--worksheet-id <id>` to focus one owner gate, and `--next-open` to focus the next open owner gate by `review_after, worksheet_id`.
- `knowledge-regression.sh`: read-only regression fixture runner; copies the repo to `/tmp`, mutates only temporary fixtures, and verifies key negative gates such as status bucket mismatch and partial owner resolution. It cleans temporary fixtures after each scenario by default, records structured failure details for internal exceptions, emits JSON in `--json` mode, and honors `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES` for low-space preflight.
- `knowledge-inventory.sh`: read-only inventory for registered sources.
- `knowledge-copy-first-plan.sh`: creates a reviewed JSONL copy-first manifest for a registered source; writes only the manifest under `artifacts/manifests/`.
- `knowledge-copy-first.sh`: reviewed copy-first migration from a JSONL manifest; dry-run by default.
- `knowledge-artifact-ref-plan.sh`: creates a JSONL artifact reference manifest with source URI, size and sha256 for non-text source files; it does not copy binary content.
- `knowledge-new.sh`: read-only manual-entry guide; prints template, registry, index, migration, validation steps and copyable manual skeletons without writing files. Supports `--owner <owner>`; defaults owner to `leiwenjun`, derives project from `--domain projects/<project>` when `--project` is omitted, and prints UTC default dates for registry and migration drafts.
- `knowledge-capture.sh`: dry-run candidate capture.
- `knowledge-promote.sh`: dry-run promotion plan.
- `knowledge-retire.sh`: dry-run retirement plan.

Writing requires explicit future implementation and must not be used by unattended automations.

## `knowledge-check.sh` 参数语义

`knowledge-check.sh` 是全仓一致性门禁。`--project` 和 `--domain` 目前只是兼容保留参数，不会缩小检查范围；传入时会在 `warnings` 中提示仍执行全仓检查。

`--explain <item-id>` 是只读人工诊断入口，用于解释单个 registry item 的基础字段、正文路径是否存在、核心索引引用计数、`by-status` bucket 和维护提示。它不修复文件、不生成索引、不执行 `validation_refs`，适合在 `knowledge-check` 报缺失或重复引用后定位人工修改点。

`--diagnostics` 是只读错误分组入口，用于把原始 errors 按 registry、source、migration、template、manual-entry、item、index、secret 和 explain 等类别生成中文摘要与人工修复提示。它不隐藏原始错误、不改变退出码、不自动修复，适合在全仓门禁失败后快速判断先改哪个文件。

示例：

下面的 `pcr02-project-docs` 是 owner-gated source-id 示例；维护其他 source 时替换为对应 `source_id`。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-status.sh
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root --owner-gates pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section status
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>'
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
```

## Evidence

命令证据应记录执行目录、完整 `rtk ...` 命令、日期、退出码、覆盖范围和中文结果摘要。写入计划工具默认先 dry-run；`--apply` 只能由人工在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备后触发。
