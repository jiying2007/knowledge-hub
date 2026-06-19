# Knowledge Hub Tools

All tools are conservative by default.

用户、文档和自动化默认只调用稳定 shell 入口：

```bash
rtk bash ~/knowledge-hub/tools/<tool>.sh ...
```

不要在长期文档中直接引用内部 Python 入口，也不要绕过 `rtk` 裸跑 shell 命令。

- `knowledge-check.sh`: read-only validation, including registry JSON/JSONL parse checks, registry owner/project/topic registration checks, source index coverage checks, registered source coverage closeout checks, owner-gated source_path active blocking from decision worksheets, registry item date consistency checks, item source reference checks, validation reference structure/path checks, item tag/promotion checks, registry field/path/enum/domain-boundary checks, migration record structure/local-target checks, item template required-field checks, personal-local active blocking, AI-generated active human-review gates, source enum checks, secret-pattern scan for text knowledge and `artifacts/manifests/`, core index drift checks for missing/stale/duplicate item refs, local path/glob reference checks in `indexes/*.md`, `--explain <item-id>` item-level manual maintenance diagnostics, and `--diagnostics` Chinese error grouping.
- Stale `review_after` values in registry items are warnings, not blocking errors; invalid date format and `updated_at < created_at` remain errors.
- `knowledge-search.sh`: read-only text search across registered sources and local domains.
- `knowledge-doctor.sh`: read-only maintenance helper; runs `knowledge-check --diagnostics`, optional `--explain <item-id>` and optional search without writing files.
- `knowledge-index-plan.sh`: read-only core index planner; prints registry-derived `by-owner`、`by-review-date` and `by-status` views without writing files.
- `knowledge-inventory.sh`: read-only inventory for registered sources.
- `knowledge-copy-first-plan.sh`: creates a reviewed JSONL copy-first manifest for a registered source; writes only the manifest under `artifacts/manifests/`.
- `knowledge-copy-first.sh`: reviewed copy-first migration from a JSONL manifest; dry-run by default.
- `knowledge-artifact-ref-plan.sh`: creates a JSONL artifact reference manifest with source URI, size and sha256 for non-text source files; it does not copy binary content.
- `knowledge-new.sh`: read-only manual-entry guide; prints template, registry, index, migration, validation steps and copyable manual skeletons without writing files.
- `knowledge-capture.sh`: dry-run candidate capture.
- `knowledge-promote.sh`: dry-run promotion plan.
- `knowledge-retire.sh`: dry-run retirement plan.

Writing requires explicit future implementation and must not be used by unattended automations.

## `knowledge-check.sh` 参数语义

`knowledge-check.sh` 是全仓一致性门禁。`--project` 和 `--domain` 目前只是兼容保留参数，不会缩小检查范围；传入时会在 `warnings` 中提示仍执行全仓检查。

`--explain <item-id>` 是只读人工诊断入口，用于解释单个 registry item 的基础字段、正文路径是否存在、核心索引引用计数、`by-status` bucket 和维护提示。它不修复文件、不生成索引、不执行 `validation_refs`，适合在 `knowledge-check` 报缺失或重复引用后定位人工修改点。

`--diagnostics` 是只读错误分组入口，用于把原始 errors 按 registry、source、migration、template、manual-entry、item、index、secret 和 explain 等类别生成中文摘要与人工修复提示。它不隐藏原始错误、不改变退出码、不自动修复，适合在全仓门禁失败后快速判断先改哪个文件。

示例：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section status
```

## Evidence

命令证据应记录执行目录、完整 `rtk ...` 命令、日期、退出码、覆盖范围和中文结果摘要。写入计划工具默认先 dry-run；`--apply` 只能由人工在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备后触发。
