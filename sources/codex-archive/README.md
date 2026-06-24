# codex-archive

## 定位

- Source ID: `codex-archive`
- Source path: `~/codex/docs/archive`
- Role: `codex-governance-source`
- Authority: `codex-workflow-history`
- Final disposition: `reference-first-registered`
- Migration strategy: `reference-first-via-codex-archive-tools`
- Owner: `leiwenjun`
- Review after: `2026-09-20`

## Hub 管理方式

Codex archive 继续作为历史归档来源；Hub 作为主库登记索引和摘要。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

历史记录不能直接作为 active governance rule。

## 维护入口

- 清单：`sources/codex-archive/inventory.jsonl`
- 覆盖：`sources/codex-archive/coverage.md`
- 计划：`sources/codex-archive/migration-plan.md`
