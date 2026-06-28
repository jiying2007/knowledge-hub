# Source 边界（Source Boundaries）

本文件是 Knowledge Hub source 边界的人读入口，用于快速判断“能不能迁移、能不能引用、能不能提升、需要谁复核”。当前 source 字段权威以 `registry/sources.json` 为准，已关闭来源以 `registry/retired-sources.jsonl` 为 provenance ledger，迁移过程账本封存到 `registry/retired-process-ledger.jsonl`，检索导航以 `indexes/by-source.md` 为准；本文件不重复维护 owner、review_after、check 等完整 registry 字段。

## Registered Sources

当前 source 数量以 `registry/sources.json` current 主表、`registry/retired-sources.jsonl` provenance ledger、`indexes/by-source.md` 和 `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source --json` 为准。source registry 的 `path` 只允许指向 Hub 内 `sources/<source_id>`；旧外部目录仅可通过 `origin_path` 作为 provenance 保留，不再作为 active source、默认查询入口、fallback 或新增归档目的地。下表是最近审计快照，不作为固定数量契约。

| 分组 | source_id | 边界摘要 |
|---|---|---|
| legacy team knowledge | `embedded-knowledge` | 已终态归位到 `domains/embedded/*`；旧团队知识目录 retired，后续提升仍需 owner review |
| legacy project archive | `engineering-archive` | 已终态归位到终态目录 `projects/pcr02/archive/engineering-archive`；历史证据不等于当前 active fact |
| patent materials | `patent-disclosure` | Markdown 正文进入 `domains/patents/archive/patent-disclosure`，附件进入 `artifacts/vault/patent-disclosure`；法律状态和披露边界仍需 owner/legal review |
| Codex archive | `codex-archive` | 已终态归位到 `domains/codex/archive/codex-archive`；旧 Codex archive 目录 retired，不再作为新增归档入口 |
| Codex runtime | `codex-memories` / `codex-history` / `codex-raw-sessions` / `codex-session-index` | 运行态输入 provenance；不复制 raw memory、history 或 session 正文，不写 `~/.codex/memories` |
| Codex archive registry | `codex-archive-registry` | 已终态归位到 `domains/codex/archive/codex-archive-registry` 和 artifact vault；旧 registry 只作 provenance |
| Hub native | `knowledge-hub-automation-runs` | Hub 原生账本；正文权威仍是 `registry/automation-runs.jsonl` |
| PCR02 Level 1 | `pcr02-project-docs` | 旧正文副本已剪枝；项目 current/archive 中的 owner-approved target 继续按 owner 决策使用，Hub 只保留 source control 和必要 provenance |
| PCR02 Level 2 | `pcr02-project-tools` | 工具、诊断和 memory automation 边界；脚本正文不默认提升，自动化默认 report-only |
| PCR02 Level 2 | `pcr02-project-knowledge` | 项目知识候选，secret boundary；不得直接提升团队标准 |
| PCR02 Level 2 | `pcr02-product-test` | 产品测试资料、配置、接口和制品引用；源码和构建产物不进入文本知识层 |
| PCR02 Level 2 | `pcr02-project-scratch` | session/context/resume 类材料；handoff 和 memory candidates 不进入 active facts |
| PCR02 Level 2 | `pcr02-project-root-artifacts` | 根目录散落 artifacts/tools/logs/patch/bin 等，只做 Hub control、artifact vault 或 archive 边界 |
| PCR02 Level 2 | `pcr02-module-agent-rules` | 模块本地 `AGENTS.md` 仍由源项目管理；Hub 仅保留 source control 和必要 provenance |
| PCR02 Level 2 | `pcr02-project-agent-config` | `.vscode` / `.kilo` 等 agent config 和自动化边界；不执行 setup/npm/script |

## PCR02 Source 分层

- Level 1：`pcr02-project-docs`，当前已有 Hub source control、必要 provenance 和 owner-approved target；旧正文副本不再保留，剩余 AI/外部资料复核队列仍按 review queue 处理。
- Level 2：`pcr02-project-tools`、`pcr02-project-knowledge`、`pcr02-product-test`、`pcr02-project-scratch`、`pcr02-project-root-artifacts`、`pcr02-module-agent-rules`、`pcr02-project-agent-config`。这些 source 已进入 Hub 控制面；后续只从 Hub canonical、artifact vault、registry 和 manifest 推进，不默认回源。

PCR02 project-specific 内容默认留在 `projects/pcr02/` 或 source/artifact 引用层；不得提升到 `domains/embedded/standards/`，除非另有 owner review、拆分证据和团队级适用性决策。

## 边界决策（Boundary Decisions）

- team knowledge 不接收项目 lifecycle 目录正文。
- engineering archive 不保存当前项目活文档正文。
- project current 不保存跨项目标准。
- patent domain 不保存通用工程 runbook。
- codex domain 不保存工程事实正文。
- memories 不作为唯一 source。
- source 正文只维护一份；Hub canonical 文本位于 `projects/`、`domains/`、`notes/` 或对应终态归档目录，非文本附件位于 `artifacts/vault/`。
- source check 的默认门禁是 Hub-local registry 静态契约审计；不得把旧外部路径或旧归档工具作为 active check。

## 禁止事项（Must Not）

- 不修改 PCR02 源项目任何文件。
- 不复制脚本、源码、日志、patch、bin、PDF、zip/tgz 或 `.env` 正文到文本知识层。
- 不执行源项目脚本、构建、setup、npm、产品测试或设备测试。
- 不写 `~/.codex/memories`，也不把 memory candidates 当 active facts。
- 不生成 owner decision，不代签，不关闭 owner gate。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不把 owner-ready package、handoff、session archive 或 AI 摘要当成事实闭环。

## 恢复入口

需要恢复完整 source 控制面时，优先运行只读计划：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source --json
```

`knowledge-index-plan` 只读输出 planned view，不写 registry、index、owner decision、memory，也不关闭 owner gate。完成修改后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

## 跨仓路径路由

“归档路径在哪里”这类问题不再由当前工作区或历史 memory 单独决定。统一先读 `governance/path-routing.md`：

- PCR02 工程归档新增落点：`projects/pcr02/archive/engineering-archive/pcr02/`。
- Codex archive 新增落点：`domains/codex/archive/codex-archive/`。
- 旧 `~/embedded/engineering_archive`、`~/codex/docs/archive`、源项目旧 `docs/` / `knowledge/` / `tools/` 只能作为 provenance 或历史证据。
- memory 和历史 session 中的旧路径命中先用 `tools/knowledge-path-audit.sh` 归类，不直接改写。
