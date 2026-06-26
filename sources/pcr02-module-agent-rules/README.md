# pcr02-module-agent-rules

## 定位

- Source ID: `pcr02-module-agent-rules`
- Hub source path: `sources/pcr02-module-agent-rules`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-agent-rules`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-module-agent-rules 的历史 AGENTS 材料已完成硬迁移证据登记；Hub source-docs 中历史 AGENTS 正文副本已剪枝，当前源码仓及独立子仓 AGENTS.md 作为项目本地 Codex 运行控制文件由源项目 Git 管理，不作为 Hub 知识正文双写。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

模块本地约束未经 owner review 不得提升为全局规则；源项目本地 AGENTS.md 不等于 Hub active rule；Hub 仅保留 hash/provenance。

## 维护入口

- 清单：`sources/pcr02-module-agent-rules/inventory.jsonl`
- 覆盖：`sources/pcr02-module-agent-rules/coverage.md`
- 策略：`sources/pcr02-module-agent-rules/source-policy.md`
