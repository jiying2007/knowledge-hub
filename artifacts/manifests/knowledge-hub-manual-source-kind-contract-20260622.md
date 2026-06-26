# Knowledge Hub manual source and kind contract 2026-06-22

## 摘要

本轮压实人工新增入口和结构化检索之间的契约：

- `knowledge-new.sh` 普通 item 模式新增 `--item-source-id` / `--item-source-path`，只读校验 source 已在 `registry/sources.json` 登记后，才在 registry 草稿中输出 `source.source_id`、可选 `source.source_path`、`indexes/by-source.md` 草稿和带 `--source-id` 的定向检索命令。
- `knowledge-new.sh` 将模板别名映射为合法 `registry kind`，避免 `validation-report`、`owner-worksheet`、`external-source` 等输入 kind 被原样写进 registry 后无法通过 `knowledge-check`。
- `knowledge-check.sh`、`knowledge-search.sh`、`registry/schema.md` 和 `templates/README.md` 对齐扩展后的长期资产 kind：`debug-record`、`external-source-note`、`owner-decision-worksheet`、`audit-record`、`patent-disclosure`。
- `knowledge-search.sh --kind` 支持模板别名归一，例如 `validation-report` 归一为 `validation`，JSON 输出保留 `kind_normalized`。

本轮不新增 source coverage，不修改 PCR02 源项目，不复制 source 正文，不生成 owner decision，不关闭 owner gate，不写 memory，不启用自动化写操作。

## 处理的 Gap

| gap_id | 类型 | 处理动作 | 状态 |
|---|---|---|---|
| KH-MSK-001 | manual-maintenance | 普通 item 新增入口支持已登记 source 绑定，避免人工二次补 `source.source_id` 和 by-source 索引时漏项。 | applied |
| KH-MSK-002 | tooling | 模板 kind 与 registry/search/check kind 契约对齐，避免向导生成无法通过门禁或无法结构化检索的 kind。 | applied |
| KH-MSK-003 | regression | 新增 `manual-entry-registered-source-binding` 与 `knowledge-search-kind-alias-filters` 回归，并同步 regression helper manifest。 | applied |

## 边界

- `--item-source-id` 只用于 Knowledge Hub registry item 草稿，不登记新 source；新增 source 仍使用 `knowledge-new.sh --source`。
- 未登记 source id 会直接失败，不输出伪造 `source.source_id`。
- `--item-source-path` 必须配合 `--item-source-id` 使用。
- `source.source_id` 只表示来源关联，不等于 owner decision、source 内容语义验证或 active promotion。
- `kind_normalized` 只是搜索过滤归一化字段，不改变 registry 已落盘 kind。

## Evidence Index

| 命令 Command | 退出码 Exit Code | 中文结果摘要 Result Summary | 证据路径 Evidence Path | 层级 Layer | 关联制品 Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过：人工新增向导语法检查通过。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash -n tools/knowledge-search.sh` | 0 | 通过：结构化搜索入口语法检查通过。 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 通过：回归脚本语法检查通过。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner team-core --id pcr02-source-bound-runbook --path domains/projects/pcr02/current/runbooks/source-bound.md --item-source-id pcr02-project-docs --item-source-path runbooks/source-bound.md` | 0 | 通过：已登记 source 绑定输出 registered source 草稿、by-source 草稿和 source-id 定向搜索命令。 | `tools/knowledge-new.sh` | Manual Entry | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --id pcr02-unknown-source-runbook --path domains/projects/pcr02/current/runbooks/unknown-source.md --item-source-id not-registered-source` | 2 | 通过：未知 source id 被拒绝，未输出伪造 source。 | `tools/knowledge-new.sh` | Negative Test | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash tools/knowledge-search.sh prog_tool --kind validation-report --json --limit 5` | 0 | 通过：模板 kind alias `validation-report` 归一为 registry kind `validation`，JSON 输出含 `kind_normalized`。 | `tools/knowledge-search.sh` | Search | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 通过：93 个回归场景通过，新增回归进入总回归集合。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-manual-source-kind-contract-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 通过：registry、schema、index 和 manifest 一致性检查通过。 | `tools/knowledge-check.sh` | Gate | `knowledge-hub-manual-source-kind-contract-20260622` |

## 下一步

1. 保持 owner gate open，不代签、不生成 owner decision。
2. 后续人工新增 item 时优先提供 `--item-source-id`；未知 source 必须先走 source 登记或保留人工来源说明。
3. 后续新增模板别名时同步更新 `knowledge-new.sh`、`knowledge-search.sh`、`knowledge-check.sh`、`registry/schema.md` 和回归场景。
