# engineering-archive

## 定位

- Source ID: `engineering-archive`
- Hub source path: `sources/engineering-archive`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-copy-docs`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

engineering-archive 已迁移到 Hub PCR02 终态工程归档目录；旧工程归档路径只作 provenance，旧 source-docs 副本不再保留。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

历史 archive corpus 不等于 active project fact。

## 维护入口

- 清单：`sources/engineering-archive/inventory.jsonl`
- 覆盖：`sources/engineering-archive/coverage.md`
- 策略：`sources/engineering-archive/source-policy.md`
