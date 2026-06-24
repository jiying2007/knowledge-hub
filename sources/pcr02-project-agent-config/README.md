# pcr02-project-agent-config

## 定位

- Source ID: `pcr02-project-agent-config`
- Hub source path: `sources/pcr02-project-agent-config`
- Retired origin path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-agent-config`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-project-agent-config 作为配置/自动化边界已在 Hub 控制面退役外部 source path；旧配置路径不再作为知识源。

## 边界

- `path` 指向 Hub 内 source 控制目录；旧外部路径只允许作为 `origin_path` provenance。
- Hub 统一管理 source 的清单、覆盖状态、迁移证据、退役策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

配置可能含外部依赖或敏感信息；启用自动化前需授权和审计。

## 维护入口

- 清单：`sources/pcr02-project-agent-config/inventory.jsonl`
- 覆盖：`sources/pcr02-project-agent-config/coverage.md`
- 计划：`sources/pcr02-project-agent-config/migration-plan.md`
