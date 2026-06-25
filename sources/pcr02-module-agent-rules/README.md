# pcr02-module-agent-rules

## 定位

- Source ID: `pcr02-module-agent-rules`
- Hub source path: `sources/pcr02-module-agent-rules`
- Retired origin path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-agent-rules`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-module-agent-rules 的历史 AGENTS 材料已完成硬迁移证据登记；历史 `AGENTS.md` 正文副本已从 Hub 旧迁移正文层剪枝，剪枝账本见 `artifacts/manifests/pcr02-agent-rules-body-prune-20260625.jsonl`。当前源码仓及独立子仓的 `AGENTS.md` 属于项目本地 Codex 运行控制文件，仍由源项目 Git 管理，不作为 Hub 知识正文双写。

## 边界

- `path` 指向 Hub 内 source 控制目录；旧外部路径只允许作为 `origin_path` provenance。
- Hub 统一管理 source 的清单、覆盖状态、迁移证据、退役策略和可复用提取物。
- 源项目当前 `AGENTS.md` 仅保留本地运行边界、构建边界和危险操作限制；不承载迁移归档正文。
- Hub 不保留历史 `AGENTS.md` 正文副本作为规则入口；只保留 hash/provenance 和剪枝账本。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

模块本地约束未经 owner review 不得提升为全局规则。

## 维护入口

- 清单：`sources/pcr02-module-agent-rules/inventory.jsonl`
- 覆盖：`sources/pcr02-module-agent-rules/coverage.md`
- 计划：`sources/pcr02-module-agent-rules/migration-plan.md`
