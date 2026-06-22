# Source 边界（Source Boundaries）

本文件是 Knowledge Hub source 边界的人读入口，用于快速判断“能不能迁移、能不能引用、能不能提升、需要谁复核”。字段权威以 `registry/sources.json` 为准，检索导航以 `indexes/by-source.md` 为准；本文件不重复维护 owner、review_after、check 等完整 registry 字段。

## 当前已登记 Sources（Registered Sources）

截至 2026-06-21，Knowledge Hub 控制面登记 13 个 source。登记 source 只代表治理覆盖、检索入口和后续分类路径已经建立，不代表正文已迁移、owner 已签收或内容已成为 active fact。

| 分组 | source_id | 边界摘要 |
|---|---|---|
| legacy team knowledge | `embedded-knowledge` | 旧团队知识源，reference-first + owner review；不得混入未拆分的 project-specific 内容 |
| legacy project archive | `engineering-archive` | 历史工程归档，copy-first archive；历史证据不等于当前 active fact |
| patent materials | `patent-disclosure` | 专利材料，专利域独立治理；法律状态和披露边界需 owner/legal review |
| Codex archive | `codex-archive` | Codex 工作流历史，reference-first；历史记录不能直接提升为当前规则 |
| Codex memories | `codex-memories` | 辅助召回源；不得作为事实或规则唯一来源，不得由 Knowledge Hub 自动写入 |
| PCR02 Level 1 | `pcr02-project-docs` | 项目 docs 已做 copy/reference/artifact/owner-gated 覆盖；7 个 owner gate 仍未语义关闭 |
| PCR02 Level 2 | `pcr02-project-tools` | 工具、诊断和 memory automation 边界；脚本正文不默认复制，自动化默认 report-only |
| PCR02 Level 2 | `pcr02-project-knowledge` | 项目知识候选，classify-first + secret boundary；不得直接提升团队标准 |
| PCR02 Level 2 | `pcr02-product-test` | 产品测试资料、配置、接口和制品引用；源码和构建产物不进入文本知识层 |
| PCR02 Level 2 | `pcr02-project-scratch` | session/context/resume 类材料，archive-only；handoff 和 memory candidates 不进入 active facts |
| PCR02 Level 2 | `pcr02-project-root-artifacts` | 根目录散落 artifacts/tools/logs/patch/bin 等，只做 artifact/tool/archive/classify-first 边界 |
| PCR02 Level 2 | `pcr02-module-agent-rules` | 模块本地 `AGENTS.md` 规则引用，owner-gated；未签收前不提升为 Knowledge Hub 根规则 |
| PCR02 Level 2 | `pcr02-project-agent-config` | `.vscode` / `.kilo` 等 agent config 和自动化边界；不执行 setup/npm/script |

## PCR02 Source 分层

- Level 1：`pcr02-project-docs`，当前已有 32/32 docs 治理覆盖；其中 7 个 review-required 项仍保持 owner gate open。
- Level 2：`pcr02-project-tools`、`pcr02-project-knowledge`、`pcr02-product-test`、`pcr02-project-scratch`、`pcr02-project-root-artifacts`、`pcr02-module-agent-rules`、`pcr02-project-agent-config`。这些 source 进入控制面后，默认只做分类、引用、artifact-ref、identity、archive-only 或 report-only evidence，不复制源码/脚本/日志/二进制正文。

PCR02 project-specific 内容默认留在 `domains/projects/pcr02/` 或 source/artifact 引用层；不得提升到 `domains/embedded/standards/`，除非另有 owner review、拆分证据和团队级适用性决策。

## 边界决策（Boundary Decisions）

- team knowledge 不接收项目 lifecycle 目录正文。
- engineering archive 不保存当前项目活文档正文。
- project current 不保存跨项目标准。
- patent domain 不保存通用工程 runbook。
- codex domain 不保存工程事实正文。
- memories 不作为唯一 source。
- source 正文只维护一份；Knowledge Hub 使用迁移副本、ref、artifact-ref、registry 和 manifest 管理。
- source check 的默认门禁是 registry 静态契约审计；外部 source check 只允许显式 report-only 快照，不自动执行、不自动修复。

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
