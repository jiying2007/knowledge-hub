# pcr02-project-tools

## 定位

- Source ID: `pcr02-project-tools`
- Hub source path: `sources/pcr02-project-tools`
- Retired origin provenance: `registry/sources.json` origin_path; `registry/source-tombstones.jsonl`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-copy-docs`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-project-tools 的旧可读文档副本已按终态剪枝；Hub 仅保留 source control、hash/provenance 和必要的命令契约/验证记录，工具代码不作为 Hub 正文源。

## 边界

- `path` 指向 Hub 内 source 控制目录；旧外部路径只允许作为 `origin_path` provenance。
- Hub 统一管理 source 的清单、覆盖状态、迁移证据、退役策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

脚本和工具逻辑仍属于源项目代码边界，不由 Hub 自动改写。

## 维护入口

- 清单：`sources/pcr02-project-tools/inventory.jsonl`
- 覆盖：`sources/pcr02-project-tools/coverage.md`
- 计划：`sources/pcr02-project-tools/migration-plan.md`
