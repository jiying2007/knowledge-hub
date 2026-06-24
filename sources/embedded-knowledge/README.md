# embedded-knowledge

## 定位

- Source ID: `embedded-knowledge`
- Source path: `~/embedded/knowledge`
- Role: `team-knowledge-source`
- Authority: `legacy-team-ssot`
- Final disposition: `owner-gated-pending-decision`
- Migration strategy: `reference-first-owner-review`
- Owner: `team-core`
- Review after: `2026-09-20`

## Hub 管理方式

Embedded knowledge 保持外部 legacy team SSOT，不批量迁移；跨项目标准提升必须先 owner review 和拆分。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

source dirty 或 project-specific 内容可能污染 team standards。

## 维护入口

- 清单：`sources/embedded-knowledge/inventory.jsonl`
- 覆盖：`sources/embedded-knowledge/coverage.md`
- 计划：`sources/embedded-knowledge/migration-plan.md`
