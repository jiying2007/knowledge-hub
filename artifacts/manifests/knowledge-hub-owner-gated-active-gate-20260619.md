# Knowledge Hub Owner-Gated Active Gate 2026-06-19

## 目标

把 owner decision worksheet 中仍未闭环的源路径纳入 `knowledge-check` 默认门禁，防止 PCR02 owner-gated 文档在缺少 owner 决策、目标决策和复核证据时被登记成 `active`。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| OGA-001 | PCR02 owner-review 包已经列出 7 个未闭环源路径，但此前门禁只保护通用 active safety，不直接关联 worksheet。 | 维护者后续可能手工新增 registry item，把 owner-gated 源路径误登记为 active。 | `knowledge-check` 读取 `*owner-decision-worksheets-*.jsonl`，建立未闭环 `source_id + source_path` 集合。 |
| OGA-002 | `pcr02-project-docs` 同时包含已 copy-first 文档和 owner-gated 文档，不能按 source 级别一刀切。 | 误伤已经迁移并处于 reviewing/archive 的低风险条目。 | 门禁只匹配 worksheet 中具体 `source_path`，不阻断同 source 下其他路径。 |
| OGA-003 | 自动提升 owner-gated 条目会扩大治理复杂度。 | owner 决策、适用版本和验证证据可能被绕过。 | 本轮只做只读检查，不生成 owner 决策、不迁移正文、不启用自动化。 |

## 决策

- 默认读取 `artifacts/manifests/*owner-decision-worksheets-*.jsonl`。
- 对每个未闭环 worksheet 行提取 `source_id` 和 `source_path`。
- 若 `registry/items.jsonl` 中任一 item 的 `status=active` 且 `source.source_id + source.source_path` 命中未闭环集合，则 `knowledge-check` 报错。
- 已有 `reviewing`、`archived`、reference-first、artifact-ref 和控制面 audit 条目不因此被阻断。

## 非目标

- 不修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不自动生成 owner 决策或 owner sign-off。
- 不写 `~/.codex/memories`。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 本门禁默认启用后全仓通过，0 errors，0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-gated-active-gate |
| `/tmp owner-gated active fixture` | 1 | 临时副本把 `runbooks/asan-debug-guide.md` 登记为 active 后，仅触发 `owner-gated-active` 一类错误。 | `/tmp/kh-owner-gate-clean2.*` | Negative fixture | owner-gated-active-gate |
| `rtk bash tools/knowledge-search.sh owner-gated-active-gate-applied --json` | 0 | 可检索到 3 处登记和说明，包括 registry item、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md` | Knowledge Hub | owner-gated-active-gate |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：如 owner worksheet 行完成 owner 决策，应补 owner_decision、target_decision、reviewed_by、reviewed_at 和 resolved/closed 状态，再允许后续 active 评估。
