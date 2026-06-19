# Migration Record Template

用于向 `registry/migrations.jsonl` 手工追加一条迁移、引用、归档或治理记录。本文是人工模板，不是正文知识条目。

## 可复制 JSONL 行

复制下面一行到 `registry/migrations.jsonl`，替换尖括号内容，保持单行 JSON：

```json
{"from":"<source path, manifest, registry id or human-readable source>","to":"<existing Knowledge Hub local path>","mode":"<migration-or-governance-mode>","status":"<planned|applied|reviewing|pending-owner-review|...>","checked_at":"YYYY-MM-DD","notes":"<中文摘要；说明做了什么、未做什么、边界和验证结果>"}
```

## 字段说明

- `from`：来源，可以是旧项目路径、manifest、registry id、工具名或人工说明；不要求本地存在。
- `to`：Knowledge Hub 内已经存在的相对路径，例如 `artifacts/`、`domains/`、`registry/`、`indexes/`、`governance/`、`tools/` 或 `templates/`。
- `mode`：本次动作类型，例如 `copy-first-apply`、`artifact-ref-register`、`manual-entry-guide`。
- `status`：审计状态，使用人可读状态；不要把它当作 registry item 的 `status`。
- `checked_at`：检查日期，格式必须是 `YYYY-MM-DD`。
- `notes`：中文摘要，必须写清边界，例如未修改源项目、未启用自动化、未写 memory、未提升 active。

## 多目标写法

多个 `to` 目标用英文分号分隔，且每个目标都必须存在：

```json
{"from":"registry/items.jsonl","to":"artifacts/manifests/example.md; artifacts/manifests/example.jsonl","mode":"example","status":"applied","checked_at":"YYYY-MM-DD","notes":"中文摘要。"}
```

## 验证

```bash
rtk jq -c . registry/migrations.jsonl
rtk bash tools/knowledge-check.sh --dry-run --json
```

## 常见错误

- `to` 写成绝对路径。
- `to` 写成人类描述而不是本仓相对路径。
- `to` 指向尚未创建的 manifest 或目录。
- `checked_at` 不是 `YYYY-MM-DD`。
- `notes` 没写边界，导致后续无法判断是否修改了源项目、是否启用自动化或是否提升 active。
