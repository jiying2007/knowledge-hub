# 全局路径路由（Path Routing）

本文件定义 Knowledge Hub 终态下“归档路径在哪里”“会话总结写哪里”“旧路径还能不能用”的统一回答口径。它约束新增内容和自动化路由；历史会话、Git 历史和 provenance 字段只保留事实证据，不作为新增入口。

## 总原则

- 新增知识、归档、会话总结、排障记录和 Codex 工作流材料默认写入 `~/knowledge-hub`。
- 涉及项目事实、归档路径、历史决策、runbook、source 状态、发布验证或排障结论的问题，回答前先做 Hub 上下文预检。
- 旧外部路径只能作为 `origin_path`、历史 manifest、Git 历史或只读 provenance 出现。
- 回答路径类问题时，先给 Hub canonical path，再说明旧路径状态；不得把旧路径作为默认落盘目录。
- 不直接改写 `~/.codex/memories` 或历史 session。需要修正召回口径时，先在 Hub 产出 report-only 审计和 memory candidate，再经授权处理。
- 不在源项目内新增 `docs/`、`knowledge/`、`tools/` 作为知识入口。项目源码仓只保留本地运行规则和项目自身源码/配置。

## Knowledge Hub Preflight

Codex 在任意项目目录处理以下任务时，应先运行或等价执行 Hub 上下文预检：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "<用户问题或任务>" --task-type <type> --json
```

`task-type` 常用值：

- `archive`：归档路径、会话总结、长期沉淀。
- `debug`：core、GDB、日志、现场排障。
- `release`：构建、发布、OTA、NAS、版本记录。
- `decision`：当前策略、owner decision、废弃/保留判断。
- `runbook`：操作指南、复用流程、排障手册。
- `source`：source coverage、source 边界、迁移状态。

预检输出的 `route` 是当前项目入口；`ranked_items` 和 `search` 是候选证据；`candidate_recommendation.required=true` 时，完成或中断都必须生成 Hub candidate，或明确说明“本次无可归档结论”。

## 上下文装配原则

`knowledge-context.sh` 或等价预检应输出“预算内、可解释、可追溯”的上下文，而不是把搜索结果无差别塞给会话。

推荐装配顺序：

1. `goal`：用户当前任务和任务类型。
2. `route`：项目入口、逻辑 URI、工作区映射和 canonical path。
3. `current`：当前事实、有效决策、owner 状态和 review_after。
4. `recent`：最近相关会话、归档摘要、验证记录或排障记录。
5. `related`：按项目、source、topic、component、状态和时效排序的候选材料。
6. `risk`：must-not、旧路径禁用、owner gate、敏感信息和未验证边界。

排序说明必须能回答“为什么选中这些材料”：优先当前项目、当前事实、有效决策、已验证 runbook 和最近相关证据；降低 archive-only、superseded、source-only、未审候选和历史 provenance 的权重。上下文预算不足时，先保留 `route/current/risk`，再压缩 `recent/related`。

预检只提供候选和解释，不代表已归档、已提升或已通过 owner review。需要长期沉淀时，仍按 `governance/ultimate-maintenance-plan.md` 的 L1-L5 层级和 `governance/promotion-policy.md` 执行。

## Canonical 路由表

| 语境 | 旧口径 | 终态回答和新增落点 |
|---|---|---|
| PCR02 工程归档 | `~/embedded/engineering_archive/pcr02/` | `~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/` |
| PCR02 排障记录 | `~/embedded/engineering_archive/pcr02/<topic>/` | `~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/<topic>/` |
| PCR02 当前事实 | 源项目 `docs/`、`knowledge/` | `~/knowledge-hub/projects/pcr02/current/` |
| PCR02 当前决策 | 源项目 `docs/decisions` 或历史归档 | `~/knowledge-hub/projects/pcr02/decisions/` |
| PCR02 验证记录 | 源项目散落日志或旧 validation 归档 | `~/knowledge-hub/projects/pcr02/validation/` |
| Codex archive | `~/codex/docs/archive/` | `~/knowledge-hub/domains/codex/archive/codex-archive/` |
| Codex archive registry | `~/codex/docs/archive/_registry/` | `~/knowledge-hub/domains/codex/archive/codex-archive-registry/` |
| Codex 会话总结和工作流治理 | `~/codex/docs/archive/session-*` | `~/knowledge-hub/domains/codex/` 或 `~/knowledge-hub/domains/codex/archive/codex-archive/` |
| memory / history / raw session | `~/.codex/memories/**`、`~/.codex/history.jsonl`、`~/.codex/sessions/**` | 只读 runtime provenance；长期知识先进入 Hub registry、index 或 archive，不静默写 memory |

## 回答模板

当用户问“归档路径在哪里”且没有指定更窄语境时，默认回答：

```text
新增归档统一写入 Knowledge Hub。

PCR02 工程归档：
~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/

Codex 工作流和会话归档：
~/knowledge-hub/domains/codex/archive/codex-archive/

旧路径如 ~/embedded/engineering_archive 和 ~/codex/docs/archive 只作历史 provenance，不再作为新增入口。
```

当用户处在具体项目仓或工程工作区时，也必须先给 Hub canonical path。可以补一句“旧工程目录历史上曾使用，但终态已归位到 Hub”。

## 多仓协同

全局协同分四层推进：

1. Hub 控制面：本文件、`README.md`、`governance/source-boundaries.md`、`registry/sources.json` 和 `indexes/by-source.md` 是路径口径源。
2. Codex runtime：`~/codex` 的 AGENTS、skill、workflow、docs 和 tests 需要引用本文件或同等终态口径；修改后必须走 `~/codex` build、doctor、plan、apply、routing 和 check 链路。
3. 记忆层：`~/.codex/memories` 和历史 session 只能通过 report-only 审计识别旧路径召回风险；写 memory 或清理 memory 必须走授权账本。
4. 源项目：项目仓 `AGENTS.md` 可保留本地 Codex 运行规则，但不得把旧 `docs/`、`knowledge/`、`tools/` 恢复成知识入口。

## 旧路径审计

使用只读工具扫描当前路径口径漂移：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope hub --json
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope runtime-rules --strict --json
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope all --max-matches 200 --json
```

审计结果只报告，不自动修改文件。分类口径：

- `canonical-policy`：Hub 内明确禁止或重定向旧路径的规则说明，允许存在。
- `provenance`：registry、source inventory、coverage 或历史 manifest 中的来源证据，允许存在。
- `runtime-route-candidate`：Codex runtime、memory summary、raw memories 或 live docs 中可能继续影响回答的旧路径，需要进入后续修复队列。
- `historical-session`：历史 session 记录，默认不可改写，只作为召回风险证据。

`runtime-rules` scope 只检查会实际影响新会话的规则入口，例如全局 Codex AGENTS、`~/codex` source AGENTS、目录级 AGENTS 和重点项目 AGENTS。该 scope 命中旧路径当前入口语义时必须修复；历史 session 和 source provenance 不纳入该 scope 的失败依据。

## 禁止事项

- 不把 `~/embedded/engineering_archive` 回答为当前默认新增归档目录。
- 不把 `~/codex/docs/archive` 回答为当前默认 Codex 归档目录。
- 不为了消除扫描命中而改写历史 session、Git 历史或 provenance。
- 不把 memory 中的旧路径当成高于 Hub 的事实源。
- 不在没有授权账本时修改 `~/.codex/memories`、源项目或 `~/codex` live/apply 结果。
