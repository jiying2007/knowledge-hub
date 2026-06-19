# Knowledge Hub Owner Gate Board Helper 2026-06-19

## 目标

新增只读 owner gate 看板入口，把 owner decision worksheet 中的未闭环条目、owner、必填字段、禁止动作和 active exposure 汇总出来，降低人工处理 owner-gated 内容时的维护成本。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| OGB-001 | owner-gated 条目分散在 worksheet、action board、registry 和索引中。 | 人工后续处理时容易漏看 owner、证据字段或 active 暴露状态。 | 新增 `tools/knowledge-owner-gates.sh`，从 worksheet 和 registry 只读生成看板。 |
| OGB-002 | 自动修复 owner-gated 条目会放大风险。 | 工具可能替 owner 做决策，或误把内容提升为 active。 | 工具只读输出，不创建、不修改、不提交、不提升任何文件。 |
| OGB-003 | 看板如果按 source 级别聚合，可能误伤同 source 中已迁移低风险文档。 | PCR02 docs 同时包含 copy-first、reference-first、artifact-ref 和 owner-gated 内容。 | 看板按 `source_id + source_path` 汇总，并显示对应 registry item 与 active exposure。 |

## 决策

- 新增稳定入口：`rtk bash tools/knowledge-owner-gates.sh`。
- 支持：
  - `--source-id <source-id>`
  - `--status all|open|resolved`
  - `--json`
- 默认输出 open rows。
- 输出字段包括 owner、worksheet_status、decision_options、required_owner_fields、must_not、registry_items 和 active_registry_items。
- 不执行 `validation_refs`，不读取源项目正文，不写 memory。

## 非目标

- 不生成 owner decision。
- 不迁移 owner-gated 正文。
- 不自动更新 registry/index/migration。
- 不修改源项目 docs。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --json` | 0 | PCR02 owner gate 看板返回 7 条 open、0 条 resolved、0 active exposure。 | `tools/knowledge-owner-gates.sh` | Knowledge Hub | owner-gate-board-helper |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs` | 0 | 中文可读输出列出 7 个 PCR02 owner-gated source_path、owner、必填证据和禁止动作。 | `tools/knowledge-owner-gates.sh` | Knowledge Hub | owner-gate-board-helper |
| `cd /tmp && rtk bash /home/leiwenjun/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --json` | 0 | 新工具可从非仓库 cwd 执行，返回 7 条 open、0 active exposure。 | `tools/knowledge-owner-gates.sh` | Entry smoke | owner-gate-board-helper |
| `/tmp missing owner worksheet fixture` | 1 | 临时副本隐藏 owner worksheet 后，工具返回 `status=blocked` 和缺失 worksheet 错误。 | `/tmp/kh-owner-board-missing.*` | Negative fixture | owner-gate-board-helper |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增工具和登记制品后全仓门禁通过，0 errors，0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-gate-board-helper |
| `rtk bash tools/knowledge-search.sh owner-gate-board-helper-applied --json` | 0 | 可检索到 3 处登记和说明，包括 registry item、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md` | Knowledge Hub | owner-gate-board-helper |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：如 owner worksheet schema 变化，更新本工具字段读取和本 manifest。
