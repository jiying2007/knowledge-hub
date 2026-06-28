# 命令与工具入口规范

## 目标

Knowledge Hub 的命令和工具必须保守、可复查、可回滚。用户和自动化都应通过稳定入口调用，不直接绕过治理边界。

## 调用入口

- 所有 shell 命令通过 `rtk` 执行。
- 仓库工具优先使用 `rtk bash ~/knowledge-hub/tools/<tool>.sh ...`。
- 文档、README、模板和 runbook 不直接要求用户调用内部 Python 文件。
- 新增脚本入口后，至少从非仓库 cwd 做一次帮助或 dry-run 验证。

## 工具分类

只读工具：

- `knowledge-check.sh`
- `knowledge-search.sh`
- `knowledge-inventory.sh`

写入计划工具：

- `knowledge-capture.sh`
- `knowledge-promote.sh`
- `knowledge-retire.sh`

写入计划工具默认 dry-run。`--apply` 只能在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备时由人工触发。

## 证据记录

命令类文档必须记录：

- 执行目录。
- 完整 `rtk ...` 命令。
- 执行日期。
- 退出码。
- 结果摘要。
- 失败时的阻塞原因和下一步。

## 禁止事项

- 不裸跑 `bash`、`git`、`python`、`rg`、`sed` 等命令。
- 不用 shell 重定向或 heredoc 写仓库文件。
- 不让无人值守自动化执行 `--apply`。
- 不绕过 registry 直接提升或退役条目。
- 不把工具输出中的敏感信息保存为长期正文。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
