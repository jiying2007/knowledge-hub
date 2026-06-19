# Knowledge Hub Tools

All tools are conservative by default.

用户、文档和自动化默认只调用稳定 shell 入口：

```bash
rtk bash ~/knowledge-hub/tools/<tool>.sh ...
```

不要在长期文档中直接引用内部 Python 入口，也不要绕过 `rtk` 裸跑 shell 命令。

- `knowledge-check.sh`: read-only validation, including registry field/path/enum/domain-boundary checks, migration record structure/local-target checks, item template required-field checks, personal-local active blocking, AI-generated active human-review gates, source enum checks, secret-pattern scan for text knowledge and `artifacts/manifests/`, core index drift checks for missing/stale item refs, and local path/glob reference checks in `indexes/*.md`.
- `knowledge-search.sh`: read-only text search across registered sources and local domains.
- `knowledge-inventory.sh`: read-only inventory for registered sources.
- `knowledge-copy-first.sh`: reviewed copy-first migration from a JSONL manifest; dry-run by default.
- `knowledge-new.sh`: read-only manual-entry guide; prints template, registry, index, migration and validation steps without writing files.
- `knowledge-capture.sh`: dry-run candidate capture.
- `knowledge-promote.sh`: dry-run promotion plan.
- `knowledge-retire.sh`: dry-run retirement plan.

Writing requires explicit future implementation and must not be used by unattended automations.

## `knowledge-check.sh` 参数语义

`knowledge-check.sh` 是全仓一致性门禁。`--project` 和 `--domain` 目前只是兼容保留参数，不会缩小检查范围；传入时会在 `warnings` 中提示仍执行全仓检查。

## Evidence

命令证据应记录执行目录、完整 `rtk ...` 命令、日期、退出码、覆盖范围和中文结果摘要。写入计划工具默认先 dry-run；`--apply` 只能由人工在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备后触发。
