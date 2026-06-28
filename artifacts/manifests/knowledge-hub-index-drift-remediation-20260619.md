# Knowledge Hub Index Drift Remediation - 2026-06-19

## 摘要

本次修复把 registry 与核心索引之间的覆盖漂移纳入门禁，并补齐当前已发现的 `by-owner`、`by-review-date` 漏项。

本 manifest 是治理修复记录，不是内容迁移，不修改源项目 docs，不提升任何 PCR02 owner-gated 条目，不写 `~/.codex/memories`。

## 问题地图

| ID | 发现 | 级别 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| KHD-20260619-001 | `indexes/by-owner.md` 未覆盖全部 registry item。 | P1 | 只读核对曾发现缺 26 个 item；其中迁移过程 item 已在成熟态退役，当前以 `registry/retired-process-ledger.jsonl` 和 source-control 证据恢复。 | 已按 owner 从 `registry/items.jsonl` 补齐；迁移过程 item 后续不再作为当前索引目标。 |
| KHD-20260619-002 | `indexes/by-review-date.md` 未覆盖全部 registry item。 | P1 | 只读核对发现缺 37 个 item，主要集中在 2026-07-16 和 2026-09-18 review bucket。 | 已按 `review_after` 从 `registry/items.jsonl` 补齐。 |
| KHD-20260619-003 | `tools/knowledge-check.sh` 过去不校验索引覆盖，无法防止 registry/index 再次漂移。 | P1 | 原门禁只检查 registry 基础字段、路径、secret pattern 和 source path。 | 已增加 `by-owner`、`by-review-date`、`by-status` 覆盖检查；`by-status` 支持现有 range 语法。 |

## 已改内容

- `tools/knowledge-check.sh`：新增 registry item 到核心索引的覆盖检查。
- `indexes/by-owner.md`：补齐 `leiwenjun`、`team-core`、`pcr02-registry-owner` 三类 owner。
- `indexes/by-review-date.md`：补齐所有 registry item 的 review bucket。
- `tools/README.md`：补充 `knowledge-check.sh` 的索引漂移检查职责。
- `registry/items.jsonl`、`registry/items.jsonl` 和索引：登记本次治理修复记录。

## 验证

已执行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json
rtk bash tools/knowledge-search.sh "source control unification" --json
rtk git diff --check
```

预期结果：

- `knowledge-check` 返回 `pass`，无 errors/warnings。
- source inventory 终态证据可通过 `registry/sources.json`、`sources/<source_id>/inventory.jsonl` 和 `knowledge-hub-source-control-unification-20260624` 恢复。
- diff 无 whitespace error。

## 剩余风险

- `indexes/by-project.md` 和 `indexes/by-topic.md` 仍是导航型人工索引，不要求覆盖每个 registry item；后续若需要强一致，应新增单独的生成器或定义 project/topic 的覆盖契约。
- `indexes/by-status.md` 仍保留 range 写法；当前门禁已支持 range 展开，但长期建议生成化，减少人工编辑大行。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`index-drift-remediation-applied`
- promotion：`none`
- review_after：`2026-09-19`
