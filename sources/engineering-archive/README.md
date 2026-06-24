# engineering-archive

## 定位

- Source ID: `engineering-archive`
- Source path: `~/embedded/engineering_archive`
- Role: `project-archive-source`
- Authority: `legacy-project-history`
- Final disposition: `copy-first-migrated`
- Migration strategy: `copy-first-archive`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

Engineering archive 已通过 copy-first 迁入 PCR02 archive。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

历史 archive corpus 不等于 active fact。

## 维护入口

- 清单：`sources/engineering-archive/inventory.jsonl`
- 覆盖：`sources/engineering-archive/coverage.md`
- 计划：`sources/engineering-archive/migration-plan.md`
