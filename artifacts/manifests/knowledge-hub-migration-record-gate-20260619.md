# Knowledge Hub Migration Record Gate 2026-06-19

## 目标

把 `registry/migrations.jsonl` 从人工约定提升为 `knowledge-check` 可执行门禁，减少治理制品、迁移记录和索引之间的长期漂移。

## 源事实

- `registry/migrations.jsonl` 是迁移、引用、归档、门禁变更的审计链路。
- 现有记录已经普遍包含 `from`、`to`、`mode`、`status`、`checked_at`、`notes`。
- 迁移目标 `to` 应指向 Knowledge Hub 内的真实文件或目录。
- 外部源 `from` 可能是旧项目路径或人类说明，本次不强制其存在，避免把外部项目状态变成 Knowledge Hub 的本地门禁。

## 问题地图

| ID | 发现 | 风险 | 本次动作 |
|---|---|---|---|
| MRG-001 | `migrations.jsonl` 只有 JSONL 语法校验，没有结构门禁 | 可追溯记录可能缺字段仍通过 | 增加必填字段检查 |
| MRG-002 | `checked_at` 未被机器检查 | 日期漂移或不可排序 | 增加 ISO 日期检查 |
| MRG-003 | `to` 未被验证为本仓真实目标 | 迁移记录可能指向不存在制品 | 增加相对本地路径和存在性检查 |
| MRG-004 | 一条历史记录的 `to` 是人类描述 | 新门禁无法执行 | 归一为对应 manifest 路径 |

## 已落盘

- 更新 `tools/knowledge-check.sh`：新增 migration 必填字段、日期、相对本地 `to` 目标存在性检查。
- 更新 `registry/schema.md`：新增 `migrations.jsonl` schema 与 invariants。
- 更新 `tools/README.md`：说明 `knowledge-check.sh` 覆盖 migration record checks。
- 更新 `templates/migration-record.md`：改为可复制 JSONL 行、字段说明和验证命令，避免人工按旧 Markdown/frontmatter 模板新增不合规记录。
- 更新 `registry/migrations.jsonl`：归一中文长期资产治理记录的 `to`，并登记本次门禁。
- 更新 registry 与核心索引，登记本治理制品。

## 非目标

- 不校验外部 `from` 路径是否存在。
- 不修改 PCR02 源项目 docs。
- 不启用自动化，不写 `~/.codex/memories`。
- 不解析 migration `status` 业务枚举；这些状态仍作为审计状态保留。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . artifacts/manifests/knowledge-hub-migration-record-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-search.sh "migration-record-gate-applied" --json`
- `rtk git diff --check`
- 负向样例：临时副本中删除 migration `notes` 字段，应失败。
- 负向样例：临时副本中把 migration `to` 改为不存在路径，应失败。

## 状态

- `review_status`: migration-record-gate-applied
- `status`: reviewing
- `owner`: leiwenjun
- `review_after`: 2026-09-19
